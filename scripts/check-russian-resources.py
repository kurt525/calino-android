#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

PLACEHOLDER = re.compile(r"%(?:\d+\$)?[-#+ 0,(]*\d*(?:\.\d+)?[a-zA-Z%]|\^\d+")

roots = [
    (Path("app/src/main/res/values"), Path("app/src/main/res/values-ru"), Path("app/src/main/res/xml/locales_config.xml")),
    (Path("wear/src/main/res/values"), Path("wear/src/main/res/values-ru"), Path("wear/src/main/res/xml/locales_config.xml")),
]

errors: list[str] = []

def parse(path: Path):
    return ET.parse(path).getroot()

def entries(path: Path):
    root = parse(path)
    out = {}
    for child in root:
        if child.tag == "string":
            if child.attrib.get("translatable") == "false":
                continue
            out[("string", child.attrib["name"], None)] = child.text or ""
        elif child.tag == "plurals":
            name = child.attrib["name"]
            for item in child.findall("item"):
                out[("plurals", name, item.attrib["quantity"])] = item.text or ""
    return out

for base, ru, locale_config in roots:
    if not ru.exists():
        errors.append(f"missing Russian resource directory: {ru}")
        continue
    if 'android:name="ru"' not in locale_config.read_text(encoding="utf-8"):
        errors.append(f"ru missing from locale config: {locale_config}")

    source_files = sorted(p.name for p in base.glob("strings*.xml"))
    ru_files = sorted(p.name for p in ru.glob("strings*.xml"))
    if source_files != ru_files:
        errors.append(f"file set differs for {base}: source={source_files}, ru={ru_files}")
        continue

    for name in source_files:
        src = entries(base / name)
        dst = entries(ru / name)
        if set(src) != set(dst):
            missing = sorted(set(src) - set(dst))
            extra = sorted(set(dst) - set(src))
            errors.append(f"{name}: resource keys differ; missing={missing[:10]} extra={extra[:10]}")
            continue
        for key, src_text in src.items():
            dst_text = dst[key]
            if Counter(PLACEHOLDER.findall(src_text)) != Counter(PLACEHOLDER.findall(dst_text)):
                errors.append(
                    f"{name}:{key[1]}:{key[2]} placeholders differ: "
                    f"{PLACEHOLDER.findall(src_text)} != {PLACEHOLDER.findall(dst_text)}"
                )
            if not dst_text.strip():
                errors.append(f"{name}:{key[1]}:{key[2]} Russian text is empty")

if errors:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    print(f"RU_RESOURCE_CHECK=FAIL ({len(errors)} issue(s))", file=sys.stderr)
    raise SystemExit(1)

print("RU_RESOURCE_CHECK=PASS")
