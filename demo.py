"""Run RepoMatch with user input."""
import argparse

from repomatch.recommender import RepoMatch, load_repositories


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset", default="data/repositories.jsonl", help="Path to a repository JSONL file"
    )
    parser.add_argument("--mode", choices=("checkpoint2", "bm25"), default="checkpoint2")
    parser.add_argument("--top", type=int, default=5, help="Maximum number of results")
    parser.add_argument("--debug", action="store_true", help="Show individual ranking scores")
    args = parser.parse_args()
    if args.top < 1:
        parser.error("--top must be positive")

    # Build the search index once and reuse it for every query in this session
    repos = load_repositories(args.dataset)
    matcher = RepoMatch(repos)
    print(f"Loaded {len(repos):,} repositories | Mode: {args.mode}")
    bm25_only = args.mode == "bm25"

    while True:
        print("\n=== RepoMatch ===")
        query = input("What kind of project are you looking for? ").strip()
        if not query:
            print("Please enter a search query.")
            continue

        skills = []
        if not bm25_only:
            skills = input("Enter your skills (comma-separated): ").split(",")

        print("\nFinding recommendations...\n")
        # Keep the usual 30 candidates unless the user asks for more results
        results = matcher.recommend(
            query, skills, top_n=args.top, candidates=max(30, args.top), bm25_only=bm25_only
        )

        for rank, result in enumerate(results, 1):
            print(f"{rank}. {result['name']} | Score: {result['score']}")
            print(f"   {result['url']}")
            reasons = ", ".join(result["reasons"]) or "No matching signals"
            print(f"   Why: {reasons}")
            if args.debug:
                print(
                    f"   BM25 (normalized): {result['bm25']:.4f} | "
                    f"TF-IDF: {result['semantic']:.4f} | Skills: {result['skill_match']:.4f}"
                )
            print()

        if input("Search again? (y/n): ").strip().lower() != "y":
            print("Thanks for using RepoMatch!")
            break


if __name__ == "__main__":
    main()
