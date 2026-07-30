from app.extensions import db
from sqlalchemy import text
import select
import psycopg2

class EventPublisher:
    def publish(self, game_id: int):
        # Postgres NOTIFY payload limit is 8000 bytes.
        # We notify that the game state has changed.
        # The listener will fetch the latest state from the database.
        db.session.execute(text(f"NOTIFY card_battle_{game_id}"))
        # No commit here; we assume the caller will commit or it will be committed at the end of the request.

    def listen(self, game_id: int):
        # This should be called in a generator for SSE
        engine = db.engine
        # Use raw connection for LISTEN
        connection = engine.raw_connection()
        try:
            connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = connection.cursor()
            cursor.execute(f"LISTEN card_battle_{game_id};")
            
            # Initial yield to confirm connection
            yield "initial"
            
            while True:
                # Wait for notifications with a timeout for keep-alive
                if select.select([connection], [], [], 20) == ([], [], []):
                    yield "keep-alive"
                else:
                    connection.poll()
                    while connection.notifies:
                        connection.notifies.pop(0)
                        yield "update"
        except GeneratorExit:
            pass
        except Exception:
            # Handle potential connection issues
            pass
        finally:
            connection.close()

game_event_publisher = EventPublisher()
