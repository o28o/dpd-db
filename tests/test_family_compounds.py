#!/usr/bin/env python3

from pathlib import Path

from db.models import PaliWord
from exporter.export_dpd import PaliWordTemplates, get_family_compounds_for_pali_word, render_family_compound_templ
from exporter.helpers import cf_set_gen
from tools.paths import ProjectPaths
from db.get_db_session import get_db_session

PTH = ProjectPaths()
TMPL = PaliWordTemplates(PTH)

HTML_DATA_DIR = Path("./tests/data/comp_tables/")

if not HTML_DATA_DIR.exists():
    HTML_DATA_DIR.mkdir()

# PaliWords and their expected FamilyCompounds.
# This is a many-to-many relation.
WORDS = {
    "aṭṭhakusalakammapaccayā": ["aṭṭha1", "kusala", "kamma", "paccayā"],
    "adhammakammasañña": ["dhamma1", "kamma", "saññā"],
    "apaṇṇakapaṭipadā": ["apaṇṇaka", "paṭipadā"],
    "gihisāmīcipaṭipadā": ["gihī", "sāmīci", "paṭipadā"],
    "sallekhasutta": [],
    "aṅgulipatodakasikkhāpada": [],
    "issatta": [],
    "ukkūlavikkūla": [],
    "dvipadagga": ["dvi", "pada", "agga1"],
    "sokaparidevamacchara": ["soka", "parideva", "macchara"],
    "aññāsikoṇḍañña": ["aññāsi"],
    "assayuja 1": ["assa1", "yuja"],
    "bodhirukkha": ["bodhi", "rukkha"],
}


def test_family_compounds_in_db():
    db_session = get_db_session(PTH.dpd_db_path)

    for pali_1, expected_comps in WORDS.items():
        w = db_session.query(PaliWord).filter(PaliWord.pali_1 == pali_1).first()
        if w is None:
            raise Exception(f"Cannot find word: {pali_1}")

        comp_list = [i.compound_family for i in get_family_compounds_for_pali_word(w)]

        assert ";".join(comp_list) == ";".join(expected_comps)

    db_session.close()

def test_family_compound_table_html_render():
    db_session = get_db_session(PTH.dpd_db_path)

    for pali_1, comps in WORDS.items():
        if len(comps) == 0:
            continue

        with open(HTML_DATA_DIR.joinpath(f"{pali_1}.html"), "r", encoding='utf-8') as f:
            expected_html = f.read()

        w = db_session.query(PaliWord).filter(PaliWord.pali_1 == pali_1).first()
        if w is None:
            raise Exception(f"Cannot find word: {pali_1}")

        fc = get_family_compounds_for_pali_word(w)
        cf_set = cf_set_gen(PTH)

        html = render_family_compound_templ(PTH, w, fc, cf_set, TMPL.family_compound_templ)

        assert html == expected_html

    db_session.close()

def write_family_compounds_tables():
    db_session = get_db_session(PTH.dpd_db_path)

    for pali_1, comps in WORDS.items():
        if len(comps) == 0:
            continue

        w = db_session.query(PaliWord).filter(PaliWord.pali_1 == pali_1).first()
        if w is None:
            raise Exception(f"Cannot find word: {pali_1}")

        fc = get_family_compounds_for_pali_word(w)
        cf_set = cf_set_gen(PTH)

        with open(HTML_DATA_DIR.joinpath(f"{pali_1}.html"), "w", encoding='utf-8') as f:
            html = render_family_compound_templ(PTH, w, fc, cf_set, TMPL.family_compound_templ)
            f.write(html)

    db_session.close()

if __name__ == "__main__":
    write_family_compounds_tables()
