from app.extensions import db
from sqlalchemy import text
import select
import psycopg2
import os
import logging

logger = logging.getLogger(__name__)

class EventPublisher:
    def publish(self, game_id: int):
        # Postgres NOTIFY payload limit is 8000 bytes.
        # We notify that the game state has changed.
        # The listener will fetch the latest state from the database.
        logger.debug(f"[SSE] publish: sending NOTIFY for game {game_id}")
        db.session.execute(text(f"NOTIFY card_battle_{game_id}"))
        # MUST commit here: PostgreSQL only delivers NOTIFY when the transaction
        # commits. Without this commit the notification is silently dropped when
        # Flask-SQLAlchemy rolls back / removes the session at request teardown.
        db.session.commit()
        logger.debug(f"[SSE] publish: NOTIFY committed for game {game_id}")

    def listen(self, game_id: int):
        # This should be called in a generator for SSE.
        # Connect directly via psycopg2 (bypassing SQLAlchemy pool) so that
        # long-lived SSE streams do not hold pool connections and exhaust them.
        dsn = os.environ.get("SQLALCHEMY_DATABASE_URI", "postgresql://user:password@localhost:5432/mydb")
        connection = psycopg2.connect(dsn)
        logger.debug(f"[SSE] listen: new SSE connection opened for game {game_id}")
        try:
            connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = connection.cursor()
            cursor.execute(f"LISTEN card_battle_{game_id};")

            # Initial yield to confirm connection
            logger.debug(f"[SSE] listen: sending initial state for game {game_id}")
            yield "initial"

            while True:
                # Wait for notifications with a timeout for keep-alive
                ready = select.select([connection], [], [], 20)
                if ready == ([], [], []):
                    logger.debug(f"[SSE] listen: keep-alive ping for game {game_id}")
                    yield "keep-alive"
                else:
                    connection.poll()
                    notif_count = len(connection.notifies)
                    logger.debug(f"[SSE] listen: received {notif_count} notification(s) for game {game_id}")
                    while connection.notifies:
                        connection.notifies.pop(0)
                        yield "update"
        except GeneratorExit:
            logger.debug(f"[SSE] listen: client disconnected from game {game_id}")
        except Exception as e:
            logger.warning(f"[SSE] listen: error in SSE stream for game {game_id}: {e}")
        finally:
            logger.debug(f"[SSE] listen: closing SSE connection for game {game_id}")
            connection.close()

game_event_publisher = EventPublisher()
