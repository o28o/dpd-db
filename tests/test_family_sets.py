#!/usr/bin/env python3

from pathlib import Path

from db.models import PaliWord
from exporter.export_dpd import PaliWordTemplates, get_family_sets_for_pali_word, render_family_set_templ
from tools.paths import ProjectPaths
from db.get_db_session import get_db_session

PTH = ProjectPaths()
TMPL = PaliWordTemplates(PTH)

HTML_DATA_DIR = Path("./tests/data/set_tables/")

if not HTML_DATA_DIR.exists():
    HTML_DATA_DIR.mkdir()

# PaliWords and their expected FamilySets.
# This is a many-to-many relation.
WORDS = {
    "aṭṭhakusalakammapaccayā": [],
    "adhammakammasañña": [],
    "apaṇṇakapaṭipadā": [],
    "gihisāmīcipaṭipadā": [],
    "sallekhasutta": ["suttas of the Majjhima Nikāya"],
    "aṅgulipatodakasikkhāpada": ["bhikkhupātimokkha rules"],
    "issatta": [],
    "ukkūlavikkūla": [],
    "dvipadagga": [],
    "sokaparidevamacchara": [],
    "aññāsikoṇḍañña": ["names of monks", "names of arahants"],
    "assayuja 1": ["months of the lunar year", "astronomical terms"],
    "bodhirukkha": ["plants", "trees"],
}


def test_family_sets_in_db():
    db_session = get_db_session(PTH.dpd_db_path)

    for pali_1, expected_sets in WORDS.items():
        w = db_session.query(PaliWord).filter(PaliWord.pali_1 == pali_1).first()
        if w is None:
            raise Exception(f"Cannot find word: {pali_1}")

        set_list = [i.set for i in get_family_sets_for_pali_word(w)]

        assert ";".join(set_list) == ";".join(expected_sets)

    db_session.close()

def test_family_set_table_html_render():
    db_session = get_db_session(PTH.dpd_db_path)

    for pali_1, sets in WORDS.items():
        if len(sets) == 0:
            continue

        with open(HTML_DATA_DIR.joinpath(f"{pali_1}.html"), "r", encoding='utf-8') as f:
            expected_html = f.read()

        w = db_session.query(PaliWord).filter(PaliWord.pali_1 == pali_1).first()
        if w is None:
            raise Exception(f"Cannot find word: {pali_1}")

        fs = get_family_sets_for_pali_word(w)

        html = render_family_set_templ(PTH, w, fs, TMPL.family_set_templ)

        assert html == expected_html

    db_session.close()

def write_family_sets_tables():
    db_session = get_db_session(PTH.dpd_db_path)

    for pali_1, sets in WORDS.items():
        if len(sets) == 0:
            continue

        w = db_session.query(PaliWord).filter(PaliWord.pali_1 == pali_1).first()
        if w is None:
            raise Exception(f"Cannot find word: {pali_1}")

        fs = get_family_sets_for_pali_word(w)

        with open(HTML_DATA_DIR.joinpath(f"{pali_1}.html"), "w", encoding='utf-8') as f:
            html = render_family_set_templ(PTH, w, fs, TMPL.family_set_templ)
            f.write(html)

    db_session.close()

if __name__ == "__main__":
    write_family_sets_tables()
