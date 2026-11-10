"""Pool recommendations for blind judging or score saved judgments."""
import argparse
import json
import math
from pathlib import Path

from repomatch.recommender import RepoMatch, load_repositories


TOP = 10
CANDIDATES = 30
# Each variant sets three flags in order: BM25 only, use TF-IDF, use skills
VARIANTS = {
    "bm25": (True, False, False),
    "bm25+tfidf": (False, True, False),
    "bm25+skills": (False, False, True),
    "checkpoint2": (False, True, True),
}


def evaluate_case(matcher, case, repo_ids):
    rankings = {}
    for name, (bm25_only, use_tfidf, use_skills) in VARIANTS.items():
        rankings[name] = matcher.recommend(
            case["query"],
            case["skills"] if use_skills else (),
            top_n=TOP,
            candidates=CANDIDATES,
            bm25_only=bm25_only,
            use_tfidf=use_tfidf,
        )

    # Judge each repository once even when multiple variants retrieve it
    pool = {
        repo_ids[result["name"]]: result
        for ranking in rankings.values()
        for result in ranking
    }
    return rankings, pool


def dcg(grades):
    # Reward higher relevance grades more and discount results farther down the list
    return sum(
        (2 ** grade - 1) / math.log2(rank + 2)
        for rank, grade in enumerate(grades)
    )


def score_case(case, rankings, pool, repo_ids, judgments, matcher):
    grades = {int(repo_id): grade for repo_id, grade in judgments.items()}
    if any(grade not in (0, 1, 2) for grade in grades.values()):
        raise ValueError(f"{case['id']} has grades outside 0, 1, or 2")
    missing = pool.keys() - grades.keys()
    if missing:
        raise ValueError(f"{case['id']} needs judgments for repo IDs {sorted(missing)}")

    # Compare each ranking with the best ordering of the saved grades
    ideal = dcg(sorted(grades.values(), reverse=True)[:TOP])
    result = {"pool_size": len(pool)}
    if ideal:
        result["ndcg@10"] = {
            name: dcg(grades[repo_ids[repo["name"]]] for repo in ranking) / ideal
            for name, ranking in rankings.items()
        }

    # Check which known matches reach the candidate list before reranking
    known = set(case.get("known_relevant", []))
    if known:
        candidates = matcher.recommend(
            case["query"], top_n=CANDIDATES, candidates=CANDIDATES, bm25_only=True
        )
        retrieved = {repo_ids[repo["name"]] for repo in candidates}
        result["known_relevant_found"] = len(known & retrieved)
        result["known_relevant_missed"] = sorted(known - retrieved)
        result["known_relevant_total"] = len(known)

    if case.get("expect_no_match"):
        result["no_match"] = {
            name: {
                "returned": len(ranking),
                "irrelevant": sum(grades[repo_ids[repo["name"]]] == 0 for repo in ranking),
                "first_result": ranking[0]["name"] if ranking else None,
            }
            for name, ranking in rankings.items()
        }

    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("pool", "score"))
    parser.add_argument("--dataset", type=Path, default=Path("data/snapshots/checkpoint1/repos.jsonl"))
    parser.add_argument("--cases", type=Path, default=Path("evaluation/cases.json"))
    parser.add_argument("--judgments", type=Path, default=Path("evaluation/judgments.json"))
    args = parser.parse_args()

    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    repos = load_repositories(args.dataset)
    repo_ids = {repo["name"]: repo["id"] for repo in repos}
    if None in repo_ids.values() or len(set(repo_ids.values())) != len(repos):
        parser.error("Dataset must have a unique GitHub repository ID for each project")

    matcher = RepoMatch(repos)
    if args.action == "pool":
        for case in cases:
            _, pool = evaluate_case(matcher, case, repo_ids)
            # Show candidates alphabetically and hide their original ranks for blind judging
            projects = [
                {"id": repo_id, "name": repo["name"], "language": repo["language"],
                 "description": repo["description"]}
                for repo_id, repo in sorted(pool.items(), key=lambda item: item[1]["name"].lower())
            ]
            print(json.dumps({"case": case, "projects": projects}))
        return

    judgments = json.loads(args.judgments.read_text(encoding="utf-8"))
    results = {}
    for case in cases:
        rankings, pool = evaluate_case(matcher, case, repo_ids)
        results[case["id"]] = score_case(
            case, rankings, pool, repo_ids, judgments.get(case["id"], {}), matcher
        )

    ranked = [result["ndcg@10"] for result in results.values() if "ndcg@10" in result]
    means = {
        name: round(sum(scores[name] for scores in ranked) / len(ranked), 4)
        for name in VARIANTS
    } if ranked else {}
    print(json.dumps({"judged_cases": len(ranked), "mean_ndcg@10": means, "cases": results}, indent=2))


if __name__ == "__main__":
    main()
