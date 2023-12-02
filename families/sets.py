#!/usr/bin/env python3

"""Compile sets save to database."""

from typing import Dict, List, TypedDict
from rich import print
from sqlalchemy.sql import and_

from db.get_db_session import get_db_session
from db.models import PaliWord, FamilySet
from tools.tic_toc import tic, toc
from tools.superscripter import superscripter_uni
from tools.meaning_construction import make_meaning
from tools.pali_sort_key import pali_sort_key
from tools.meaning_construction import degree_of_completion as doc
from tools.paths import ProjectPaths

class SetItem(TypedDict):
    headwords: List[str]

SetsDict = Dict[str, SetItem]

def main():
    tic()
    print("[bright_yellow]sets generator")

    errors_list = add_all_sf_to_db()
    print_errors_list(errors_list)

    toc()

def check_fs(fs: str, pali_1: str) -> None:
    if fs == " ":
        raise Exception(f"[bright_red]ERROR: spaces found please remove! pali_1 = {pali_1}")
    elif not fs:
        raise Exception(f"[bright_red]ERROR: '' found please remove! pali_1 = {pali_1}")
    elif fs == "+":
        raise Exception(f"[bright_red]ERROR: + found please remove! pali_1 = {pali_1}")

def make_sets_dict(dpd_db: List[PaliWord]) -> SetsDict:
    """Create a dict of all sets.
    """
    print("[green]extracting set names", end=" ")

    sets_dict: SetsDict = dict()

    for i in dpd_db:

        for fs in i.family_sets_keys_from_ssv:
            check_fs(fs, i.pali_1)

            if i.meaning_1 is not None and i.meaning_1 != "":

                if fs not in sets_dict.keys():
                    sets_dict[fs] = SetItem(headwords=[])

                sets_dict[fs]["headwords"].append(i.pali_1)

    print(len(sets_dict))
    return sets_dict

def pali_word_table_row(i: PaliWord) -> str:
    html_string = ""

    meaning = make_meaning(i)
    html_string += "\n<tr>"
    html_string += f"<th>{superscripter_uni(i.pali_1)}</th>"
    html_string += f"<td><b>{i.pos}</b></td>"
    html_string += f"<td>{meaning} {doc(i)}</td>"
    html_string += "</tr>"

    return html_string

def render_family_set_table_html(fs: FamilySet) -> str:
    html_string = "\n<table class='family'>\n"

    for i in sorted(fs.pali_words, key=lambda x: pali_sort_key(x.pali_1)):
        html_string += pali_word_table_row(i)

    html_string += "\n\n</table>\n"

    return html_string

def add_all_sf_to_db() -> List[str]:
    print("[green]adding to db", end=" ")
    pth = ProjectPaths()

    db_session = get_db_session(pth.dpd_db_path)

    db_session.execute(FamilySet.__table__.delete()) # type: ignore

    dpd_db = db_session.query(PaliWord) \
        .filter(and_(PaliWord.family_set.is_not(None),
                     PaliWord.family_set != "")) \
        .all()
    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.pali_1))

    sets_dict = make_sets_dict(dpd_db)

    # (1) Create all the FamilySets as defined in sets_dict, without html tables.
    #
    # Commit to db so FamilySets get db id.
    #
    # (2) Associate them to the PaliWords.
    #
    # Commit to db.
    #
    # (3) Render their html tables, which require getting the associated PaliWords.
    #
    # Commit to db.

    errors_list: List[str] = []

    for sf_key, sf_item in sets_dict.items():
        count = len(sf_item["headwords"])

        fs = FamilySet(
            set = sf_key,
            html = "",
            count = len(sf_item["headwords"]),
        )
        db_session.add(fs)

        if count < 3:
            errors_list.append(sf_key)

    db_session.commit()

    for i in dpd_db:
        for sf_key in i.family_sets_keys_from_ssv:
            if sf_key in sets_dict:
                if i.pali_1 in sets_dict[sf_key]["headwords"]:

                    sf = db_session.query(FamilySet) \
                                    .filter(FamilySet.set == sf_key) \
                                    .first()
                    assert(sf is not None)

                    if i not in sf.pali_words:
                        sf.pali_words.append(i)

    db_session.commit()

    for fs in db_session.query(FamilySet).all():
        fs.html = render_family_set_table_html(fs)

    db_session.commit()
    db_session.close()
    print("[white]ok")

    return errors_list


def print_errors_list(errors_list: List[str]):
    if errors_list != []:
        print("[bright_red]ERROR: less than 3 names in set: ")
        for error in errors_list:
            print(f"[red]{error}")


if __name__ == "__main__":
    main()
