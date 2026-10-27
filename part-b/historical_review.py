"""Read the first fresh review using its complete, preserved implementation."""
from functools import lru_cache
import importlib.util

from corpus import ROOT, load_corpus


@lru_cache(maxsize=1)
def archived_fresh_module():
    root = ROOT / "evidence/versions/temperature-v3-pre-routing-v4"
    spec = importlib.util.spec_from_file_location("relay_preserved_fresh1", root / "fresh_evaluate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Imports in the live app already resolve the current corpus module. Bind
    # this isolated archived reader to its own immutable inputs explicitly.
    module.ROOT = root
    paths = {"REGISTRATION": "evidence/fresh-20261022-registration.json",
             "SOURCE": "evidence/fresh-20261022-source.json",
             "DRIVER": "evidence/fresh-20261022-driver.json",
             "REPORTS": "data/fresh_reports_20261022.jsonl",
             "LABELS": "data/fresh_labels_20261022.jsonl",
             "FREEZE": "data/fresh_labels_20261022.freeze.json",
             "REVIEW_DIR": "evidence/reviews/fresh-20261022"}
    for name, relative in paths.items():
        setattr(module, name, root / relative)
    module.load_corpus = lambda: load_corpus(root)
    return module


def fresh1_rows():
    return archived_fresh_module().fresh_rows()
