"""Discover a balanced first pass, then fill gaps with unique repositories."""

import json
import logging

from .github import GitHubError

LOG = logging.getLogger(__name__)
PAGE_SIZE = 100
MAX_SEARCH_PAGES = 10


def search_quotas(searches, target: int) -> dict:
    """Scale quotas proportionally; cumulative rounding preserves every slot."""
    total_slots = sum(search.quota for search in searches)
    target = min(target, total_slots)
    quotas = {}
    cumulative_slots = 0
    allocated = 0
    for search in searches:
        cumulative_slots += search.quota
        next_allocation = target * cumulative_slots // total_slots
        quotas[search.name] = next_allocation - allocated
        allocated = next_allocation
    return quotas


def discover(client, store, config, limit=None) -> int:
    target = min(limit, config.target_count) if limit is not None else config.target_count
    quotas = search_quotas(config.searches, target)
    backfill = False

    while store.count() < target:
        requested_any_page = False
        for search in config.searches:
            if store.count() >= target:
                break

            key = json.dumps([search.name, search.query, search.sort, search.order])
            progress = store.progress(key)
            if progress["exhausted"]:
                continue
            if not backfill and store.search_count(search) >= quotas[search.name]:
                continue

            page = progress["page"]
            response = client.get(
                "/search/repositories",
                {
                    "q": search.query,
                    "sort": search.sort,
                    "order": search.order,
                    "per_page": PAGE_SIZE,
                    "page": page,
                },
            )
            if response.get("incomplete_results"):
                raise GitHubError(
                    f"Search {search.name} returned incomplete results; "
                    "narrow the query and retry"
                )

            repositories = response["items"]
            consumed_page = True
            for repository in repositories:
                quota_filled = store.search_count(search) >= quotas[search.name]
                if store.count() >= target or (not backfill and quota_filled):
                    consumed_page = False
                    break
                if not any(
                    repository.get(flag)
                    for flag in ("private", "fork", "archived", "disabled")
                ):
                    store.add(repository, search)

            # Retain interrupted pages for a larger run or the backfill pass.
            # Replaying saved IDs is safe because the store deduplicates them.
            exhausted = consumed_page and (
                len(repositories) < PAGE_SIZE or page >= MAX_SEARCH_PAGES
            )
            store.save_progress(
                key, page + 1 if consumed_page else page,
                exhausted, response.get("total_count", 0), False,
            )
            requested_any_page = True

        if not requested_any_page:
            if backfill:
                break
            LOG.info(
                "First-pass groups finished; backfilling unique candidates "
                "from the same queries."
            )
            backfill = True

    count = store.count()
    if count < target:
        LOG.warning("Collected %s of %s candidates; accessible searches exhausted.", count, target)
    return count

