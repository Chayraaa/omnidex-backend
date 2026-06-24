from sqlalchemy import or_

from app.database_models.card_model import CardModel
from app.repositories.interfaces.storage.collection_repo_protocol import CollectionRepoProtocol


class SqlCollectionRepo(CollectionRepoProtocol):
    def find_by_user(
        self,
        *,
        user_id: int,
        query: str | None = None,
        sort: str = "newest",
        category: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[CardModel]:
        db_query = CardModel.query.filter(CardModel.user_id == user_id)

        if query:
            pattern = f"%{query.strip()}%"
            db_query = db_query.filter(
                or_(
                    CardModel.name.ilike(pattern),
                    CardModel.card_summary.ilike(pattern),
                    CardModel.description.ilike(pattern),
                )
            )

        if category:
            db_query = db_query.filter(CardModel.category == category)

        if sort == "newest":
            db_query = db_query.order_by(CardModel.created_at.desc(), CardModel.id.desc())
        else:
            db_query = db_query.order_by(CardModel.created_at.asc(), CardModel.id.asc())

        if offset is not None:
            db_query = db_query.offset(offset)
        if limit is not None:
            db_query = db_query.limit(limit)

        return list(db_query.all())

    def find_by_id_for_user(self, *, user_id: int, entry_id: int) -> CardModel | None:
        return (
            CardModel.query.filter(
                CardModel.user_id == user_id,
                CardModel.id == entry_id,
            )
            .limit(1)
            .one_or_none()
        )
