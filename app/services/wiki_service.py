from app.repositories.interfaces.external.wiki_repo_protocol import WikiRepoProtocol

class WikiService:
    def __init__(self, wiki_repo: WikiRepoProtocol):
        self.wiki_repo = wiki_repo

    def get_summary(self, article_title: str) -> str:
        return self.wiki_repo.get_article_summary(article_title)