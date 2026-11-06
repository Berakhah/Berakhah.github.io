#!/usr/bin/env python3
"""Fail if any price on the site disagrees with assets/data/pricing.json.

Checks two things in every .html page:
1. Each element marked data-price="<key>" shows exactly the price for <key>.
2. On pages that show prices (any data-price element), every other dollar
   amount in the visible text is one of the listed prices, so an unmarked
   price can't drift unnoticed.
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
prices = {k: v for k, v in json.loads((ROOT / "assets/data/pricing.json").read_text()).items()
          if isinstance(v, int)}
fmt = lambda n: f"${n:,}"
allowed = {fmt(v) for v in prices.values()}
errors = []

for page in sorted(ROOT.rglob("*.html")):
    html = page.read_text(encoding="utf-8")
    marked = re.findall(r'data-price="([a-z]+)"[^>]*>([^<]*)<', html)
    for key, shown in marked:
        if key not in prices:
            errors.append(f"{page.relative_to(ROOT)}: unknown price key '{key}'")
        elif shown.strip() != fmt(prices[key]):
            errors.append(f"{page.relative_to(ROOT)}: {key} shows {shown.strip()!r}, pricing.json says {fmt(prices[key])}")
    if marked:
        text = re.sub(r"<(script|style)\b.*?</\1>", "", html, flags=re.S)
        text = re.sub(r"<[^>]+>", " ", text)
        for amount in set(re.findall(r"\$[\d,]+", text)):
            if amount not in allowed:
                errors.append(f"{page.relative_to(ROOT)}: unlisted price {amount}")

if errors:
    print("\n".join(errors)); sys.exit(1)
print(f"Prices match pricing.json ({', '.join(sorted(allowed))}).")
