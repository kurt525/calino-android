#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

PLACEHOLDER = re.compile(r"%(?:\d+\$)?[-#+ 0,(]*\d*(?:\.\d+)?[a-zA-Z%]|\^\d+")
RU_REQUIRED_QUANTITIES = {"one", "few", "many", "other"}

roots = [
    (Path("app/src/main/res/values"), Path("app/src/main/res/values-ru"), Path("app/src/main/res/xml/locales_config.xml")),
    (Path("wear/src/main/res/values"), Path("wear/src/main/res/values-ru"), Path("wear/src/main/res/xml/locales_config.xml")),
]

errors: list[str] = []

def parse(path: Path):
    return ET.parse(path).getroot()

def string_map(path: Path):
    out={}
    for child in parse(path):
        if child.tag=="string" and child.attrib.get("translatable")!="false":
            out[child.attrib["name"]]=child.text or ""
    return out

def plural_map(path: Path):
    out={}
    for child in parse(path):
        if child.tag=="plurals":
            out[child.attrib["name"]]={item.attrib["quantity"]:item.text or "" for item in child.findall("item")}
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
        src_strings=string_map(base/name)
        dst_strings=string_map(ru/name)
        if set(src_strings)!=set(dst_strings):
            errors.append(f"{name}: string resource keys differ")
        for key,src_text in src_strings.items():
            dst_text=dst_strings.get(key,"")
            if Counter(PLACEHOLDER.findall(src_text)) != Counter(PLACEHOLDER.findall(dst_text)):
                errors.append(f"{name}:{key} placeholders differ")
            if not dst_text.strip():
                errors.append(f"{name}:{key} Russian text is empty")

        src_plurals=plural_map(base/name)
        dst_plurals=plural_map(ru/name)
        if set(src_plurals)!=set(dst_plurals):
            errors.append(f"{name}: plural resource names differ")
        for key,src_forms in src_plurals.items():
            dst_forms=dst_plurals.get(key,{})
            if not RU_REQUIRED_QUANTITIES.issubset(dst_forms):
                errors.append(f"{name}:{key} missing Russian plural quantities: {sorted(RU_REQUIRED_QUANTITIES-set(dst_forms))}")
                continue
            source_other=src_forms.get("other","")
            source_one=src_forms.get("one","")
            source_other_placeholders=Counter(PLACEHOLDER.findall(source_other))
            source_one_placeholders=Counter(PLACEHOLDER.findall(source_one))
            for quantity in RU_REQUIRED_QUANTITIES:
                text=dst_forms[quantity]
                # English singular resources sometimes hard-code the literal 1 while
                # the plural form receives the count as a formatting argument. Russian
                # quantity=one also matches 21, 31, ...; therefore it must keep that
                # count placeholder or Android Lint reports ImpliedQuantity.
                reference = (
                    source_other
                    if quantity == "one" and not source_one_placeholders and source_other_placeholders
                    else source_one if quantity == "one" else source_other
                )
                if Counter(PLACEHOLDER.findall(text)) != Counter(PLACEHOLDER.findall(reference)):
                    errors.append(f"{name}:{key}:{quantity} placeholders differ from source plural form")
                if not text.strip():
                    errors.append(f"{name}:{key}:{quantity} Russian plural text is empty")

if errors:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    print(f"RU_RESOURCE_CHECK=FAIL ({len(errors)} issue(s))", file=sys.stderr)
    raise SystemExit(1)

print("RU_RESOURCE_CHECK=PASS")
