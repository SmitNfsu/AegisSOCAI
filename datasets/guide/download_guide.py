#!/usr/bin/env python3
"""Fetch the Microsoft GUIDE security-incident dataset into this folder.

The full CSVs (GUIDE_Train.csv ~2.4GB, GUIDE_Test.csv ~1GB) are too large for
GitHub, so they are not committed. A 20k-row sample and the full queue-ranking
ground truth live in ./sample. Run this to pull the complete set.

Prereqs:
  1. pip install kaggle
  2. Kaggle API token at ~/.kaggle/kaggle.json  (Kaggle → Account → Create New API Token)
  3. Accept the dataset terms once on the dataset page.

Usage:
  python datasets/guide/download_guide.py
"""
import pathlib
import subprocess
import sys

DATASET = "Microsoft/microsoft-security-incident-prediction"   # CDLA-2.0
DEST = pathlib.Path(__file__).resolve().parent
EXPECTED = ["GUIDE_Train.csv", "GUIDE_Test.csv", "GUIDE_Test_Queue_Rankings.csv"]


def main() -> int:
    have = [f for f in EXPECTED if (DEST / f).exists()]
    if len(have) == len(EXPECTED):
        print("GUIDE already present in", DEST)
        return 0
    try:
        import kaggle  # noqa: F401
    except ImportError:
        print("Install the Kaggle client first:  pip install kaggle", file=sys.stderr)
        return 1
    print(f"Downloading {DATASET} into {DEST} (large; may take a while)...")
    # kaggle CLI handles auth (~/.kaggle/kaggle.json) and unzips in place.
    r = subprocess.run(
        ["kaggle", "datasets", "download", "-d", DATASET, "-p", str(DEST), "--unzip"],
        check=False,
    )
    if r.returncode != 0:
        print("Download failed. Check Kaggle auth and that you accepted the dataset terms.",
              file=sys.stderr)
        return r.returncode
    missing = [f for f in EXPECTED if not (DEST / f).exists()]
    if missing:
        print("Downloaded, but missing:", missing, "— check the dataset layout.", file=sys.stderr)
        return 1
    print("Done. Full GUIDE dataset ready in", DEST)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
