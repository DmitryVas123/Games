import bcrypt


class UserManager:

    def __init__(self, db):
        self.db = db
        self.current_user = None

    def register(self):

        username = input("Username: ")
        password = input("Password: ")

        password_hash = bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt()
        ).decode()

        success = self.db.create_user(
            username,
            password_hash
        )

        if success:
            print("User registered.")
        else:
            print("Username already exists.")

    def login(self):
        username = input("Username: ")
        password = input("Password: ")

        user = self.db.get_user_by_name(username)

        if user is None:
            print("User not found.")
            return False
        
        if bcrypt.checkpw(
            password.encode(),
            user["password_hash"].encode()
            ):
            self.current_user = user

        print(
        f"Welcome {user['username']}!"
        )
        return True

    def logout(self):
        self.current_user = None
        print("Logged out.")

    def is_logged_in(self): return self.current_user is not None

    def login_gui(
        self,
        username,
        password
    ):

        user = self.db.get_user_by_name(
            username
        )

        if not user:
            return None

        if bcrypt.checkpw(
            password.encode(),
            user["password_hash"].encode()
        ):

            self.current_user = user

            return user

        return None

    def register_gui(self, username, password):
        """
        Handles registration from the GUI.
        Returns a tuple: (success_boolean, message_string).
        """
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        success = self.db.create_user(username, password_hash)

        if success:
            return True, "Registration successful! You may now log in."
        else:
            return False, "Username already exists."

    def login_gui(self, username, password):
        """Handles login from the GUI."""
        user = self.db.get_user_by_name(username)
        if not user:
            return None

        if bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            self.current_user = user
            return user
        return None

