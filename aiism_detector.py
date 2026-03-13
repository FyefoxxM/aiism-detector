#!/usr/bin/env python3
"""
aiism_detector.py
Scans text for AI writing patterns and banned phrases.
Usage:
    python aiism_detector.py myfile.txt
    cat myfile.txt | python aiism_detector.py
"""

import sys
import re
from dataclasses import dataclass


@dataclass
class Flag:
    line_number: int
    line_text: str
    category: str
    pattern_name: str
    match: str


# (category, label, regex)
PATTERNS = [
    # ── Vocabulary: Classic AI tells ──────────────────────────────────
    ("vocabulary", "Em-dash",               r"—"),
    ("vocabulary", "Delve",                 r"\bdelve[sd]?\b"),
    ("vocabulary", "Leverage (verb)",       r"\bleverag(e|ing|ed|es)\b"),
    ("vocabulary", "Utilize",               r"\butilize[sd]?\b"),
    ("vocabulary", "Robust",                r"\brobust\b"),
    ("vocabulary", "Seamless(ly)",          r"\bseamless(ly)?\b"),
    ("vocabulary", "Groundbreaking",        r"\bgroundbreaking\b"),
    ("vocabulary", "Revolutionize",         r"\brevolution(ize|ary|izing|ized)\b"),
    ("vocabulary", "Transformative",        r"\btransformative\b"),
    ("vocabulary", "Holistic",              r"\bholistic\b"),
    ("vocabulary", "Synergy",               r"\bsynerg(y|ies|ize|istic)\b"),
    ("vocabulary", "Facilitate",            r"\bfacilitat(e|ing|ed|ion)\b"),
    ("vocabulary", "Paramount",             r"\bparamount\b"),
    ("vocabulary", "Cutting-edge",          r"\bcutting[- ]?edge\b"),
    ("vocabulary", "Game-changer",          r"\bgame[- ]?changer\b"),

    # ── Vocabulary: Current-era AI tells (2024-2025) ──────────────────
    ("vocabulary", "Tapestry",              r"\btapestr(y|ies)\b"),
    ("vocabulary", "Embark",                r"\bembark(ed|ing|s)?\b"),
    ("vocabulary", "Realm",                 r"\brealm(s)?\b"),
    ("vocabulary", "Beacon",                r"\bbeacon(s)?\b"),
    ("vocabulary", "Meticulous(ly)",        r"\bmeticulous(ly)?\b"),
    ("vocabulary", "Underscore (verb)",     r"\bunderscore[sd]?\b"),
    ("vocabulary", "Pivotal",               r"\bpivotal\b"),
    ("vocabulary", "Testament",             r"\btestament\b"),
    ("vocabulary", "Vibrant",               r"\bvibrant(ly)?\b"),
    ("vocabulary", "Nuanced",               r"\bnuanced?\b"),
    ("vocabulary", "Elevate",               r"\belevat(e|es|ed|ing)\b"),
    ("vocabulary", "Resonate",              r"\bresonate?[sd]?\b"),
    ("vocabulary", "Foster",                r"\bfoster(s|ed|ing)?\b"),
    ("vocabulary", "Showcase",              r"\bshowcase[sd]?\b"),
    ("vocabulary", "Showcasing",            r"\bshowcasing\b"),
    ("vocabulary", "Harness",               r"\bharness(es|ed|ing)?\b"),
    ("vocabulary", "Navigate/Navigating",   r"\bnavigat(e|es|ed|ing)\b"),
    ("vocabulary", "Interplay",             r"\binterplay\b"),
    ("vocabulary", "Multifaceted",          r"\bmultifaceted\b"),
    ("vocabulary", "Comprehensive",         r"\bcomprehensive(ly)?\b"),
    ("vocabulary", "Bolstered",             r"\bbolster(s|ed|ing)?\b"),
    ("vocabulary", "Garner",                r"\bgarner(s|ed|ing)?\b"),
    ("vocabulary", "Aligns with",           r"\balign(s|ed|ing)? with\b"),
    ("vocabulary", "Curated",               r"\bcurat(e|es|ed|ing)\b"),
    ("vocabulary", "Strive(s) to",          r"\bstriv(e|es|ed|ing)\b"),
    ("vocabulary", "Reimagine",             r"\breimagin(e|es|ed|ing)\b"),
    ("vocabulary", "Landscape (metaphor)",  r"\blandscape\b"),
    ("vocabulary", "Journey (metaphor)",    r"\bjourney\b"),
    ("vocabulary", "Notably",               r"\bnotably\b"),
    ("vocabulary", "Ultimately",            r"\bultimately\b"),
    ("vocabulary", "Crucial",               r"\bcrucial(ly)?\b"),
    ("vocabulary", "Enhance",               r"\benhance[sd]?\b"),
    ("vocabulary", "Highlight(ing)",        r"\bhighlight(s|ed|ing)?\b"),
    ("vocabulary", "Emphasizing",           r"\bemphasiz(e|es|ed|ing)\b"),
    ("vocabulary", "Enduring",              r"\benduring\b"),
    ("vocabulary", "Genuinely",             r"\bgenuinely\b"),
    ("vocabulary", "Straightforward",       r"\bstraightforward\b"),
    ("vocabulary", "Dive into",             r"\bdive[sd]? into\b"),
    ("vocabulary", "Unlock",                r"\bunlock(s|ed|ing)?\b"),

    # ── Phrases: Hedging & throat-clearing ────────────────────────────
    ("phrase",    "It's important to note",      r"it'?s important to note"),
    ("phrase",    "It's worth noting",           r"it'?s worth noting"),
    ("phrase",    "It goes without saying",      r"it goes without saying"),
    ("phrase",    "Needless to say",             r"needless to say"),
    ("phrase",    "Generally speaking",          r"generally speaking"),
    ("phrase",    "To put it simply",            r"to put it simply"),
    ("phrase",    "At its core",                 r"at its core"),
    ("phrase",    "A key takeaway",              r"a key takeaway"),
    ("phrase",    "This underscores",            r"this underscores"),
    ("phrase",    "In today's fast-paced world", r"in today'?s .{0,20} world"),
    ("phrase",    "Aims to",                     r"\baims to\b"),
    ("phrase",    "Designed to",                 r"\bdesigned to\b"),
    ("phrase",    "At the end of the day",       r"at the end of the day"),
    ("phrase",    "In conclusion",               r"\bin conclusion\b"),
    ("phrase",    "In summary",                  r"\bin summary\b"),
    ("phrase",    "Overall (conclusion opener)", r"^overall[,:]"),
    ("phrase",    "Touch base",                  r"\btouch base\b"),
    ("phrase",    "Circle back",                 r"\bcircle back\b"),
    ("phrase",    "Moving forward",              r"\bmoving forward\b"),
    ("phrase",    "Email finds you well",        r"(hope this email|email finds you) (finds you )?well"),
    ("phrase",    "It's not X, it's Y",          r"it'?s not .{0,40}?,? it'?s"),
    ("phrase",    "Here's the thing",            r"here'?s the thing"),
    ("phrase",    "Let's be honest",             r"let'?s be honest"),
    ("phrase",    "Not just X, but Y",           r"not just .{0,40}, but\b"),
    ("phrase",    "From X to Y (range cliche)",  r"\bfrom .{3,30} to .{3,30}(,|\.)"),

    # ── Transitions: Stacking formal connectors ────────────────────────
    ("transition", "Moreover",         r"\bmoreover\b"),
    ("transition", "Furthermore",      r"\bfurthermore\b"),
    ("transition", "Additionally",     r"\badditionally\b"),
    ("transition", "Consequently",     r"\bconsequently\b"),
    ("transition", "Thus",             r"\bthus\b"),
    ("transition", "Hence",            r"\bhence\b"),
    ("transition", "Nonetheless",      r"\bnonetheless\b"),
    ("transition", "Notwithstanding",  r"\bnotwithstanding\b"),
    ("transition", "Subsequently",     r"\bsubsequently\b"),
    ("transition", "In addition",      r"\bin addition\b"),
    ("transition", "In contrast",      r"\bin contrast\b"),
    ("transition", "In light of",      r"\bin light of\b"),

    # ── Cadence: Participial phrase endings ───────────────────────────
    ("cadence", "Participial close (-ing phrase)",
     r",\s+(revealing|offering|providing|enabling|allowing|creating|ensuring|highlighting|demonstrating|showcasing|emphasizing|suggesting|indicating)\b"),
]


def detect_broetry(lines):
    """3+ consecutive lines of 1-8 words ending in sentence-terminal punctuation."""
    flags = []
    run = []

    def flush():
        if len(run) >= 3:
            for i, line in run:
                flags.append(Flag(i + 1, line.rstrip(), "cadence", "Broetry (staccato fragments)", line.strip()))
        run.clear()

    for i, line in enumerate(lines):
        s = line.strip()
        words = len(s.split()) if s else 0
        ends_clean = bool(re.search(r"[.!?]$", s))
        if 1 <= words <= 8 and ends_clean:
            run.append((i, line))
        else:
            flush()
    flush()
    return flags


def detect_transition_stacking(lines):
    """3+ consecutive non-blank lines starting with formal transition words."""
    opener = re.compile(
        r"^\s*(moreover|furthermore|additionally|consequently|thus|hence|in addition|in contrast|nonetheless|subsequently)\b",
        re.IGNORECASE
    )
    flags = []
    run = []

    def flush():
        if len(run) >= 3:
            for i, line in run:
                flags.append(Flag(i + 1, line.rstrip(), "cadence", "Transition stacking", line.strip()))
        run.clear()

    for i, line in enumerate(lines):
        if opener.match(line):
            run.append((i, line))
        elif line.strip():
            flush()
    flush()
    return flags


def scan(text):
    lines = text.split("\n")
    flags = []

    for i, line in enumerate(lines):
        for category, label, pattern in PATTERNS:
            for m in re.finditer(pattern, line, re.IGNORECASE | re.MULTILINE):
                flags.append(Flag(i + 1, line.rstrip(), category, label, m.group()))

    flags += detect_broetry(lines)
    flags += detect_transition_stacking(lines)
    flags.sort(key=lambda f: f.line_number)
    return flags


def render(flags, source_name):
    if not flags:
        return "\nNo AIisms detected. Either you're clean or you're lying to yourself."

    by_line = {}
    for f in flags:
        by_line.setdefault(f.line_number, []).append(f)

    cat_counts = {}
    for f in flags:
        cat_counts[f.category] = cat_counts.get(f.category, 0) + 1

    out = [f"\n{source_name} -- {len(flags)} flag(s) across {len(by_line)} line(s)\n" + "-" * 56]

    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        out.append(f"  [{cat}] {count}")

    out.append("")

    for line_num in sorted(by_line):
        group = by_line[line_num]
        preview = group[0].line_text.strip()[:80]
        if len(group[0].line_text.strip()) > 80:
            preview += "..."
        out.append(f"Line {line_num}: {preview}")
        for f in group:
            out.append(f'  [{f.category}] {f.pattern_name} -> "{f.match.strip()}"')
        out.append("")

    out.append("-" * 56)
    out.append(f"Total: {len(flags)} flags in {len(by_line)} lines")
    return "\n".join(out)


def main():
    if len(sys.argv) > 1:
        path = sys.argv[1]
        try:
            with open(path, "r", encoding="utf-8") as fh:
                text = fh.read()
            source = path
        except FileNotFoundError:
            print(f"File not found: {path}", file=sys.stderr)
            sys.exit(1)
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
        source = "stdin"
    else:
        print("Usage: python aiism_detector.py <file.txt>  OR  cat file.txt | python aiism_detector.py")
        sys.exit(0)

    flags = scan(text)
    print(render(flags, source))


if __name__ == "__main__":
    main()
