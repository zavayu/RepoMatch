"""Find a sample across the configured language and popularity groups."""

import logging

from .github import GitHubError

LOG = logging.getLogger(__name__)
PAGE_SIZE = 100
MAX_SEARCH_PAGES = 10


def discover(client, config, target):
    """Return candidates with the first search that selected each one."""
    candidates = {}
    searches = config.searches
    for index, search in enumerate(searches, start=1):
        # Spread a small run across the same groups as the full run.
        quota = target * index // len(searches) - target * (index - 1) // len(searches)
        if quota == 0:
            continue

        added = 0
        for page in range(1, MAX_SEARCH_PAGES + 1):
            response = client.get(
                "/search/repositories",
                {"q": search.query, "sort": "updated", "per_page": PAGE_SIZE, "page": page},
            )
            if response.get("incomplete_results"):
                raise GitHubError(f"Search {search.name} returned incomplete results. Try again.")

            for repo in response["items"]:
                if repo["id"] in candidates or any(
                    repo.get(flag) for flag in ("private", "fork", "archived", "disabled")
                ):
                    continue
                candidates[repo["id"]] = (repo, search)
                added += 1
                if added == quota:
                    break

            if added == quota or len(response["items"]) < PAGE_SIZE:
                break

        LOG.info("%s: found %d of %d candidates", search.name, added, quota)

    if len(candidates) < target:
        LOG.warning("Found %d of %d requested candidates", len(candidates), target)
    return list(candidates.values())
