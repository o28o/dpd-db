#!/usr/bin/env python3

from pathlib import Path
from typing import Dict, List

from db.models import FamilyCompound, PaliWord
from exporter.export_dpd import PaliWordTemplates, render_family_compound_templ
from exporter.helpers import cf_set_gen
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from db.get_db_session import get_db_session

PTH = ProjectPaths()
TMPL = PaliWordTemplates(PTH)

COMP_TABLES_DIR = Path("./tests/data/comp_tables/")
COMP_TO_WORDS_DIR = Path("./tests/data/comp_to_words/")

# PaliWords and their expected FamilyCompounds as many-to-many relations.
WORDS_REL_COMPS = {
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

def test_pali_word_to_family_compounds_relation():
    db_session = get_db_session(PTH.dpd_db_path)

    for pali_1, expected_comps in WORDS_REL_COMPS.items():
        w = db_session.query(PaliWord).filter(PaliWord.pali_1 == pali_1).first()
        if w is None:
            raise Exception(f"Cannot find word: {pali_1}")

        comp_list = [i.compound_family for i in w.family_compounds_sorted]

        assert ";".join(comp_list) == ";".join(expected_comps)

    db_session.close()

def get_comps_to_words() -> Dict[str, List[str]]:
    db_session = get_db_session(PTH.dpd_db_path)

    comps_to_words: Dict[str, List[str]] = dict()

    for i in WORDS_REL_COMPS.values():
        if len(i) != 0:
            for comp in i:
                if comp not in comps_to_words.keys():
                    comps_to_words[comp] = []

    for comp_key in comps_to_words:
        comp = db_session.query(FamilyCompound) \
                         .filter(FamilyCompound.compound_family == comp_key) \
                         .first()
        if comp is None:
            raise Exception(f"Can't find FamilyCompound: {comp_key}")

        comps_to_words[comp_key] = [i.pali_1 for i in sorted(comp.pali_words, key=lambda x: pali_sort_key(x.pali_1))]

    return comps_to_words

def test_family_compound_to_pali_words_relation():
    comps_to_words = get_comps_to_words()

    for comp_key, db_words in comps_to_words.items():
        with open(COMP_TO_WORDS_DIR.joinpath(f"{comp_key}_to_words.txt"), "r", encoding='utf-8') as f:
            expected_words = f.read()

        assert "\n".join(db_words) == expected_words

def test_family_compound_table_html_render():
    db_session = get_db_session(PTH.dpd_db_path)

    for pali_1, comps in WORDS_REL_COMPS.items():
        if len(comps) == 0:
            continue

        with open(COMP_TABLES_DIR.joinpath(f"{pali_1}.html"), "r", encoding='utf-8') as f:
            expected_html = f.read()

        w = db_session.query(PaliWord).filter(PaliWord.pali_1 == pali_1).first()
        if w is None:
            raise Exception(f"Cannot find word: {pali_1}")

        cf_set = cf_set_gen(PTH)

        html = render_family_compound_templ(PTH, w, w.family_compounds_sorted, cf_set, TMPL.family_compound_templ)

        assert html == expected_html

    db_session.close()

def write_compound_to_words_lists():
    for comp_key, words in get_comps_to_words().items():
        with open(COMP_TO_WORDS_DIR.joinpath(f"{comp_key}_to_words.txt"), "w", encoding='utf-8') as f:
            f.write("\n".join(words))

def write_family_compounds_tables():
    db_session = get_db_session(PTH.dpd_db_path)

    for pali_1, comps in WORDS_REL_COMPS.items():
        if len(comps) == 0:
            continue

        w = db_session.query(PaliWord).filter(PaliWord.pali_1 == pali_1).first()
        if w is None:
            raise Exception(f"Cannot find word: {pali_1}")

        cf_set = cf_set_gen(PTH)

        with open(COMP_TABLES_DIR.joinpath(f"{pali_1}.html"), "w", encoding='utf-8') as f:
            html = render_family_compound_templ(PTH, w, w.family_compounds_sorted, cf_set, TMPL.family_compound_templ)
            f.write(html)

    db_session.close()

if __name__ == "__main__":
    for i in [COMP_TABLES_DIR, COMP_TO_WORDS_DIR]:
        if not i.exists():
            i.mkdir(parents=True)

    write_compound_to_words_lists()
    write_family_compounds_tables()
