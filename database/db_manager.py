import mysql.connector
import json

class DatabaseManager:

    def __init__(self):
        self.db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="games_manager"
        )

        self.cursor = self.db.cursor()

    def close(self):
        self.db.close()

    def save_match(
            self,
            user_id,
            game_id,
            result,
            score,
            details
    ):
        query = """
        INSERT INTO matches
        (
            user_id,
            game_id,
            result,
            score,
            details
        )
        VALUES
        (%s,%s,%s,%s,%s)
        """

        values = (
            user_id,
            game_id,
            result,
            score,
            json.dumps(details)
        )

        self.cursor.execute(query, values)
        self.db.commit()

    def get_leaderboard(self):

        query = """
        SELECT
            u.username,
            SUM(m.score) AS total_score
        FROM users u
        JOIN matches m
            ON u.id = m.user_id
        GROUP BY u.id
        ORDER BY total_score DESC
        """

        self.cursor.execute(query)

        return self.cursor.fetchall()

    def get_match_history(self, user_id):

        query = """
        SELECT
            g.name,
            m.result,
            m.score,
            m.played_at
        FROM matches m
        JOIN games g
            ON g.id = m.game_id
        WHERE m.user_id = %s
        ORDER BY m.played_at DESC
        """

        self.cursor.execute(query, (user_id,))

        return self.cursor.fetchall()

    def get_games(self):

        query = """
        SELECT id, name
        FROM games
        WHERE is_active = TRUE
        """

        self.cursor.execute(query)

        return self.cursor.fetchall()

    def add_favorite(self, user_id, game_id):

        query = """
        INSERT INTO favorites
        (
            user_id,
            game_id
        )
        VALUES
        (%s,%s)
        """

        self.cursor.execute(
            query,
            (user_id, game_id)
        )

        self.db.commit()

    def set_quickstart(
            self,
            user_id,
            game_id
    ):

        self.cursor.execute(
            """
            UPDATE favorites
            SET is_quickstart = FALSE
            WHERE user_id = %s
            """,
            (user_id,)
        )

        self.cursor.execute(
            """
            UPDATE favorites
            SET is_quickstart = TRUE
            WHERE user_id = %s
            AND game_id = %s
            """,
            (user_id, game_id)
        )

        self.db.commit()

    def create_user(
            self,
            username,
            password_hash
    ):

        try:

            query = """
            INSERT INTO users
            (
                username,
                password_hash
            )
            VALUES
            (%s,%s)
            """

            self.cursor.execute(
                query,
                (username, password_hash)
            )

            self.db.commit()
            return True

        except:
                return False

    def get_user_by_name(
            self,
            username
    ):

        query = """
        SELECT *
        FROM users
        WHERE username = %s
        """

        self.cursor.execute(
            query,
            (username,)
        )

        row = self.cursor.fetchone()

        if row is None:
            return None

        return {
            "id": row[0],
            "username": row[1],
            "password_hash": row[2],
            "created_at": row[3]
        }

    def add_favorite(self, user_id, game_id):

        query = """
        INSERT INTO favorites
        (
            user_id,
            game_id
        )
        VALUES
        (%s, %s)
        """

        try:
            self.cursor.execute(
                query,
                (user_id, game_id)
            )

            self.db.commit()

            print("Game added to favorites.")

        except:
            print("Game already in favorites.")

    def remove_favorite(self, user_id, game_id):

        query = """
        DELETE FROM favorites
        WHERE user_id = %s
        AND game_id = %s
        """

        self.cursor.execute(
            query,
            (user_id, game_id)
        )

        self.db.commit()

    def get_favorites(self, user_id):

        query = """
        SELECT
            g.id,
            g.name,
            f.is_quickstart
        FROM favorites f
        JOIN games g
            ON g.id = f.game_id
        WHERE f.user_id = %s
        """

        self.cursor.execute(query, (user_id,))

        return self.cursor.fetchall()

    def set_quickstart(self, user_id, game_id):

        self.cursor.execute(
            """
            UPDATE favorites
            SET is_quickstart = FALSE
            WHERE user_id = %s
            """,
            (user_id,)
        )

        self.cursor.execute(
            """
            UPDATE favorites
            SET is_quickstart = TRUE
            WHERE user_id = %s
            AND game_id = %s
            """,
            (user_id, game_id)
        )

        self.db.commit()

    def get_quickstart(self, user_id):

        query = """
        SELECT
            g.id,
            g.name
        FROM favorites f
        JOIN games g
            ON g.id = f.game_id
        WHERE f.user_id = %s
        AND f.is_quickstart = TRUE
        """

        self.cursor.execute(query, (user_id,))

        return self.cursor.fetchone()

    def remove_favorite(self, user_id, game_id):

        query = """
        DELETE FROM favorites
        WHERE user_id = %s
        AND game_id = %s
        """

        self.cursor.execute(
            query,
            (user_id, game_id)
        )

        self.db.commit()

    def get_match_history(self, user_id):

        query = """
        SELECT
            g.name,
            m.result,
            m.score,
            m.played_at
        FROM matches m
        JOIN games g
            ON g.id = m.game_id
        WHERE m.user_id = %s
        ORDER BY m.played_at DESC
        """

        self.cursor.execute(
            query,
            (user_id,)
        )

        return self.cursor.fetchall()

    def get_leaderboard(self):

        query = """
        SELECT
            u.username,
            SUM(m.score) AS total_score
        FROM users u
        JOIN matches m
            ON u.id = m.user_id
        GROUP BY u.id
        ORDER BY total_score DESC
        LIMIT 10
        """

        self.cursor.execute(query)

        return self.cursor.fetchall()