import requests
from urllib.parse import quote
from app.repositories.interfaces.external.wiki_repo_protocol import WikiRepoProtocol

headers = {
    'User-Agent': 'Omnidex/1.0 (https://hof-university.de)'
}


class WikiRepo(WikiRepoProtocol):

    def __init__(self, base_url: str = "https://de.wikipedia.org"):
        self.base_url = base_url.rstrip("/")


    def get_article_summary(self, title: str) -> str:
        if not title or not title.strip():
            return "No article found"

        best_title = self._search_best_title(title)

        if not best_title:
            return "No article found"

        return self._fetch_summary(best_title)


    def _search_best_title(self, query: str) -> str | None:
        try:
            response = requests.get(
                f"{self.base_url}/w/api.php",
                headers=headers,
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "srlimit": 5,
                    "format": "json",
                },
                timeout=5,
            )
        except requests.RequestException:
            return None

        if response.status_code != 200:
            return None

        try:
            data = response.json()
        except ValueError:
            return None

        search_results = data.get("query", {}).get("search", [])
        if not isinstance(search_results, list) or not search_results:
            return None

        query_lower = query.lower()

        best_title = None
        best_score = -1

        for item in search_results:
            if not isinstance(item, dict):
                continue

            title = item.get("title")
            snippet = item.get("snippet", "")

            if not isinstance(title, str):
                continue

            score = 0
            t = title.lower()
            s = snippet.lower()
            q = query_lower

            if t == q:
                score += 100

            if q in t:
                score += 60

            if q in s:
                score += 80

            q_words = set(q.split())
            t_words = set(t.split())
            score += len(q_words & t_words) * 20

            if score > best_score:
                best_score = score
                best_title = title

        return best_title


    def _fetch_summary(self, title: str) -> str:
        safe_title = quote(title.replace(" ", "_"))

        try:
            response = requests.get(
                f"{self.base_url}/api/rest_v1/page/summary/{safe_title}",
                headers=headers,
                timeout=5,
            )
        except requests.RequestException:
            return "No article found"

        if response.status_code == 404:
            return "No article found"

        if response.status_code >= 400:
            return "No article found"

        try:
            data = response.json()
        except ValueError:
            return "No article found"

        extract = data.get("extract")
        if not isinstance(extract, str) or not extract.strip():
            return "No article found"

        return extract.strip()