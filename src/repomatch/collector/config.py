"""Load the default collection settings and build the sampling queries."""

from dataclasses import asdict, dataclass
from pathlib import Path
import tomllib

STAR_BANDS = {"small": "10..99", "medium": "100..999", "large": ">=1000"}


@dataclass(frozen=True)
class Search:
    name: str
    query: str


@dataclass(frozen=True)
class Config:
    searches: list[Search]
    target_count: int = 3000
    max_file_bytes: int = 100_000
    max_manifests: int = 6
    request_interval: float = 1.0
    timeout: float = 30.0
    retries: int = 4
    max_wait: float = 60.0

    def to_dict(self):
        return asdict(self)


def load_config(path: Path):
    settings = tomllib.loads(path.read_text(encoding="utf-8-sig"))
    sampling = settings.pop("sampling")
    searches = [
        Search(
            f"{language.lower().replace('+', 'p').replace('#', 'sharp')}-{band}",
            f'language:"{language}" stars:{STAR_BANDS[band]} fork:false archived:false is:public',
        )
        for language in sampling["languages"]
        for band in sampling["star_bands"]
    ]
    if not searches:
        raise ValueError("Configure at least one language and star band.")
    config = Config(searches, **settings)
    if config.target_count <= 0 or config.max_manifests < 0:
        raise ValueError("Invalid collection counts.")
    if not 1 <= config.max_file_bytes <= 1_000_000:
        raise ValueError("max_file_bytes must be between 1 and 1,000,000.")
    if min(config.request_interval, config.retries, config.max_wait) < 0 or config.timeout <= 0:
        raise ValueError("Invalid GitHub request settings.")
    return config
