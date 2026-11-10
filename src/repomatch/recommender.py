
"""RepoMatch: recommend GitHub projects using search relevance and user skills."""
import json
import re
from pathlib import Path

from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def words(s):
    return re.findall(r"[a-z0-9][a-z0-9.+#_-]*", s.lower())


def unwrap(x):
    if isinstance(x, dict) and "status" in x and "data" in x:
        x = x["data"]

    if x is None:
        return ""

    return x if isinstance(x, str) else json.dumps(x)


def prepare(r):
    m = r.get("metadata") or {}
    if not isinstance(m, dict):
        m = {}

    name = r.get("full_name") or m.get("full_name") or r.get("name") or "unknown"
    language = m.get("language") or r.get("language") or ""
    topics = m.get("topics") or r.get("topics") or []

    if not isinstance(topics, list):
        topics = []

    field = r.get("languages") or {}
    extra = field.get("data", {}) if isinstance(field, dict) else {}
    languages = set(extra) if isinstance(extra, dict) else set()

    if language:
        languages.add(language)

    dependencies = set()
    manifests = r.get("manifests") or {}
    entries = manifests.get("data", []) if isinstance(manifests, dict) else manifests

    for entry in entries if isinstance(entries, list) else []:
        if not isinstance(entry, dict):
            continue

        data = entry.get("data", {})
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except ValueError:
                continue

        if isinstance(data, dict):

            for key in ("dependencies", "devDependencies", "peerDependencies",
                        "optionalDependencies", "require", "require-dev"):
                
                if isinstance(data.get(key), dict):
                    dependencies.update(data[key])

    skills = {
        s.strip().lower().replace("_", "-")
        for s in languages | set(map(str, topics)) | dependencies
    }

    description = unwrap(m.get("description") or r.get("description"))

    content = " ".join([
        str(name).replace("/", " "),
        description,
        " ".join(map(str, topics)),
        " ".join(sorted(languages)),
        unwrap(r.get("readme"))[:5000],
        unwrap(r.get("contributing"))[:1000]
    ])

    return {
        "id": r.get("id"),
        "name": name,
        "url": m.get("html_url") or r.get("html_url") or f"https://github.com/{name}",
        "language": language,
        "description": description,
        "skills": skills,
        "text": content
    }


def load_repositories(path):
    repos = []
    seen = set()

    with Path(path).open(encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue

            repo = prepare(json.loads(line))
            if repo["name"] not in seen:
                repos.append(repo)
                seen.add(repo["name"])

    if not repos:
        raise ValueError("No repositories found in dataset")

    return repos


class RepoMatch:
    def __init__(self, repos):
        if not repos:
            raise ValueError("At least one repository is required")

        self.repos = repos
        self.bm25 = BM25Okapi([words(repo["text"]) or [""] for repo in repos])
        self.vectorizer = TfidfVectorizer(tokenizer=words, token_pattern=None)
        self.vectors = self.vectorizer.fit_transform([repo["text"] for repo in repos])

    def recommend(
        self, query, skills=None, top_n=5, candidates=30, *,
        bm25_only=False, use_tfidf=True,
    ):
        if not query.strip():
            raise ValueError("Query cannot be empty")
        if top_n < 1 or candidates < 1:
            raise ValueError("top_n and candidates must be positive")

        if bm25_only:
            skills = ()
        user_skills = {
            skill.strip().lower().replace("_", "-")
            for skill in (skills or ())
            if skill.strip()
        }

        scores = self.bm25.get_scores(words(query))
        candidate_ids = sorted(
            range(len(self.repos)),
            key=lambda i: (-scores[i], self.repos[i]["name"])
        )[:candidates]

        highest = float(scores[candidate_ids[0]])
        query_vector = None
        if use_tfidf and not bm25_only:
            query_vector = self.vectorizer.transform([query])
        results = []
        for i in candidate_ids:
            repo = self.repos[i]
            raw_bm25 = float(scores[i])
            keyword = max(0.0, raw_bm25) / highest if highest > 0 else 0.0
            matched = sorted(user_skills & repo["skills"])
            skill = len(matched) / len(user_skills) if user_skills else 0.0

            tfidf = 0.0
            if query_vector is not None:
                tfidf = float(cosine_similarity(query_vector, self.vectors[i])[0][0])

            total = raw_bm25
            if not bm25_only:
                total = 0.35 * keyword + 0.45 * tfidf + 0.20 * skill

            reasons = []
            if matched:
                reasons.append("matching skills: " + ", ".join(matched))
            if keyword > 0:
                reasons.append("query keyword overlap")
            if tfidf > 0:
                reasons.append("TF-IDF text similarity")
            results.append({
                "name": repo["name"],
                "url": repo["url"],
                "language": repo["language"],
                "description": repo["description"],
                "score": round(total, 4),
                "bm25": round(keyword, 4),
                "semantic": round(tfidf, 4),
                "skill_match": round(skill, 4),
                "reasons": reasons
            })

        if not bm25_only:
            results.sort(key=lambda result: (-result["score"], result["name"]))
        return results[:top_n]
