import customtkinter
from PIL import Image
import os
from random import choice

#==============================================================================
# 1. GAME LOGIC (Corrected with Score Calculation)
#==============================================================================
class RPSGame:
    def __init__(self):
        # --- ADDED SCORE TRACKING ---
        self.score = 0
        self.score_bot = 0
        self.wins = 0
        self.draws = 0
        self.loses = 0
        self.choices = ["rock", "paper", "scissors"]

    def play_round(self, user_choice):
        bot_choice = choice(self.choices)
        
        # --- ADDED POINT CALCULATION ---
        if user_choice == bot_choice:
            self.draws += 1
            round_result = "draw"
            score_round = 5
            score_round_bot = 5
        elif (
            (user_choice == "rock" and bot_choice == "scissors") or
            (user_choice == "paper" and bot_choice == "rock") or
            (user_choice == "scissors" and bot_choice == "paper")
        ):
            self.wins += 1
            round_result = "win"
            score_round = 10
            score_round_bot = 0
        else:
            self.loses += 1
            round_result = "lose"
            score_round = 0
            score_round_bot = 10
            
        self.score += score_round
        self.score_bot += score_round_bot
        
        return {
            "round_result": round_result,
            "user_choice": user_choice,
            "bot_choice": bot_choice,
            "wins": self.wins, "draws": self.draws, "loses": self.loses,
            "score": self.score, # Include current score in round data
            "finished": self.is_finished()
        }

    def is_finished(self):
        return self.wins >= 3 or self.loses >= 3

    def get_match_result(self):
        result = "win" if self.wins >= 3 else "lose"
        # --- ADDED FINAL SCORE TO RETURN DICTIONARY ---
        return {
            "result": result,
            "score": self.score, # This is the crucial fix
            "details": {"wins": self.wins, "draws": self.draws, "loses": self.loses}
        }

#==============================================================================
# 2. RPS GAME WINDOW (UI Code is unchanged)
#==============================================================================
class RockPaperScissorsWindow(customtkinter.CTkToplevel):
    def __init__(self, parent, username="Player1", on_match_finished=None):
        super().__init__(parent)
        self.parent = parent
        self.username = username
        self.on_match_finished = on_match_finished
        self.game = RPSGame() # Now uses the corrected game class

        # --- Window Setup ---
        self.title("Games With Bot - Rock Paper Scissors")
        self.geometry("1280x720")
        # (The rest of the UI code is exactly the same and correct)
        # ...
        self.resizable(False, False)
        self.configure(fg_color="#1B2838")
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.close_window)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.icons = self.load_assets()
        self.create_sidebar()
        self.create_game_area()

    def load_assets(self):
        icons = {}
        assets = {
            "rps_header": ("./GUI/assets/games/rps.png", (128, 128)),
            "rock": ("./GUI/assets/games/rock.png", (150, 150)),
            "paper": ("./GUI/assets/games/paper.png", (150, 150)),
            "scissors": ("./GUI/assets/games/scissors.png", (150, 150)),
            "logout": ("./GUI/assets/icons/logout.png", (24, 24)),
            "rock_small": ("./GUI/assets/games/rock.png", (100, 100)),
            "paper_small": ("./GUI/assets/games/paper.png", (100, 100)),
            "scissors_small": ("./GUI/assets/games/scissors.png", (100, 100)),
        }
        for name, (path, size) in assets.items():
            if os.path.exists(path):
                image = Image.open(path).convert("RGBA")
                icons[name] = customtkinter.CTkImage(light_image=image, dark_image=image, size=size)
            else:
                icons[name] = None
        return icons

    def create_sidebar(self):
        sidebar = customtkinter.CTkFrame(self, width=240, corner_radius=0, fg_color="#212325")
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(4, weight=1)
        customtkinter.CTkLabel(sidebar, text="GAMES WITH BOT", font=customtkinter.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=(30, 20))
        customtkinter.CTkLabel(sidebar, text=f"Welcome, {self.username}", font=customtkinter.CTkFont(size=14), anchor="w").grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        customtkinter.CTkButton(sidebar, text="← Back to Launcher", height=42, fg_color="transparent", hover_color="#33373A", anchor="w", command=self.close_window).grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        customtkinter.CTkButton(sidebar, text="↻ Restart Game", height=42, fg_color="transparent", hover_color="#33373A", anchor="w", command=self.restart_game).grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        customtkinter.CTkButton(sidebar, text="Close Game", image=self.icons.get("logout"), compound="left", height=42, fg_color="#A93232", hover_color="#842828", command=self.close_window).grid(row=5, column=0, padx=20, pady=20, sticky="ew")

    def create_game_area(self):
        main_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=0, column=1, sticky="nsew", padx=40, pady=24)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)
        header_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        header_frame.grid_columnconfigure(1, weight=1)
        customtkinter.CTkLabel(header_frame, text="", image=self.icons.get("rps_header")).grid(row=0, column=0, padx=(0, 22))
        heading_frame = customtkinter.CTkFrame(header_frame, fg_color="transparent")
        heading_frame.grid(row=0, column=1, sticky="w")
        customtkinter.CTkLabel(heading_frame, text="ROCK PAPER SCISSORS", font=customtkinter.CTkFont(size=32, weight="bold"), anchor="w").pack(anchor="w")
        customtkinter.CTkLabel(heading_frame, text="Choose your move to win the best of 5 against the bot.", font=customtkinter.CTkFont(size=15), text_color="#B8C4D1", anchor="w").pack(anchor="w", pady=(4, 0))
        input_card = customtkinter.CTkFrame(main_frame, fg_color="#2B2D30", corner_radius=20, border_width=1, border_color="#3E454D")
        input_card.grid(row=1, column=0, sticky="ew", pady=(0, 18))
        input_card.grid_columnconfigure((0, 1, 2), weight=1)
        self.status_label = customtkinter.CTkLabel(input_card, text="Choose your move!", font=customtkinter.CTkFont(size=23, weight="bold"))
        self.status_label.grid(row=0, column=0, columnspan=3, pady=(18, 12))
        self.rock_button = customtkinter.CTkButton(input_card, text="", width=180, height=180, corner_radius=20, image=self.icons.get("rock"), fg_color="#3E454D", hover_color="#4B5563", command=lambda: self.submit_choice("rock"))
        self.rock_button.grid(row=1, column=0, padx=15, pady=20)
        self.paper_button = customtkinter.CTkButton(input_card, text="", width=180, height=180, corner_radius=20, image=self.icons.get("paper"), fg_color="#3E454D", hover_color="#4B5563", command=lambda: self.submit_choice("paper"))
        self.paper_button.grid(row=1, column=1, padx=15, pady=20)
        self.scissors_button = customtkinter.CTkButton(input_card, text="", width=180, height=180, corner_radius=20, image=self.icons.get("scissors"), fg_color="#3E454D", hover_color="#4B5563", command=lambda: self.submit_choice("scissors"))
        self.scissors_button.grid(row=1, column=2, padx=15, pady=20)
        lower_frame = customtkinter.CTkFrame(main_frame, fg_color="transparent")
        lower_frame.grid(row=2, column=0, sticky="nsew")
        lower_frame.grid_columnconfigure((0, 1), weight=1, uniform="info_cards")
        lower_frame.grid_rowconfigure(0, weight=1)
        stats_card = customtkinter.CTkFrame(lower_frame, fg_color="#2B2D30", corner_radius=20, border_width=1, border_color="#3E454D")
        stats_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        customtkinter.CTkLabel(stats_card, text="MATCH STATS", font=customtkinter.CTkFont(size=21, weight="bold")).pack(pady=(24, 18))
        self.match_score_label = customtkinter.CTkLabel(stats_card, text="YOU  0 : 0  BOT", font=customtkinter.CTkFont(size=28, weight="bold"), text_color="#5DADE2")
        self.match_score_label.pack(pady=(0, 20))
        self.record_label = customtkinter.CTkLabel(stats_card, text="Wins: 0\nDraws: 0\nLoses: 0", font=customtkinter.CTkFont(size=17), justify="left")
        self.record_label.pack(pady=8)
        result_card = customtkinter.CTkFrame(lower_frame, fg_color="#2B2D30", corner_radius=20, border_width=1, border_color="#3E454D")
        result_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        customtkinter.CTkLabel(result_card, text="LAST ROUND", font=customtkinter.CTkFont(size=21, weight="bold")).pack(pady=(24, 18))
        self.round_result_label = customtkinter.CTkLabel(result_card, text="READY", font=customtkinter.CTkFont(size=28, weight="bold"), text_color="#B8C4D1")
        self.round_result_label.pack(pady=(0, 12))
        choices_frame = customtkinter.CTkFrame(result_card, fg_color="transparent")
        choices_frame.pack(pady=10, fill="x", expand=True)
        choices_frame.grid_columnconfigure((0, 2), weight=1)
        self.your_choice_label = customtkinter.CTkLabel(choices_frame, text="YOU\n-", font=customtkinter.CTkFont(size=16), compound="top")
        self.your_choice_label.grid(row=0, column=0)
        customtkinter.CTkLabel(choices_frame, text="VS", font=customtkinter.CTkFont(size=20, weight="bold")).grid(row=0, column=1, padx=20)
        self.bot_choice_label = customtkinter.CTkLabel(choices_frame, text="BOT\n-", font=customtkinter.CTkFont(size=16), compound="top")
        self.bot_choice_label.grid(row=0, column=2)

    def submit_choice(self, choice):
        if self.game.is_finished(): return
        round_data = self.game.play_round(choice)
        self.update_ui(round_data)
        if round_data["finished"]: self.finish_match()

    def update_ui(self, data):
        result_colors = {"win": "#4ADE80", "draw": "#FACC15", "lose": "#FF6B6B"}
        self.status_label.configure(text="Round completed")
        self.round_result_label.configure(text=data["round_result"].upper(), text_color=result_colors[data["round_result"]])
        self.match_score_label.configure(text=f"YOU  {data['wins']} : {data['loses']}  BOT")
        self.record_label.configure(text=f"Wins: {data['wins']}\nDraws: {data['draws']}\nLoses: {data['loses']}")
        self.your_choice_label.configure(image=self.icons.get(data["user_choice"] + "_small"), text=f"YOU\n({data['user_choice'].upper()})")
        self.bot_choice_label.configure(image=self.icons.get(data["bot_choice"] + "_small"), text=f"BOT\n({data['bot_choice'].upper()})")

    def finish_match(self):
        match_result = self.game.get_match_result() # This now contains the score
        self.rock_button.configure(state="disabled")
        self.paper_button.configure(state="disabled")
        self.scissors_button.configure(state="disabled")
        result = match_result["result"]
        title, color = ("YOU WON!", "#4ADE80") if result == "win" else ("BOT WON", "#FF6B6B")
        self.status_label.configure(text=f"{title} Final score: {self.game.wins}:{self.game.loses}", text_color=color)
        if self.on_match_finished: self.on_match_finished(match_result)

    def restart_game(self):
        self.game = RPSGame()
        self.status_label.configure(text="Choose your move!", text_color="#B8C4D1")
        self.rock_button.configure(state="normal")
        self.paper_button.configure(state="normal")
        self.scissors_button.configure(state="normal")
        self.match_score_label.configure(text="YOU  0 : 0  BOT")
        self.record_label.configure(text="Wins: 0\nDraws: 0\nLoses: 0")
        self.round_result_label.configure(text="READY", text_color="#B8C4D1")
        self.your_choice_label.configure(image=None, text="YOU\n-")
        self.bot_choice_label.configure(image=None, text="BOT\n-")

    def close_window(self):
        self.grab_release()
        self.destroy()
        if self.parent.winfo_exists():
            self.parent.deiconify()
            self.parent.focus_force()

if __name__ == '__main__':
    class MockLauncher(customtkinter.CTk):
        def __init__(self):
            super().__init__()
            self.title("Mock Launcher")
            self.geometry("300x200")
            customtkinter.CTkButton(self, text="Open RPS Game", command=self.open_game).pack(pady=20)
        def open_game(self):
            RockPaperScissorsWindow(self)
    
    app = MockLauncher()
    app.mainloop()
