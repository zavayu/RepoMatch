"""Serve the existing recommender to the web frontend."""

from contextlib import asynccontextmanager
import os
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field, StringConstraints

from repomatch.recommender import RepoMatch, load_repositories


@asynccontextmanager
async def lifespan(app):
    # Build the index once, rather than once per search
    default_dataset = Path(__file__).resolve().parents[2] / "data/repositories.jsonl"
    dataset = Path(os.environ.get("REPOMATCH_DATASET", default_dataset))
    app.state.matcher = RepoMatch(load_repositories(dataset))
    yield


app = FastAPI(title="RepoMatch", lifespan=lifespan)


class SearchRequest(BaseModel):
    query: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
    skills: list[Annotated[str, Field(max_length=100)]] = Field(default_factory=list, max_length=50)
    mode: Literal["personalized", "keywords"] = "personalized"
    top_n: int = Field(default=5, ge=1, le=20)


@app.get("/api/status")
def status():
    return {"repository_count": len(app.state.matcher.repos)}


@app.post("/api/search")
def search(request: SearchRequest):
    results = app.state.matcher.recommend(
        request.query,
        request.skills,
        top_n=request.top_n,
        bm25_only=request.mode == "keywords",
    )
    # Do not present zero-signal padding as a match
    results = [result for result in results if result["reasons"]]
    return {
        "results": results,
        "repository_count": len(app.state.matcher.repos),
        "query": request.query,
        "mode": request.mode,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
