import os
import sys
from dotenv import load_dotenv

# Add the current directory to sys.path so we can import from 'app'
sys.path.append(os.getcwd())

# Load .env file at root
load_dotenv()

# Set environment variables for the script if not already set
if "SQLALCHEMY_DATABASE_URI" not in os.environ:
    os.environ["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:postgres@localhost:5432/omnidex"
os.environ["SKIP_SERVICES"] = "1"

from app import create_app, db
from app.database_models.card_model import CardModel
from app.services.card_stats_service import CardStatsService
from app.repositories.external.openai_card_stats_api_client import OpenAICardStatsApiClient

def main():
    app = create_app()
    with app.app_context():
        print(f"Connected to database: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        # Manually setup the classification service
        try:
            adapter = OpenAICardStatsApiClient()
            service = CardStatsService(adapter)
        except ValueError as e:
            print(f"Error initializing OpenAI client: {e}")
            print("Make sure AI_BASE_URL and AI_API_KEY are set.")
            return

        cards = CardModel.query.all()
        print(f"Found {len(cards)} cards to classify.")
        
        count = 0
        for card in cards:
            print(f"[{count+1}/{len(cards)}] Classifying card: {card.name} (ID: {card.id})")
            try:
                stats = service.classify_card(card.name, card.description or "")
                
                card.battle_type = stats["battle_type"].value if hasattr(stats["battle_type"], "value") else stats["battle_type"]
                card.attack = stats["attack"]
                card.health = stats["health"]
                card.cost = stats["cost"]
                
                print(f"  Result: {card.battle_type}, ATK: {card.attack}, HP: {card.health}, COST: {card.cost}")
                
                # Commit every card to avoid losing progress on error
                db.session.commit()
                count += 1
            except Exception as e:
                print(f"  Failed to classify card {card.id}: {e}")
                db.session.rollback()
        
        print(f"Successfully processed {count} cards.")

if __name__ == "__main__":
    main()
