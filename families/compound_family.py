#!/usr/bin/env python3

"""Compile compound familes and save to database."""

from typing import Dict, List, Tuple, TypedDict
from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord, FamilyCompound
from tools.meaning_construction import clean_construction
from tools.meaning_construction import degree_of_completion
from tools.meaning_construction import make_meaning
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.superscripter import superscripter_uni
from tools.tic_toc import tic, toc
from tools.tsv_read_write import write_tsv_list
from tools.date_and_time import day

class CompoundItem(TypedDict):
    headwords: List[str]
    anki_data: List[Tuple[str, str, str, str]]

CompoundDict = Dict[str, CompoundItem]

def main():
    tic()
    print("[bright_yellow]compound families generator")

    pth = ProjectPaths()

    cf_dict = add_all_cf_to_db(pth)

    anki_exporter(pth, cf_dict)
    toc()

def check_cf(cf: str, pali_1: str) -> None:
    if cf == " ":
        raise Exception(f"[bright_red]ERROR: spaces found in .family_compound, please remove! pali_1 = {pali_1}")
    elif not cf:
        raise Exception(f"[bright_red]ERROR: '' found in .family_compound, please remove! pali_1 = {pali_1}")
    elif cf == "+":
        raise Exception(f"[bright_red]ERROR: + found in .family_compound please remove! pali_1 = {pali_1}")

def create_comp_fam_dict(dpd_db: List[PaliWord]) -> CompoundDict:
    """Create a dict of all compound families.
    """
    print("[green]extracting compound families and headwords", end=" ")

    cf_dict: CompoundDict = dict()

    for i in dpd_db:

        for cf in i.family_compounds_keys_from_ssv:
            check_cf(cf, i.pali_1)

            if i.is_family_compound:

                if cf not in cf_dict.keys():
                    cf_dict[cf] = CompoundItem(headwords=[], anki_data=[])

                cf_dict[cf]["headwords"].append(i.pali_1)

    print(len(cf_dict))

    return cf_dict

def pali_word_table_row(i: PaliWord) -> str:
    html_string = ""

    meaning = make_meaning(i)
    html_string += "\n<tr>"
    html_string += f"<th>{superscripter_uni(i.pali_1)}</th>"
    html_string += f"<td><b>{i.pos}</b></td>"
    html_string += f"<td>{meaning} {degree_of_completion(i)}</td>"
    html_string += "</tr>"

    return html_string

def render_family_compounds_table_html(fc: FamilyCompound) -> str:
    """Get all PaliWords of the FamilyCompound, and render each as a row in a html table.
    """

    html_string = "\n<table class='family'>\n"

    # Example with aṭṭhakusalakammapaccayā:
    # Under 'compounds with kamma', don't include 'kamma 1', 'kamma 2', etc.
    # under 'compounds with paccayā', don't include 'paccayā'.
    family_comp_words = [i for i in fc.pali_words if i.is_family_compound]

    for i in sorted(family_comp_words, key=lambda x: pali_sort_key(x.pali_1)):
        html_string += pali_word_table_row(i)

    html_string += "\n\n</table>\n"

    return html_string

def add_all_cf_to_db(pth: ProjectPaths) -> CompoundDict:
    print("[green]adding to db", end=" ")

    db_session = get_db_session(pth.dpd_db_path)

    db_session.execute(FamilyCompound.__table__.delete()) # type: ignore

    dpd_db: List[PaliWord] = db_session.query(PaliWord).all()
    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.pali_1))

    cf_dict = create_comp_fam_dict(dpd_db)

    # (1) Create all the FamilyCompounds as defined in cf_dict, without html tables.
    #
    # Commit to db so FamilyCompounds get db id.
    #
    # (2) Associate them to the PaliWords.
    #
    # For PaliWords with empty .family_compound,
    # if the PaliWord passes pali_word_is_family_compound(),
    # associate a PaliCompound where the PaliWord.pali_clean == FamilyCompound.compound_family.
    #
    # Commit to db.
    #
    # (3) Render their html tables, which require getting the associated PaliWords.
    #
    # Commit to db.

    for cf_key, cf_item in cf_dict.items():
        # The table was deleted and we are re-generating the items, so no need
        # to check for an existing FamilyCompound.
        fc = FamilyCompound(
            compound_family = cf_key,
            html = "",
            count = len(cf_item["headwords"]),
        )
        db_session.add(fc)

    db_session.commit()

    for i in dpd_db:
        if (i.family_compound is None or i.family_compound == ""):
            # A PaliWord may not be a compound (empty .family_compound field,
            # e.g. 'gata 1'), but the word itself is representative of a
            # FamilyCompound ('gata 1' → 'gata').
            #
            # .pali_clean is .pali_1 without numbers, this should be used to
            # associate the word, thus (gata 1, gata 2, etc. → gata).

            comps = db_session.query(FamilyCompound) \
                            .filter(FamilyCompound.compound_family == i.pali_clean) \
                            .all()

            for cf in comps:
                if i not in cf.pali_words:
                    cf.pali_words.append(i)

        else:
            # Associate PaliWord to the FamilyCompounds listed in PaliWord.compound_family
            for cf_key in i.family_compounds_keys_from_ssv:
                if cf_key in cf_dict:
                    if i.pali_1 in cf_dict[cf_key]["headwords"]:

                        cf = db_session.query(FamilyCompound) \
                                       .filter(FamilyCompound.compound_family == cf_key) \
                                       .first()
                        assert(cf is not None)

                        if i not in cf.pali_words:
                            cf.pali_words.append(i)

    db_session.commit()

    for fc in db_session.query(FamilyCompound).all():
        fc.html = render_family_compounds_table_html(fc)

    db_session.commit()
    db_session.close()
    print("[white]ok")

    return cf_dict

def add_anki_data_family_html(i: PaliWord, cf_item: CompoundItem) -> None:
    meaning = make_meaning(i)
    if i.meaning_1:
        construction = clean_construction(
            i.construction) if i.meaning_1 else ""

        cf_item["anki_data"] += [
            (i.pali_1, i.pos, meaning, construction)]

def anki_exporter(pth: ProjectPaths, cf_dict: CompoundDict) -> None:
    """Save to TSV for anki."""
    anki_data_list = []
    for family in cf_dict:
        anki_family = f"<b>{family}</b>"
        html = "<table><tbody>"
        for row in cf_dict[family]["anki_data"]:
            headword, pos, meaning, construction = row
            html += "<tr valign='top'>"
            html += "<div style='color: #FFB380'>"
            html += f"<td>{headword}</td>"
            html += f"<td><div style='color: #FF6600'>{pos}</div></td>"
            html += f"<td><div style='color: #FFB380'>{meaning}</td>"
            html += f"<td><div style='color: #FF6600'>{construction}</div></td></tr>"
        html += "</tbody></table>"
        if len(html) > 131072:
            print(f"[red]{family} longer than 131072 characters")
        else:
            anki_data_list += [(anki_family, html, day())]

    file_path = pth.family_compound_tsv_path
    header = []
    write_tsv_list(str(file_path), header, anki_data_list)


if __name__ == "__main__":
    main()
