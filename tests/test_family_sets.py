#!/usr/bin/env python3

from pathlib import Path
from typing import Dict, List

from db.models import FamilySet, PaliWord
from exporter.export_dpd import PaliWordTemplates, render_family_set_templ
from tools.configger import config_read
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from db.get_db_session import get_db_session

PTH = ProjectPaths()
TMPL = PaliWordTemplates(PTH)

SET_TABLES_DIR = Path("./tests/data/set_tables/")
SET_TO_WORDS_DIR = Path("./tests/data/set_to_words/")

# PaliWords and their expected FamilySets as many-to-many relations.
WORDS_REL_SETS = {
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

def test_pali_word_to_family_sets_relation():
    db_session = get_db_session(PTH.dpd_db_path)

    for pali_1, expected_sets in WORDS_REL_SETS.items():
        w = db_session.query(PaliWord).filter(PaliWord.pali_1 == pali_1).first()
        if w is None:
            raise Exception(f"Cannot find word: {pali_1}")

        set_list = [i.set for i in w.family_sets_sorted]

        assert ";".join(set_list) == ";".join(expected_sets)

    db_session.close()

def get_sets_to_words() -> Dict[str, List[str]]:
    db_session = get_db_session(PTH.dpd_db_path)

    sets_to_words: Dict[str, List[str]] = dict()

    for i in WORDS_REL_SETS.values():
        if len(i) != 0:
            for set_key in i:
                if set_key not in sets_to_words.keys():
                    sets_to_words[set_key] = []

    for set_key in sets_to_words:
        fs = db_session.query(FamilySet) \
                       .filter(FamilySet.set == set_key) \
                       .first()
        if fs is None:
            raise Exception(f"Can't find FamilySet: {set_key}")

        sets_to_words[set_key] = [i.pali_1 for i in sorted(fs.pali_words, key=lambda x: pali_sort_key(x.pali_1))]

    return sets_to_words

def test_family_set_to_pali_words_relation():
    sets_to_words = get_sets_to_words()

    for set_key, db_words in sets_to_words.items():
        with open(SET_TO_WORDS_DIR.joinpath(f"{set_key}_to_words.txt"), "r", encoding='utf-8') as f:
            expected_words = f.read()

        assert "\n".join(db_words) == expected_words

def test_family_set_table_html_render():
    db_session = get_db_session(PTH.dpd_db_path)

    for pali_1, sets in WORDS_REL_SETS.items():
        if len(sets) == 0:
            continue

        with open(SET_TABLES_DIR.joinpath(f"{pali_1}.html"), "r", encoding='utf-8') as f:
            expected_html = f.read()

        w = db_session.query(PaliWord).filter(PaliWord.pali_1 == pali_1).first()
        if w is None:
            raise Exception(f"Cannot find word: {pali_1}")

        html = render_family_set_templ(PTH, w, w.family_sets_sorted, TMPL.family_set_templ)

        assert html == expected_html

    db_session.close()

def write_sets_to_words_lists():
    for set_key, words in get_sets_to_words().items():
        with open(SET_TO_WORDS_DIR.joinpath(f"{set_key}_to_words.txt"), "w", encoding='utf-8') as f:
            f.write("\n".join(words))

def write_family_sets_tables():
    db_session = get_db_session(PTH.dpd_db_path)

    for pali_1, sets in WORDS_REL_SETS.items():
        if len(sets) == 0:
            continue

        w = db_session.query(PaliWord).filter(PaliWord.pali_1 == pali_1).first()
        if w is None:
            raise Exception(f"Cannot find word: {pali_1}")

        with open(SET_TABLES_DIR.joinpath(f"{pali_1}.html"), "w", encoding='utf-8') as f:
            html = render_family_set_templ(PTH, w, w.family_sets_sorted, TMPL.family_set_templ)
            f.write(html)

    db_session.close()

if __name__ == "__main__":
    # today = 2023-11-20
    s = config_read("info", "today")
    if s is None or s != "2023-11-20":
        raise Exception("""For consistent test outputs, set info.today = 2023-11-20 in config.ini
[info]
today = 2023-11-20
""")

    for i in [SET_TABLES_DIR, SET_TO_WORDS_DIR]:
        if not i.exists():
            i.mkdir(parents=True)

    write_sets_to_words_lists()
    write_family_sets_tables()
