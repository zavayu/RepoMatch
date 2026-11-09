
"""Run RepoMatch with user input."""
from repomatch.recommender import RepoMatch, load_repositories

repos = load_repositories("data/repositories.jsonl")
matcher = RepoMatch(repos)

while True:
    print("\n=== RepoMatch ===")

    query = input("What kind of project are you looking for? ").strip()

    if not query:
        print("Please enter a search query.")
        continue

    skills = input("Enter your skills (comma-separated): ")
    skills = [s.strip() for s in skills.split(",") if s.strip()]

    print("\nFinding recommendations...\n")

    results = matcher.recommend(query, skills)

    for i, result in enumerate(results, 1):
        print(f"{i}. {result['name']} | Score: {result['score']}")
        print(f"   {result['url']}")
        print(f"   Why: {', '.join(result['reasons'])}\n")

    again = input("Search again? (y/n): ").strip().lower()

    if again != "y":
        print("Thanks for using RepoMatch!")
        break