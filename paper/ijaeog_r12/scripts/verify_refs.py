"""Verify the manuscript's cited BibTeX entries against Crossref.

Usage: python verify_refs.py <references.bib> <sections_dir> <out.csv>

The script is audit-only: it never modifies the bibliography.
"""

from __future__ import annotations

import csv
import glob
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from difflib import SequenceMatcher


def norm(value: str) -> str:
    value = value or ""
    replacements = {
        r"{\ss}": "ss",
        r"\ss": "ss",
        r"{\l}": "l",
        r"\l": "l",
        "{": "",
        "}": "",
        "~": " ",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    value = re.sub(r"\\[A-Za-z]+\s*", "", value)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = re.sub(r"[^a-z0-9 ]", " ", value.lower())
    return re.sub(r"\s+", " ", value).strip()


def iter_entries(text: str):
    pos = 0
    while True:
        match = re.search(r"@(\w+)\s*\{\s*([^,]+),", text[pos:], re.S)
        if not match:
            return
        entry_type = match.group(1)
        key = match.group(2).strip()
        start = pos + match.end()
        depth = 1
        quote = False
        idx = start
        while idx < len(text) and depth:
            char = text[idx]
            if char == '"' and (idx == 0 or text[idx - 1] != "\\"):
                quote = not quote
            elif not quote:
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
            idx += 1
        yield entry_type, key, text[start : idx - 1]
        pos = idx


def parse_fields(body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    idx = 0
    while idx < len(body):
        match = re.search(r"([A-Za-z][A-Za-z0-9_-]*)\s*=\s*", body[idx:])
        if not match:
            break
        name = match.group(1).lower()
        cursor = idx + match.end()
        if cursor >= len(body):
            break
        opener = body[cursor]
        if opener == "{":
            depth = 1
            end = cursor + 1
            while end < len(body) and depth:
                if body[end] == "{":
                    depth += 1
                elif body[end] == "}":
                    depth -= 1
                end += 1
            value = body[cursor + 1 : end - 1]
        elif opener == '"':
            end = cursor + 1
            while end < len(body):
                if body[end] == '"' and body[end - 1] != "\\":
                    end += 1
                    break
                end += 1
            value = body[cursor + 1 : end - 1]
        else:
            end = cursor
            while end < len(body) and body[end] not in ",\n":
                end += 1
            value = body[cursor:end]
        fields[name] = re.sub(r"\s+", " ", value).strip()
        idx = end
    return fields


def parse_bib(path: str) -> dict[str, dict[str, str]]:
    text = open(path, encoding="utf-8", errors="ignore").read()
    entries: dict[str, dict[str, str]] = {}
    for entry_type, key, body in iter_entries(text):
        fields = parse_fields(body)
        fields["type"] = entry_type
        entries[key] = fields
    return entries


def cited_keys(sections_dir: str) -> set[str]:
    paper_dir = os.path.dirname(sections_dir)
    paths = glob.glob(os.path.join(sections_dir, "*.tex"))
    paths += glob.glob(os.path.join(paper_dir, "tables", "*.tex"))
    cited: set[str] = set()
    for path in paths:
        text = open(path, encoding="utf-8", errors="ignore").read()
        for match in re.finditer(r"\\cite[a-zA-Z]*\{([^}]*)\}", text):
            cited.update(k.strip() for k in match.group(1).split(",") if k.strip())
    return cited


def first_surname(author_field: str) -> str:
    first = author_field.split(" and ")[0].strip()
    if "," in first:
        return first.split(",", 1)[0].strip()
    return first.split()[-1] if first else ""


def issued_year(message: dict) -> str:
    candidates = (
        message.get("issued"),
        message.get("published-print"),
        message.get("published-online"),
    )
    for candidate in candidates:
        try:
            return str(candidate["date-parts"][0][0])
        except (TypeError, KeyError, IndexError):
            pass
    return ""


def main() -> int:
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    bib_path, sections_dir, out_path = sys.argv[1:]
    entries = parse_bib(bib_path)
    cited = cited_keys(sections_dir)
    rows = []
    for key in sorted(cited):
        entry = entries.get(key)
        if not entry:
            rows.append([key, "MISSING_FROM_BIB", "", "", "", "MISSING_FROM_BIB", "", "", "", "", ""])
            continue
        doi = entry.get("doi", "").strip()
        doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.I)
        if not doi:
            rows.append([key, "NO_DOI", "", "", "", "NO_DOI", entry.get("title", "")[:120], entry.get("year", ""), first_surname(entry.get("author", "")), "", ""])
            continue
        url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "RiskControlledEarlyCrop-ref-verify/1.0 (mailto:noreply@example.com)"},
            )
            with urllib.request.urlopen(request, timeout=25) as response:
                status = response.status
                message = json.load(response)["message"]
            bib_title = norm(entry.get("title", ""))
            cr_title_raw = (message.get("title") or [""])[0]
            cr_title = norm(cr_title_raw)
            title_ratio = SequenceMatcher(None, bib_title, cr_title).ratio()
            title_ok = bool(bib_title and cr_title and (title_ratio >= 0.88 or bib_title in cr_title or cr_title in bib_title))
            cr_year = issued_year(message)
            year_ok = cr_year == entry.get("year", "").strip()
            bib_surname = norm(first_surname(entry.get("author", "")))
            cr_authors = " ".join(
                (author.get("family", "") + " " + author.get("given", "")).strip()
                for author in message.get("author", [])
            )
            author_ok = bool(bib_surname and bib_surname in norm(cr_authors))
            verdict = "OK" if status == 200 and title_ok and year_ok and author_ok else "REVIEW"
            rows.append([
                key,
                status,
                f"{title_ok} ({title_ratio:.3f})",
                str(year_ok),
                str(author_ok),
                verdict,
                cr_title_raw[:120],
                cr_year,
                (message.get("author") or [{}])[0].get("family", ""),
                doi,
                "",
            ])
        except Exception as exc:  # audit output records all lookup failures
            rows.append([key, "ERROR", "", "", "", "ERROR", "", "", "", doi, str(exc)[:160]])
        time.sleep(0.4)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "key",
            "http",
            "title_match",
            "year_match",
            "author_match",
            "verdict",
            "crossref_title",
            "crossref_year",
            "crossref_first_author",
            "doi",
            "error",
        ])
        writer.writerows(rows)
    print(f"checked {len(rows)} cited keys -> {out_path}")
    print(f"bib entries: {len(entries)}; cited: {len(cited)}; uncited: {len(set(entries) - cited)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
