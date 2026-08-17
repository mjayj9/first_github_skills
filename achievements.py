"""A tiny CLI that lists GitHub profile achievements and how to earn them."""

import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API_ROOT = "https://api.github.com"
CACHE_PATH = Path.home() / ".cache" / "first-github-skills" / "api.json"
CACHE_TTL_SECONDS = 900

# Set from main(); the probes below read it rather than threading it through.
use_cache = True

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


class ApiError(Exception):
    """Raised when GitHub cannot be reached or refuses the request."""


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


def load_cache():
    """Read the on-disk response cache, treating any problem as a cold cache."""
    try:
        with CACHE_PATH.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def save_cache(cache):
    """Persist the response cache. A broken cache must never break the command."""
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with CACHE_PATH.open("w", encoding="utf-8") as handle:
            json.dump(cache, handle)
    except OSError:
        pass


def api_get(path, params=None):
    """GET a GitHub API path, serving from cache when a fresh entry exists.

    Unauthenticated search is capped at 10 requests per minute, so repeated
    --check runs would hit the limit fast. Caching keeps the common case
    (checking your own progress a few times) to a single network call.
    """
    url = API_ROOT + path
    if params:
        url += "?" + urllib.parse.urlencode(params)

    cache = load_cache() if use_cache else {}
    entry = cache.get(url)
    if entry and time.time() - entry["fetched_at"] < CACHE_TTL_SECONDS:
        return entry["payload"]

    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "first-github-skills-achievements",
    })
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        # Search rejects an unknown author with 422 rather than 404.
        if exc.code in (404, 422):
            raise ApiError("user not found") from exc
        if exc.code in (403, 429):
            raise ApiError(
                "rate limited by GitHub; set GITHUB_TOKEN to raise the limit") from exc
        raise ApiError(f"GitHub returned HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise ApiError(f"could not reach GitHub: {exc.reason}") from exc

    if use_cache:
        cache[url] = {"fetched_at": time.time(), "payload": payload}
        save_cache(cache)
    return payload


def probe_pull_shark(username):
    """Count merged pull requests authored by the user."""
    data = api_get("/search/issues", {
        "q": f"author:{username} is:pr is:merged",
        "per_page": 1,
    })
    return data.get("total_count", 0), "merged pull requests"


def probe_starstruck(username):
    """Find the star count of the user's most-starred public repository."""
    repos = api_get(f"/users/{username}/repos", {"per_page": 100, "sort": "pushed"})
    if not repos:
        return 0, "stars (no public repositories found)"
    top = max(repos, key=lambda repo: repo.get("stargazers_count", 0))
    return top.get("stargazers_count", 0), f"stars on {top.get('full_name')}"


# Only these achievements leave a trace the public API can count.
PROBES = {
    "pull-shark": probe_pull_shark,
    "starstruck": probe_starstruck,
}


def earned_tier(count, tiers):
    """Return the highest tier threshold reached, or None if none is."""
    reached = [tier for tier in tiers if count >= tier]
    return max(reached) if reached else None


def next_tier(count, tiers):
    """Return the lowest tier threshold not yet reached, or None if all are."""
    remaining = [tier for tier in tiers if count < tier]
    return min(remaining) if remaining else None


def check_progress(username):
    """Build a progress report for every achievement the API can measure."""
    results = []
    for slug, name, _requirement, tiers, _solo in ACHIEVEMENTS:
        probe = PROBES.get(slug)
        if probe is None:
            results.append({"slug": slug, "name": name, "checkable": False})
            continue
        count, unit = probe(username)
        results.append({
            "slug": slug,
            "name": name,
            "checkable": True,
            "count": count,
            "unit": unit,
            "earned_tier": earned_tier(count, tiers),
            "next_tier": next_tier(count, tiers),
        })
    return results


def render_progress(username, results):
    """Render a progress report as text."""
    lines = [f"Progress for {username}", ""]
    for result in results:
        if not result["checkable"]:
            continue
        lines.append(result["name"])
        lines.append(f"  {result['count']} {result['unit']}")
        earned, upcoming = result["earned_tier"], result["next_tier"]
        status = f"earned: tier {earned}" if earned else "not earned yet"
        if upcoming:
            status += f" -> next tier at {upcoming} ({upcoming - result['count']} to go)"
        else:
            status += " -> all tiers earned"
        lines.append(f"  {status}")
        lines.append("")

    skipped = [r["name"] for r in results if not r["checkable"]]
    if skipped:
        lines.append("Not measurable via the public API: " + ", ".join(skipped))
    return "\n".join(lines)


def main():
    global use_cache

    parser = argparse.ArgumentParser(
        description="List GitHub profile achievements and how to earn them.")
    parser.add_argument("--name", help="show only the achievement with this slug")
    parser.add_argument("--solo", action="store_true",
                        help="show only achievements you can earn on your own")
    parser.add_argument("--json", action="store_true",
                        help="emit machine-readable JSON instead of text")
    parser.add_argument("--check", metavar="USERNAME",
                        help="query the GitHub API for this user's actual progress")
    parser.add_argument("--no-cache", action="store_true",
                        help="bypass the local response cache when checking")
    args = parser.parse_args()

    use_cache = not args.no_cache

    if args.check:
        try:
            results = check_progress(args.check)
        except ApiError as exc:
            raise SystemExit(f"error: {exc}")
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print(render_progress(args.check, results))
        return

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
