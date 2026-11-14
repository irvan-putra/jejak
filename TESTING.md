# Testing and dependencies

Python 3.9+. Analysis: standard library only (ast + TF-IDF; analyzed code is
never executed). Heatmap: matplotlib.

Commands run and verified (2026-11-15, Python 3.10):

    python3 rtm.py
    python3 rtm.py --json | python3 -m json.tool       # clean JSON stdout
    python3 rtm.py --viz rtm_heatmap.png
    python3 rtm.py --reqs reqs.md --src src/           # own project
    python3 rtm.py --reqs empty.md                     # rejected: no requirements
    python3 rtm.py --reqs missing.md                   # rejected: cannot read
    python3 rtm.py --src empty-dir/                    # rejected: no code units
    python3 rtm.py --src missing-dir/                  # rejected: not a directory

Verified behavior: the embedded example links 5/6 requirements forward and
flags REQ-6 as a possible coverage gap plus 3 possible orphan code units.
Files with syntax errors are skipped with a stderr warning; duplicate and
nested function names get unique ids (helper, helper#2); source is read as
UTF-8 with replacement for invalid bytes. All links are printed as INFERRED,
not verified coverage.

The Pages site (docs/) was rendered headless and inspected at 1280px and
390px widths.
--json keeps stdout as pure JSON: with --viz the "Heatmap written" line goes to
stderr. --threshold is validated as finite within [0, 1]. Unreadable source
files (permissions) are reported as skipped warnings, not tracebacks.
