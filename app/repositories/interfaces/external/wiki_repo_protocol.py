from typing import Protocol

class WikiRepoProtocol(Protocol):

    def get_article_summary(self, title: str) -> str: ...
