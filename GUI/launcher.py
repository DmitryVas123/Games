import customtkinter
from PIL import Image
import os
from GUI.games.numguess_window import NumberGuessWindow
from GUI.games.rps_window import RockPaperScissorsWindow
from GUI.games.tanks_window import TanksWindow

#TODO: Connect the tanks game to the database and implement the result handling in the GameLauncher class.
class LeaderboardWindow(customtkinter.CTkToplevel):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        
        self.title("Leaderboard")
        self.geometry("500x600")
        self.resizable(False, False)
        self.configure(fg_color="#1B2838")
        self.transient(parent)
        self.grab_set()

        customtkinter.CTkLabel(self, text="LEADERBOARD", font=customtkinter.CTkFont(size=24, weight="bold")).pack(pady=20)

        scrollable_frame = customtkinter.CTkScrollableFrame(self, fg_color="#2B2D30", corner_radius=15)
        scrollable_frame.pack(pady=10, padx=20, fill="both", expand=True)

        leaderboard_data = self.db.get_leaderboard()

        if not leaderboard_data:
            customtkinter.CTkLabel(scrollable_frame, text="No data available yet.", font=customtkinter.CTkFont(size=16)).pack(pady=20)
        else:
            for i, (username, score) in enumerate(leaderboard_data, start=1):
                entry_frame = customtkinter.CTkFrame(scrollable_frame, fg_color="transparent")
                entry_frame.pack(fill="x", pady=5, padx=10)
                entry_frame.grid_columnconfigure(1, weight=1)
                
                pos_text = f"#{i}"
                customtkinter.CTkLabel(entry_frame, text=pos_text, font=customtkinter.CTkFont(size=18, weight="bold"), width=50).grid(row=0, column=0, sticky="w")
                customtkinter.CTkLabel(entry_frame, text=username, font=customtkinter.CTkFont(size=18)).grid(row=0, column=1, sticky="w")
                customtkinter.CTkLabel(entry_frame, text=f"{score} pts", font=customtkinter.CTkFont(size=18, weight="bold"), text_color="#5DADE2").grid(row=0, column=2, sticky="e")


class HistoryWindow(customtkinter.CTkToplevel):
    def __init__(self, parent, db, user_id):
        super().__init__(parent)
        self.db = db
        self.user_id = user_id

        self.title("Match History")
        self.geometry("700x600")
        self.resizable(False, False)
        self.configure(fg_color="#1B2838")
        self.transient(parent)
        self.grab_set()

        customtkinter.CTkLabel(self, text="MATCH HISTORY", font=customtkinter.CTkFont(size=24, weight="bold")).pack(pady=20)

        scrollable_frame = customtkinter.CTkScrollableFrame(self, fg_color="#2B2D30", corner_radius=15)
        scrollable_frame.pack(pady=10, padx=20, fill="both", expand=True)

        history_data = self.db.get_match_history(self.user_id)

        if not history_data:
            customtkinter.CTkLabel(scrollable_frame, text="No matches played yet.", font=customtkinter.CTkFont(size=16)).pack(pady=20)
        else:
            for game, result, score, played_at in history_data:
                entry_frame = customtkinter.CTkFrame(scrollable_frame, fg_color="transparent", border_width=1, border_color="#3E454D", corner_radius=10)
                entry_frame.pack(fill="x", pady=8, padx=10)
                
                color = "#4ADE80" if result == "win" else "#FF6B6B"
                
                customtkinter.CTkLabel(entry_frame, text=game, font=customtkinter.CTkFont(size=16, weight="bold")).pack(pady=(10,0))
                customtkinter.CTkLabel(entry_frame, text=result.upper(), font=customtkinter.CTkFont(size=18, weight="bold"), text_color=color).pack()
                customtkinter.CTkLabel(entry_frame, text=f"Score: {score} points", font=customtkinter.CTkFont(size=14)).pack()
                customtkinter.CTkLabel(entry_frame, text=played_at, font=customtkinter.CTkFont(size=12), text_color="gray60").pack(pady=(0,10))


class FavoritesWindow(customtkinter.CTkToplevel):
    def __init__(self, parent, db, user_id):
        super().__init__(parent)
        self.db = db
        self.user_id = user_id

        self.title("Favorites & Quickstart")
        self.geometry("500x400")
        self.resizable(False, False)
        self.configure(fg_color="#1B2838")
        self.transient(parent)
        self.grab_set()
        
        customtkinter.CTkLabel(self, text="FAVORITES", font=customtkinter.CTkFont(size=24, weight="bold")).pack(pady=20)
        
        self.frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.frame.grid_columnconfigure(0, weight=1)
        
        self.refresh_favorites_list()

    def refresh_favorites_list(self):
        # Clear existing widgets
        for widget in self.frame.winfo_children():
            widget.destroy()
            
        favorites = self.db.get_favorites(self.user_id)
        
        customtkinter.CTkLabel(self.frame, text="Current Favorites:", font=customtkinter.CTkFont(size=16)).grid(row=0, column=0, sticky="w", pady=(0,10))
        
        if not favorites:
            customtkinter.CTkLabel(self.frame, text="No favorite games yet.").grid(row=1, column=0, sticky="w")
        else:
            self.quickstart_var = customtkinter.StringVar()
            for i, (game_id, game_name, is_quickstart) in enumerate(favorites):
                marker = " [QUICKSTART]" if is_quickstart else ""
                fav_label = customtkinter.CTkLabel(self.frame, text=f"• {game_name}{marker}", font=customtkinter.CTkFont(size=15))
                fav_label.grid(row=i+1, column=0, sticky="w", padx=10)
                
                # Radio button to set quickstart
                radio_btn = customtkinter.CTkRadioButton(self.frame, text="", variable=self.quickstart_var, value=str(game_id))
                radio_btn.grid(row=i+1, column=1, sticky="e")
                if is_quickstart:
                    radio_btn.select()

        # Add buttons
        add_frame = customtkinter.CTkFrame(self.frame, fg_color="transparent")
        add_frame.grid(row=len(favorites)+2, column=0, columnspan=2, pady=20, sticky="ew")
        add_frame.grid_columnconfigure((0,1), weight=1)
        
        customtkinter.CTkButton(add_frame, text="Add Number Guess", command=lambda: self.add_fav(1)).grid(row=0, column=0, padx=5)
        customtkinter.CTkButton(add_frame, text="Add Rock Paper Scissors", command=lambda: self.add_fav(2)).grid(row=0, column=1, padx=5)
        
        customtkinter.CTkButton(self.frame, text="Set Quickstart", command=self.set_quickstart).grid(row=len(favorites)+3, column=0, columnspan=2, pady=10, sticky="ew")

    def add_fav(self, game_id):
        self.db.add_favorite(self.user_id, game_id)
        self.refresh_favorites_list()

    def set_quickstart(self):
        game_id_str = self.quickstart_var.get()
        if game_id_str:
            self.db.set_quickstart(self.user_id, int(game_id_str))
            self.refresh_favorites_list()


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
        
        # Ensure this window stays on top
        self.transient(parent)
        self.grab_set()

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

        print("Tanks match finished:")
        print(result)

        # Future database code:
        #
        # self.db.save_match(
        #     user_id=self.user_id,
        #     game_id=3,
        #     result=result["result"],
        #     score=result["score"],
        #     details=result["details"]
        # )

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
