import requests
from app.repositories.interfaces.external.wiki_repo_protocol import WikiRepoProtocol

headers = {
    'User-Agent': 'Omnidex/1.0 (https://hof-university.de)'
}


class WikiRepo(WikiRepoProtocol):

    def __init__(self, base_url: str = "https://de.wikipedia.org/api/rest_v1"):
        self.base_url = base_url

    def get_article_summary(self, title: str) -> str:
        response = requests.get(f"{self.base_url}/page/summary/{title}", headers=headers)

        if response.status_code == 404:
            return "No article found"

        response.raise_for_status()
        data = response.json()

        return data.get("extract")