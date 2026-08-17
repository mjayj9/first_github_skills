"""A tiny CLI that lists GitHub profile achievements and how to earn them."""

import argparse
import json

# Each entry: slug, display name, requirement, tier thresholds, solo-obtainable
ACHIEVEMENTS = [
    ("quickdraw", "Quickdraw",
     "Close an issue or pull request within 5 minutes of opening it.",
     [1], True),
    ("yolo", "YOLO",
     "Merge a pull request without a review.",
     [1], True),
    ("pull-shark", "Pull Shark",
     "Open a pull request that gets merged.",
     [2, 16, 128, 1024], True),
    ("galaxy-brain", "Galaxy Brain",
     "Get an accepted answer in a repository discussion.",
     [2, 8, 16, 32], False),
    ("pair-extraordinaire", "Pair Extraordinaire",
     "Land a merged pull request with a Co-authored-by commit.",
     [1, 10, 24, 48], False),
    ("starstruck", "Starstruck",
     "Own a repository that collects stars.",
     [16, 128, 512, 4096], False),
    ("public-sponsor", "Public Sponsor",
     "Sponsor an open source contributor via GitHub Sponsors.",
     [1], False),
]


def format_tiers(tiers):
    """Render tier thresholds as a readable string."""
    if len(tiers) == 1:
        return "no tiers"
    return "tiers at " + ", ".join(str(t) for t in tiers)


def render(entry):
    """Render one achievement as a multi-line block."""
    slug, name, requirement, tiers, solo = entry
    mark = "[solo]" if solo else "[needs others]"
    return f"{name} {mark}\n  slug: {slug}\n  how:  {requirement}\n  {format_tiers(tiers)}"


def main():
    parser = argparse.ArgumentParser(
        description="List GitHub profile achievements and how to earn them.")
    parser.add_argument("--name", help="show only the achievement with this slug")
    parser.add_argument("--solo", action="store_true",
                        help="show only achievements you can earn on your own")
    parser.add_argument("--json", action="store_true",
                        help="emit machine-readable JSON instead of text")
    args = parser.parse_args()

    entries = ACHIEVEMENTS
    if args.solo:
        entries = [e for e in entries if e[4]]
    if args.name:
        entries = [e for e in entries if e[0] == args.name]
        if not entries:
            parser.error(f"unknown achievement: {args.name}")

    if args.json:
        payload = [
            {"slug": slug, "name": name, "requirement": requirement,
             "tiers": tiers, "solo": solo}
            for slug, name, requirement, tiers, solo in entries
        ]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for entry in entries:
        print(render(entry))
        print()


if __name__ == "__main__":
    main()
