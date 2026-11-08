#!/usr/bin/env python3
"""Checks that content/en/<name>.json matches content/<name>.json key for key.

Usage: python3 scripts/check_en.py [content/<name>.json ...]   (no arguments = every lesson)
Prints OK per file, or the first mismatch; exits 1 if anything is wrong or missing.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def same(a, b, path="$"):
    if type(a) != type(b):
        raise AssertionError(f"{path}: type")
    if isinstance(a, dict):
        if a.keys() != b.keys():
            raise AssertionError(f"{path}: keys differ {sorted(set(a) ^ set(b))}")
        for k in a:
            same(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list):
        if len(a) != len(b):
            raise AssertionError(f"{path}: length {len(a)} vs {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            same(x, y, f"{path}[{i}]")


def check(tr_path):
    en_path = tr_path.parent / "en" / tr_path.name
    if not en_path.exists():
        raise AssertionError("English file missing")
    tr = json.loads(tr_path.read_text(encoding="utf-8"))
    en = json.loads(en_path.read_text(encoding="utf-8"))
    same(tr, en)
    for k in ("hafta", "gun", "tarih", "tur", "pdf"):
        if tr.get(k) != en.get(k):
            raise AssertionError(f"{k} changed")
    for a, b in zip(tr.get("quiz") or [], en.get("quiz") or []):
        if a["dogru"] != b["dogru"]:
            raise AssertionError("quiz dogru changed")
    for a, b in zip(tr.get("terimler") or [], en.get("terimler") or []):
        if a["tr"] != b["tr"]:
            raise AssertionError("terimler tr changed")


def main():
    paths = [pathlib.Path(p).resolve() for p in sys.argv[1:]] or sorted((ROOT / "content").glob("*.json"))
    bad = 0
    for p in paths:
        try:
            check(p)
            print(f"OK  {p.name}")
        except (AssertionError, json.JSONDecodeError, KeyError) as e:
            bad += 1
            print(f"ERR {p.name}: {e}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
