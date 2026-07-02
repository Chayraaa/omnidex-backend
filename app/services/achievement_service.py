from app.domain_models.user_achievements import UserAchievement
from app.repositories.interfaces.storage.achievement_repo_protocol import AchievementRepoProtocol
from app.repositories.interfaces.storage.user_achievements_repo_protocol import UserAchievementRepoProtocol
from app.domain_models.achievement import Achievement
from app.repositories.interfaces.storage.card_repo_protocol import CardRepoProtocol
from app.domain_models.user import User


class AchievementService:
    def __init__(self, user_achievement_repo: UserAchievementRepoProtocol, achievement_repo: AchievementRepoProtocol, card_repo: CardRepoProtocol) -> None:
        self.user_achievement_repo = user_achievement_repo
        self.achievement_repo = achievement_repo
        self.card_repo = card_repo

    def get_all_achievements(self) -> list[Achievement]:
        return self.achievement_repo.get_all_achievements()

    def get_current_progress(self, user: User) -> list[UserAchievement]:
        return self.user_achievement_repo.get_current_progress(user)

    def ensure_user_achievements(self, user: User):
        achievements = self.achievement_repo.get_all_achievements()
        existing = self.user_achievement_repo.get_current_progress(user)

        existing_ids = {a.achievement_id for a in existing}
        for achievement in achievements:
            if achievement.id not in existing_ids:
                self.user_achievement_repo.create_user_achievement(
                    user_id=user.id,
                    achievement_id=achievement.id,
                    currentProgress=0,
                    isDone=False
                )

    def process_card_created(self, user_id: int):
        achievements = self.achievement_repo.get_all_achievements()

        for achievement in achievements:
            progress = self._calculate_progress(user_id, achievement)

            done = progress >= achievement.required

            self.user_achievement_repo.update_progress(user_id, achievement, progress, done)

    def _calculate_progress(self, user_id: int, achievement: Achievement,) -> int:

        match achievement.id:

            case 1:
                # First Step -> 1 Karte insgesamt
                return self.card_repo.count_cards(user_id)

            case 2:
                # Touch Grass -> 10 Pflanzen
                return self.card_repo.count_cards_by_category(user_id, "pflanzen")

            case 3:
                # Darf man das streicheln -> 10 Tiere
                return self.card_repo.count_cards_by_category(user_id, "tiere")

            case 4:
                # Spider-Man -> 10 Insekten
                return self.card_repo.count_cards_by_category(user_id, "insekten")

            case 5:
                # Du bist nicht du, wenn du hungrig bist -> 10 Nahrung
                return self.card_repo.count_cards_by_category(user_id, "nahrung")

            case 6:
                # Science! -> 10 Technik
                return self.card_repo.count_cards_by_category(user_id, "technik")

            case 7:
                # Tüftler -> 10 Mechanik
                return self.card_repo.count_cards_by_category(user_id, "mechanik")

            case 8:
                # Es ist kein Brocken, es ist ein Fels -> 10 Gestein
                return self.card_repo.count_cards_by_category(user_id, "gestein")

            case 9:
                # Was bist du -> 10 Unbekannt
                return self.card_repo.count_cards_by_category(user_id, "unbekannt")

            case 10:
                # Gerümpel -> 10 Gegenstände
                return self.card_repo.count_cards_by_category(user_id, "gegenstände")

            case 11:
                # Gonna catch 'em all -> 100 Karten insgesamt
                return self.card_repo.count_cards(user_id)

            case _:
                return 0