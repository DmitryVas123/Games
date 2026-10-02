import customtkinter
from PIL import Image
import os
from GUI.games.numguess_window import NumberGuessWindow
from GUI.games.rps_window import RockPaperScissorsWindow
from GUI.games.tanks_window import TanksWindow
from GUI.windows.leaderboard import LeaderboardWindow
from GUI.windows.history import HistoryWindow
from GUI.windows.favorites import FavoritesWindow


class GameLauncher(customtkinter.CTkToplevel): 
    def __init__(self, parent, on_logout, username, user_id, db):
        super().__init__()
        
        self.on_logout = on_logout
        self.username = username
        self.user_id = user_id
        self.db = db

        self.title("Games With Bot")
        self.geometry("1280x720")
        self.resizable(False, False)
        # Note: A CTkToplevel does not have its own fg_color. It's transparent
        # and shows the color of the root window behind it.
        # self.configure(fg_color="#1B2838") # This line is not needed for a Toplevel

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.icons = self.load_icons()
        self.create_sidebar()
        self.create_main_content_area()
        
        self.transient(parent)
        self.grab_set()

        self.protocol(
            "WM_DELETE_WINDOW",
            self.close_launcher
        )

    def close_launcher(self):

        self.destroy()
        self.master.destroy()

    def load_icons(self):
        icons = {}
        icon_paths = {
            "numguess_large": ("./GUI/assets/games/numguess.png", (128, 128)),
            "rps_large": ("./GUI/assets/games/rps.png", (128, 128)),
            "trophy": ("./GUI/assets/icons/trophy.png", (28, 28)),
            "history": ("./GUI/assets/icons/history.png", (28, 28)),
            "favorite": ("./GUI/assets/icons/favorites.png", (28, 28)),
            "logout": ("./GUI/assets/icons/logout.png", (24, 24)),
            "tanks_large": ("./GUI/assets/games/tanks.png", (128, 128))
        }
        for name, (path, size) in icon_paths.items():
            if os.path.exists(path):
                img = Image.open(path).convert("RGBA")
                icons[name] = customtkinter.CTkImage(light_image=img, dark_image=img, size=size)
            else:
                icons[name] = None
        return icons

    def create_sidebar(self):
        sidebar_frame = customtkinter.CTkFrame(self, width=240, corner_radius=0, fg_color="#212325")
        sidebar_frame.grid(row=0, column=0, sticky="nsw")
        sidebar_frame.grid_rowconfigure(5, weight=1)
        customtkinter.CTkLabel(sidebar_frame, text="GAMES WITH BOT", font=customtkinter.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=(30, 20))
        customtkinter.CTkLabel(sidebar_frame, text=f"Welcome, {self.username}", font=customtkinter.CTkFont(size=14), anchor="w").grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        # --- Connect button commands to new methods ---
        customtkinter.CTkButton(sidebar_frame, image=self.icons.get("trophy"), text="Leaderboard", command=self.open_leaderboard, **self.sidebar_button_styles()).grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        customtkinter.CTkButton(sidebar_frame, image=self.icons.get("history"), text="History", command=self.open_history, **self.sidebar_button_styles()).grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        customtkinter.CTkButton(sidebar_frame, image=self.icons.get("favorite"), text="Favorites", command=self.open_favorites, **self.sidebar_button_styles()).grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        customtkinter.CTkButton(sidebar_frame, image=self.icons.get("logout"), text="Logout", command=self.logout, **self.sidebar_button_styles()).grid(row=6, column=0, padx=20, pady=(10, 20), sticky="sew")
        
    def sidebar_button_styles(self):
        """Returns a dictionary of common styles for sidebar buttons."""
        return {"font": customtkinter.CTkFont(size=16), "fg_color": "transparent", "hover_color": "#33373a", "compound": "left", "anchor": "w", "height": 40}

    def create_main_content_area(self):
        main_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=0, column=1, sticky="nsew", padx=50, pady=30)
        main_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="games")
        main_frame.grid_rowconfigure(1, weight=1)
        customtkinter.CTkLabel(main_frame, text="MY GAMES", font=customtkinter.CTkFont(size=28, weight="bold"), anchor="w").grid(row=0, column=0, columnspan=3, pady=(0, 30), sticky="ew")
        self.create_game_card(main_frame, self.icons.get("numguess_large"), "Number Guess", self.open_numguess).grid(row=1, column=0, padx=(0, 25), sticky="nsew")
        self.create_game_card(main_frame, self.icons.get("rps_large"), "Rock Paper Scissors", self.open_rps).grid(row=1, column=1, padx=(25, 0), sticky="nsew")
        self.create_game_card(main_frame, self.icons.get("tanks_large"), "Tanks", self.open_tanks).grid(row=1, column=2, padx=(25, 0), sticky="nsew")
        
    def create_game_card(self, parent, icon, title, command):
        card = customtkinter.CTkFrame(parent, fg_color="#2B2D30", corner_radius=20, border_width=1, border_color="#3E454D")
        card.grid_rowconfigure(0, weight=2); card.grid_rowconfigure(1, weight=1); card.grid_rowconfigure(2, weight=0); card.grid_columnconfigure(0, weight=1)
        customtkinter.CTkLabel(card, image=icon, text="", fg_color="transparent").grid(row=0, column=0, pady=(20, 10), sticky="s")
        customtkinter.CTkLabel(card, text=title, font=customtkinter.CTkFont(size=22, weight="bold")).grid(row=1, column=0, pady=10, sticky="n")
        customtkinter.CTkButton(card, text="PLAY ▶", font=customtkinter.CTkFont(size=18, weight="bold"), height=50, corner_radius=10, command=command).grid(row=2, column=0, pady=20, padx=30, sticky="s")
        return card

    # --- Game Launchers and Handlers ---
    def open_numguess(self):
        self.withdraw()
        NumberGuessWindow(parent=self, username=self.username, on_match_finished=self.handle_numguess_result)

    def handle_numguess_result(self, result):
        self.db.save_match(user_id=self.user_id, game_id=1, result=result["result"], score=result["score"], details=result["details"])
        self.deiconify(); self.lift()

    def open_rps(self):
        self.withdraw()
        RockPaperScissorsWindow(parent=self, username=self.username, on_match_finished=self.handle_rps_result)

    def open_tanks(self):
        self.withdraw()
        TanksWindow(
            username=self.username,
            on_match_finished=self.handle_tanks_result
        ).run()

    def handle_rps_result(self, result):
        score = result.get("score", 0) 
        self.db.save_match(user_id=self.user_id, game_id=2, result=result["result"], score=score, details=result["details"])
        self.deiconify(); self.lift()

    def handle_tanks_result(self, result):

        if result is None:
            self.deiconify()
            self.lift()
            self.focus_force()
            return
        else:
            print("Tanks match finished:")
            print(result)

            self.db.save_match(
                user_id=self.user_id,
                game_id=3,
                result=result["result"],
                score=result["score"],
                details=result["details"]
            )

            self.deiconify()
            self.lift()
            self.focus_force()


    def open_leaderboard(self):
        LeaderboardWindow(parent=self, db=self.db)
        
    def open_history(self):
        HistoryWindow(parent=self, db=self.db, user_id=self.user_id)
        
    def open_favorites(self):
        FavoritesWindow(parent=self, db=self.db, user_id=self.user_id)
        
    def logout(self):
        self.on_logout()


if __name__ == "__main__":
    class MockDB:
        def get_leaderboard(self): return [("Player1", 150), ("BotSlayer", 95), ("Tester", 50)]
        def get_match_history(self, user_id): return [("Number Guess", "win", 35, "2023-10-27 10:30"), ("Rock Paper Scissors", "lose", 10, "2023-10-27 10:35")]
        def get_favorites(self, user_id): return [(1, "Number Guess", True), (2, "Rock Paper Scissors", False)]
        def add_favorite(self, user_id, game_id): print(f"DB: Adding fav {game_id} for user {user_id}")
        def set_quickstart(self, user_id, game_id): print(f"DB: Setting quickstart to {game_id} for user {user_id}")
        def save_match(self, **kwargs): print(f"DB: Saving match: {kwargs}")

    def show_login_screen():
        print("\n--- LOGOUT SUCCESSFUL ---")
        print("Now showing login screen...")
        mock_app.quit()

    mock_app = GameLauncher(on_logout=show_login_screen, username="Tester", user_id=1, db=MockDB())
    mock_app.mainloop()
