#!/usr/bin/env python3
"""
rtm.py - bidirectional requirements-traceability demo (jejak).

A minimal, runnable illustration of the concept in proposal-gemini.md:
forward traceability (requirement -> code) and backward traceability
(code -> requirement), inferred from TF-IDF cosine similarity between
natural-language requirements and code units parsed with the `ast` module.

IMPORTANT: every link this script reports is an INFERRED heuristic match,
not verified evidence that a requirement is implemented. Semantic
similarity is not proof of coverage (see framing-and-limitations.md).
A real system would have to measure precision/recall against
human-confirmed traces before anyone trusts it in CI.

Analysis uses ast.parse only - the analyzed code is never executed.
Runs on Python 3.9+ with no third-party dependency for the analysis.
The --viz option needs matplotlib.

Usage:
    python3 rtm.py                  # text report on the embedded example
    python3 rtm.py --threshold 0.2  # stricter/looser link threshold
    python3 rtm.py --viz rtm_heatmap.png
    python3 rtm.py --reqs my_reqs.md --src my_project/   # your own project
"""

import argparse
import ast
import json
import math
import re
import sys
from collections import Counter

# ---------------------------------------------------------------------------
# Embedded example: a small habit-tracker CLI (fictional, written for this demo)
# ---------------------------------------------------------------------------

EXAMPLE_REQS = """\
# Requirements (example)

REQ-1 The user shall be able to add a habit with a name and a target frequency per week.
REQ-2 The user shall be able to mark a habit as completed for the current day.
REQ-3 The system shall compute the current streak of consecutive days for each habit.
REQ-4 The system shall export all habit data as JSON so the user can back it up.
REQ-5 The system shall remind the user when a habit's weekly target is not yet met.
REQ-6 The user shall be able to delete a habit and all of its history.
"""

EXAMPLE_CODE = {
    "habits.py": '''\
"""Core habit storage."""

def add_habit(store, name, target_per_week):
    """Add a new habit with a name and weekly target frequency."""
    store[name] = {"target": target_per_week, "days": []}
    return store

def complete_habit(store, name, day):
    """Mark a habit as completed for a given day."""
    store[name]["days"].append(day)

def current_streak(store, name, today):
    """Compute consecutive-day streak ending today."""
    days = set(store[name]["days"])
    streak = 0
    while today - streak in days:
        streak += 1
    return streak

def legacy_format(rows):
    # older CSV dump kept for one migration; nothing references it now
    return "\\n".join(",".join(map(str, r)) for r in rows)
''',
    "export.py": '''\
"""Data export helpers."""
import json

def export_json(store, path):
    """Export all habit data as JSON for backup."""
    with open(path, "w") as fh:
        json.dump(store, fh, indent=2)
''',
    "cli.py": '''\
"""Command-line entry points."""

def parse_args(argv):
    """Parse command-line arguments."""
    return argv[1:]

def main(argv):
    """Run the habit tracker CLI."""
    args = parse_args(argv)
    return 0
''',
}

WORD_RE = re.compile(r"[a-z][a-z0-9]+")
CAMEL_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")

STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "for", "in", "on", "with",
    "as", "by", "is", "be", "shall", "able", "all", "so", "that", "this",
    "when", "not", "yet", "per", "each", "its", "it", "from", "into",
}


def tokenize(text):
    """Lowercase word tokens; snake_case and camelCase identifiers split."""
    text = CAMEL_RE.sub("_", text)
    tokens = WORD_RE.findall(text.lower().replace("_", " "))
    return [t for t in tokens if t not in STOPWORDS]


def parse_requirements(md_text):
    """Split a requirements markdown file into (req_id, text) chunks."""
    reqs = []
    for line in md_text.splitlines():
        m = re.match(r"\s*(REQ-\d+)\s+(.*)", line)
        if m:
            reqs.append((m.group(1), m.group(2).strip()))
    return reqs


def code_units_from_source(filename, source):
    """Extract functions/classes as documented code units via AST.

    Uses ast.parse only: the analyzed code is never executed. Nested
    functions are included; duplicate names get a numeric suffix so every
    unit id stays unique.
    """
    tree = ast.parse(source)  # may raise SyntaxError - caller handles
    units = []
    seen = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(node) or ""
            seg = ast.get_source_segment(source, node) or ""
            comments = " ".join(
                ln.strip()[1:] for ln in seg.splitlines() if ln.strip().startswith("#")
            )
            base = f"{filename}:{node.name}"
            seen[base] = seen.get(base, 0) + 1
            uid = base if seen[base] == 1 else f"{base}#{seen[base]}"
            units.append({
                "id": uid,
                "text": f"{node.name} {doc} {comments}".strip(),
            })
    return units


def tfidf_vectors(docs):
    """TF-IDF vectors (l2-normalized) for a list of token lists."""
    df = Counter()
    for tokens in docs:
        df.update(set(tokens))
    n = len(docs)
    idf = {t: math.log((n + 1) / (c + 1)) + 1 for t, c in df.items()}
    vecs = []
    for tokens in docs:
        tf = Counter(tokens)
        v = {t: (c / max(1, len(tokens))) * idf[t] for t, c in tf.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vecs.append({t: x / norm for t, x in v.items()})
    return vecs


def cosine(a, b):
    """Cosine similarity of two sparse vectors."""
    if len(a) > len(b):
        a, b = b, a
    return sum(w * b.get(t, 0.0) for t, w in a.items())


def build_matrix(reqs, units):
    docs = [tokenize(text) for _, text in reqs] + [tokenize(u["text"]) for u in units]
    vecs = tfidf_vectors(docs)
    rvecs, uvecs = vecs[: len(reqs)], vecs[len(reqs):]
    return [[cosine(rv, uv) for uv in uvecs] for rv in rvecs]


def report(reqs, units, matrix, threshold):
    lines = []
    lines.append("FORWARD TRACEABILITY (requirement -> code)  [INFERRED, unverified]")
    uncovered = []
    for i, (rid, text) in enumerate(reqs):
        ranked = sorted(
            enumerate(matrix[i]), key=lambda kv: kv[1], reverse=True
        )[:3]
        best = [(units[j]["id"], s) for j, s in ranked if s >= threshold]
        if not best:
            uncovered.append(rid)
            lines.append(f"  {rid}: NO LINK >= {threshold:.2f}  <- possible coverage gap")
        else:
            links = ", ".join(f"{uid} ({s:.2f})" for uid, s in best)
            lines.append(f"  {rid}: {links}")
        lines.append(f"        \"{text[:70]}\"")
    lines.append("")
    lines.append("BACKWARD TRACEABILITY (code -> requirement)  [INFERRED, unverified]")
    orphans = []
    for j, unit in enumerate(units):
        best_i = max(range(len(reqs)), key=lambda i: matrix[i][j])
        score = matrix[best_i][j]
        if score >= threshold:
            lines.append(f"  {unit['id']}: {reqs[best_i][0]} ({score:.2f})")
        else:
            orphans.append(unit["id"])
            lines.append(
                f"  {unit['id']}: NO LINK >= {threshold:.2f}  <- possible orphan code"
            )
    lines.append("")
    lines.append(
        f"Summary: {len(uncovered)} requirement(s) without an inferred code link: "
        f"{', '.join(uncovered) or 'none'}"
    )
    lines.append(
        f"         {len(orphans)} code unit(s) without an inferred requirement link: "
        f"{', '.join(orphans) or 'none'}"
    )
    lines.append(
        "Reminder: these are similarity heuristics. A strong link does not prove a "
        "requirement is implemented; a weak link does not prove it is missing."
    )
    return "\n".join(lines)


def make_heatmap(reqs, units, matrix, threshold, path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    data = np.array(matrix)
    fig, ax = plt.subplots(figsize=(max(6, len(units) * 1.1), max(4, len(reqs) * 0.7)))
    im = ax.imshow(data, cmap="viridis", vmin=0, vmax=max(0.5, data.max()))
    ax.set_xticks(range(len(units)))
    ax.set_xticklabels(
        [u["id"] for u in units], fontsize=8, rotation=35, ha="right"
    )
    ax.set_yticks(range(len(reqs)))
    ax.set_yticklabels([r for r, _ in reqs], fontsize=9)
    for i in range(len(reqs)):
        for j in range(len(units)):
            if matrix[i][j] >= threshold:
                ax.text(
                    j, i, f"{matrix[i][j]:.2f}", ha="center", va="center",
                    color="white", fontsize=8, weight="bold",
                )
    ax.set_title(
        "Requirements x code similarity (TF-IDF cosine)\n"
        f"cells annotated where score >= {threshold:.2f} - INFERRED links, not verified coverage",
        fontsize=10,
    )
    fig.colorbar(im, ax=ax, label="cosine similarity")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--reqs", help="requirements markdown file (default: embedded example)")
    ap.add_argument("--src", help="directory of .py files (default: embedded example)")
    ap.add_argument("--threshold", type=float, default=0.15)
    ap.add_argument("--viz", metavar="PNG", help="write a similarity heatmap to this path")
    ap.add_argument("--json", action="store_true", help="emit the matrix as JSON")
    args = ap.parse_args()
    if not math.isfinite(args.threshold) or not 0.0 <= args.threshold <= 1.0:
        ap.error("--threshold must be a finite number in [0, 1]")

    if args.reqs:
        try:
            with open(args.reqs, encoding="utf-8", errors="replace") as fh:
                reqs = parse_requirements(fh.read())
        except OSError as exc:
            sys.exit(f"cannot read requirements file: {exc}")
    else:
        reqs = parse_requirements(EXAMPLE_REQS)
    if not reqs:
        sys.exit("no requirements found (expected lines starting with REQ-<n>)")

    units = []
    skipped = []
    if args.src:
        import pathlib

        src = pathlib.Path(args.src)
        if not src.is_dir():
            sys.exit(f"source directory not found: {args.src}")
        for py in sorted(src.rglob("*.py")):
            try:
                text = py.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                skipped.append(f"{py} (unreadable: {exc})")
                continue
            try:
                units.extend(code_units_from_source(str(py), text))
            except SyntaxError as exc:
                skipped.append(f"{py} ({exc})")
    else:
        for fname, source in EXAMPLE_CODE.items():
            units.extend(code_units_from_source(fname, source))
    for s in skipped:
        print(f"warning: skipped unparseable file: {s}", file=sys.stderr)
    if not units:
        sys.exit("no functions or classes found in the source")

    matrix = build_matrix(reqs, units)
    if args.json:
        print(json.dumps({
            "requirements": [r for r, _ in reqs],
            "code_units": [u["id"] for u in units],
            "similarity": matrix,
            "threshold": args.threshold,
            "status": "inferred links only - not verified coverage",
        }, indent=2))
    else:
        print(report(reqs, units, matrix, args.threshold))
    if args.viz:
        path = make_heatmap(reqs, units, matrix, args.threshold, args.viz)
        # keep stdout pure JSON when --json is set
        print(f"\nHeatmap written to {path}", file=sys.stderr if args.json else sys.stdout)


if __name__ == "__main__":
    main()
