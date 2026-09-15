"""Audit non-ASCII characters in text extracted from the final PDF."""

import collections
import sys
import unicodedata


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


text = open(sys.argv[1], encoding="utf-8", errors="ignore").read()
counts = collections.Counter(ch for ch in text if ord(ch) > 127)

for ch, count in sorted(counts.items(), key=lambda item: -item[1]):
    try:
        name = unicodedata.name(ch)
    except ValueError:
        name = f"U+{ord(ch):04X}"
    print(f"U+{ord(ch):04X}  x{count:<3d}  {name}")

print()
print('BAD "RuSSwurm" occurrences:', text.count("RuSSwurm"))
print('GOOD "Rußwurm" occurrences :', text.count("Rußwurm"))
