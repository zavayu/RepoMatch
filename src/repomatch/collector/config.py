"""Generate sampling searches from a small TOML collection plan."""

from dataclasses import asdict, dataclass, field
from pathlib import Path
import tomllib

STAR_BANDS = {"small": "10..99", "medium": "100..999", "large": ">=1000"}


@dataclass(frozen=True)
class Search:
    """A query and its first-pass sampling quota."""

    name: str
    query: str
    quota: int = 125
    sort: str = "updated"
    order: str = "desc"


@dataclass(frozen=True)
class Config:
    database: str = "data/working/collector.sqlite3"
    target_count: int = 3000
    max_file_bytes: int = 100_000
    max_manifests: int = 6
    request_interval: float = 1.0
    timeout: float = 30.0
    retries: int = 4
    max_wait: float = 60.0
    searches: list[Search] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Export the actual generated queries for reproducibility."""
        return asdict(self)


def build_searches(plan: dict) -> list[Search]:
    searches = []
    newcomer_quota = plan.get("newcomer_quota", 0)
    cohorts = [("general", plan.get("quota", 125), "")]
    if newcomer_quota:
        cohorts.append(("newcomer", newcomer_quota, " good-first-issues:>0"))

    for language in plan["languages"]:
        language_name = language.lower().replace("+", "p").replace("#", "sharp")
        for band in plan.get("star_bands", list(STAR_BANDS)):
            query = (
                f'language:"{language}" stars:{STAR_BANDS[band]}'
                + plan.get("qualifiers", "")
                + " fork:false archived:false is:public"
            )
            for cohort, quota, qualifier in cohorts:
                name = f"{language_name}-{band}"
                if newcomer_quota:
                    name += f"-{cohort}"
                searches.append(
                    Search(name, query + qualifier, quota, plan.get("sort", "updated"))
                )
    return searches


def load_config(path: Path) -> Config:
    settings = tomllib.loads(path.read_text(encoding="utf-8-sig"))
    searches = build_searches(settings.pop("sampling"))
    config = Config(**settings, searches=searches)

    if not searches or len({search.name for search in searches}) != len(searches):
        raise ValueError("Sampling groups must be nonempty and have unique names")
    if config.target_count <= 0 or config.max_manifests < 0:
        raise ValueError("Invalid collection counts")
    if not 1 <= config.max_file_bytes <= 1_000_000:
        raise ValueError("max_file_bytes must be between 1 and 1,000,000")
    if (
        config.request_interval < 0 or config.timeout <= 0
        or config.retries < 0 or config.max_wait < 0
    ):
        raise ValueError("Invalid API timing settings")
    for search in searches:
        if not 1 <= search.quota <= 1000:
            raise ValueError("Sampling quotas must be between 1 and 1000")
        if search.sort not in {"stars", "forks", "updated", "help-wanted-issues"}:
            raise ValueError("Unsupported search ordering")
    return config

