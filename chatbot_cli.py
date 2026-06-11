#!/usr/bin/env python
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent / "src"))
from retrieve_estimate import retrieve

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="DHIS/NHIS FAQ-estimate prototype CLI")
    parser.add_argument("question", nargs="+", help="Question to answer")
    parser.add_argument("--debug", action="store_true", help="Include matched source details")
    args = parser.parse_args()
    print(retrieve(" ".join(args.question), debug=args.debug)["answer"])
