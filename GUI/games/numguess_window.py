import customtkinter
from PIL import Image
import os

import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

sys.path.append(PROJECT_ROOT)

from games.numguess import NumberGuessGame

class NumberGuessWindow(customtkinter.CTkToplevel):

    def __init__(
        self,
        parent,
        username="Player1",
        on_match_finished=None
    ):
        super().__init__(parent)

        self.parent = parent
        self.username = username
        self.on_match_finished = on_match_finished

        # Create a fresh game for this window
        self.game = NumberGuessGame()

        # Counts played rounds, including draws
        self.round_number = 1

        self.title("Games With Bot - Number Guess")
        self.geometry("1280x720")
        self.resizable(False, False)
        self.configure(fg_color="#1B2838")

        # Keep game window above the launcher
        self.transient(parent)

        # Optional: prevent interacting with launcher
        # while the game window is open
        self.grab_set()

        self.protocol(
            "WM_DELETE_WINDOW",
            self.close_window
        )

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.icons = self.load_assets()

        self.create_sidebar()
        self.create_game_area()

        # Allow Enter key to submit a guess
        self.guess_entry.bind(
            "<Return>",
            lambda event: self.submit_guess()
        )

        self.guess_entry.focus()

    def load_assets(self):
        icons = {}

        assets = {
            "numguess": (
                "./GUI/assets/games/numguess.png",
                (128, 128)
            ),
            "logout": (
                "./GUI/assets/icons/logout.png",
                (24, 24)
            )
        }

        for name, (path, size) in assets.items():
            if os.path.exists(path):
                image = Image.open(path).convert("RGBA")

                icons[name] = customtkinter.CTkImage(
                    light_image=image,
                    dark_image=image,
                    size=size
                )
            else:
                icons[name] = None
                print(f"Warning: Asset not found: {path}")

        return icons

    def create_sidebar(self):
        sidebar = customtkinter.CTkFrame(
            self,
            width=240,
            corner_radius=0,
            fg_color="#212325"
        )

        sidebar.grid(
            row=0,
            column=0,
            sticky="nsw"
        )

        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(4, weight=1)

        title_label = customtkinter.CTkLabel(
            sidebar,
            text="GAMES WITH BOT",
            font=customtkinter.CTkFont(
                size=20,
                weight="bold"
            )
        )

        title_label.grid(
            row=0,
            column=0,
            padx=20,
            pady=(30, 20)
        )

        username_label = customtkinter.CTkLabel(
            sidebar,
            text=f"Welcome, {self.username}",
            font=customtkinter.CTkFont(size=14),
            anchor="w"
        )

        username_label.grid(
            row=1,
            column=0,
            padx=20,
            pady=10,
            sticky="ew"
        )

        back_button = customtkinter.CTkButton(
            sidebar,
            text="← Back to Launcher",
            height=42,
            fg_color="transparent",
            hover_color="#33373A",
            anchor="w",
            command=self.close_window
        )

        back_button.grid(
            row=2,
            column=0,
            padx=20,
            pady=10,
            sticky="ew"
        )

        new_game_button = customtkinter.CTkButton(
            sidebar,
            text="↻ Restart Game",
            height=42,
            fg_color="transparent",
            hover_color="#33373A",
            anchor="w",
            command=self.restart_game
        )

        new_game_button.grid(
            row=3,
            column=0,
            padx=20,
            pady=10,
            sticky="ew"
        )

        close_button = customtkinter.CTkButton(
            sidebar,
            text="Close Game",
            image=self.icons.get("logout"),
            compound="left",
            height=42,
            fg_color="#A93232",
            hover_color="#842828",
            command=self.close_window
        )

        close_button.grid(
            row=5,
            column=0,
            padx=20,
            pady=20,
            sticky="ew"
        )

    def create_game_area(self):
        main_frame = customtkinter.CTkFrame(
            self,
            fg_color="transparent"
        )

        main_frame.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=40,
            pady=24
        )

        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)

        # Header
        header_frame = customtkinter.CTkFrame(
            main_frame,
            fg_color="transparent"
        )

        header_frame.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 18)
        )

        header_frame.grid_columnconfigure(1, weight=1)

        icon_label = customtkinter.CTkLabel(
            header_frame,
            text="",
            image=self.icons.get("numguess")
        )

        icon_label.grid(
            row=0,
            column=0,
            padx=(0, 22)
        )

        heading_frame = customtkinter.CTkFrame(
            header_frame,
            fg_color="transparent"
        )

        heading_frame.grid(
            row=0,
            column=1,
            sticky="w"
        )

        customtkinter.CTkLabel(
            heading_frame,
            text="NUMBER GUESS",
            font=customtkinter.CTkFont(
                size=32,
                weight="bold"
            ),
            anchor="w"
        ).pack(anchor="w")

        customtkinter.CTkLabel(
            heading_frame,
            text="Guess closer to the secret number than the bot.",
            font=customtkinter.CTkFont(size=15),
            text_color="#B8C4D1",
            anchor="w"
        ).pack(anchor="w", pady=(4, 0))

        # Guess input card
        input_card = customtkinter.CTkFrame(
            main_frame,
            fg_color="#2B2D30",
            corner_radius=20,
            border_width=1,
            border_color="#3E454D"
        )

        input_card.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(0, 18)
        )

        input_card.grid_columnconfigure(0, weight=1)

        self.round_label = customtkinter.CTkLabel(
            input_card,
            text="Round 1",
            font=customtkinter.CTkFont(
                size=23,
                weight="bold"
            )
        )

        self.round_label.grid(
            row=0,
            column=0,
            pady=(18, 4)
        )

        self.status_label = customtkinter.CTkLabel(
            input_card,
            text="Enter a whole number from 1 to 100",
            font=customtkinter.CTkFont(size=14),
            text_color="#B8C4D1"
        )

        self.status_label.grid(
            row=1,
            column=0,
            pady=(0, 12)
        )

        input_row = customtkinter.CTkFrame(
            input_card,
            fg_color="transparent"
        )

        input_row.grid(
            row=2,
            column=0,
            pady=(0, 20)
        )

        self.guess_entry = customtkinter.CTkEntry(
            input_row,
            width=250,
            height=52,
            justify="center",
            placeholder_text="1 - 100",
            font=customtkinter.CTkFont(
                size=23,
                weight="bold"
            )
        )

        self.guess_entry.grid(
            row=0,
            column=0,
            padx=(0, 12)
        )

        self.guess_button = customtkinter.CTkButton(
            input_row,
            text="GUESS ▶",
            width=180,
            height=52,
            corner_radius=10,
            font=customtkinter.CTkFont(
                size=17,
                weight="bold"
            ),
            command=self.submit_guess
        )

        self.guess_button.grid(
            row=0,
            column=1
        )

        # Lower information cards
        lower_frame = customtkinter.CTkFrame(
            main_frame,
            fg_color="transparent"
        )

        lower_frame.grid(
            row=2,
            column=0,
            sticky="nsew"
        )

        lower_frame.grid_columnconfigure(
            (0, 1),
            weight=1,
            uniform="info_cards"
        )

        lower_frame.grid_rowconfigure(0, weight=1)

        # Match stats
        stats_card = customtkinter.CTkFrame(
            lower_frame,
            fg_color="#2B2D30",
            corner_radius=20,
            border_width=1,
            border_color="#3E454D"
        )

        stats_card.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 10)
        )

        customtkinter.CTkLabel(
            stats_card,
            text="MATCH STATS",
            font=customtkinter.CTkFont(
                size=21,
                weight="bold"
            )
        ).pack(pady=(24, 18))

        self.match_score_label = customtkinter.CTkLabel(
            stats_card,
            text="YOU  0 : 0  BOT",
            font=customtkinter.CTkFont(
                size=28,
                weight="bold"
            ),
            text_color="#5DADE2"
        )

        self.match_score_label.pack(pady=(0, 20))

        self.points_label = customtkinter.CTkLabel(
            stats_card,
            text="Your points: 0\nBot points: 0",
            font=customtkinter.CTkFont(size=17),
            justify="left"
        )

        self.points_label.pack(pady=8)

        self.record_label = customtkinter.CTkLabel(
            stats_card,
            text="Wins: 0\nDraws: 0\nLoses: 0",
            font=customtkinter.CTkFont(size=17),
            justify="left"
        )

        self.record_label.pack(pady=8)

        # Last round
        result_card = customtkinter.CTkFrame(
            lower_frame,
            fg_color="#2B2D30",
            corner_radius=20,
            border_width=1,
            border_color="#3E454D"
        )

        result_card.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(10, 0)
        )

        customtkinter.CTkLabel(
            result_card,
            text="LAST ROUND",
            font=customtkinter.CTkFont(
                size=21,
                weight="bold"
            )
        ).pack(pady=(24, 18))

        self.round_result_label = customtkinter.CTkLabel(
            result_card,
            text="READY",
            font=customtkinter.CTkFont(
                size=28,
                weight="bold"
            ),
            text_color="#B8C4D1"
        )

        self.round_result_label.pack(pady=(0, 12))

        self.result_details_label = customtkinter.CTkLabel(
            result_card,
            text=(
                "Secret number: -\n"
                "Your guess: -\n"
                "Bot guess: -\n\n"
                "Your round points: -\n"
                "Bot round points: -"
            ),
            font=customtkinter.CTkFont(size=16),
            justify="left"
        )

        self.result_details_label.pack(pady=10)

    def submit_guess(self):
        """Reads GUI input and plays exactly one game round."""

        if self.game.is_finished():
            return

        raw_guess = self.guess_entry.get().strip()

        try:
            user_guess = int(raw_guess)
        except ValueError:
            self.show_input_error(
                "Please enter a whole number."
            )
            return

        if not 1 <= user_guess <= 100:
            self.show_input_error(
                "The number must be between 1 and 100."
            )
            return

        # Call the independent game logic
        round_data = self.game.play_round(user_guess)

        self.update_round_interface(round_data)

        self.guess_entry.delete(0, "end")

        if round_data["finished"]:
            self.finish_match()
        else:
            self.round_number += 1
            self.round_label.configure(
                text=f"Round {self.round_number}"
            )
            self.guess_entry.focus()

    def show_input_error(self, message):
        self.status_label.configure(
            text=message,
            text_color="#FF6B6B"
        )

        self.guess_entry.configure(
            border_color="#FF6B6B"
        )

        self.guess_entry.focus()

    def update_round_interface(self, data):
        result = data["round_result"]

        result_colors = {
            "win": "#4ADE80",
            "draw": "#FACC15",
            "lose": "#FF6B6B"
        }

        self.status_label.configure(
            text="Round completed",
            text_color="#B8C4D1"
        )

        self.guess_entry.configure(
            border_color=(
                customtkinter.ThemeManager
                .theme["CTkEntry"]["border_color"]
            )
        )

        self.round_result_label.configure(
            text=result.upper(),
            text_color=result_colors[result]
        )

        self.match_score_label.configure(
            text=(
                f"YOU  {data['wins']} : "
                f"{data['loses']}  BOT"
            )
        )

        self.points_label.configure(
            text=(
                f"Your points: {data['score']}\n"
                f"Bot points: {data['score_bot']}"
            )
        )

        self.record_label.configure(
            text=(
                f"Wins: {data['wins']}\n"
                f"Draws: {data['draws']}\n"
                f"Loses: {data['loses']}"
            )
        )

        self.result_details_label.configure(
            text=(
                f"Secret number: "
                f"{data['number_to_guess']}\n"
                f"Your guess: {data['user_guess']}\n"
                f"Bot guess: {data['bot_guess']}\n\n"
                f"Your round points: "
                f"+{data['user_points']}\n"
                f"Bot round points: "
                f"+{data['bot_points']}"
            )
        )

    def finish_match(self):
        match_result = self.game.get_match_result()

        self.guess_entry.configure(
            state="disabled"
        )

        self.guess_button.configure(
            state="disabled",
            text="MATCH FINISHED"
        )

        if match_result["result"] == "win":
            title = "YOU WON!"
            color = "#4ADE80"
        else:
            title = "BOT WON"
            color = "#FF6B6B"

        self.status_label.configure(
            text=(
                f"{title} Final score: "
                f"{self.game.wins}:{self.game.loses}"
            ),
            text_color=color
        )

        self.show_match_dialog(match_result)

        # Optional callback for saving into the database
        if self.on_match_finished is not None:
            self.on_match_finished(match_result)

    def show_match_dialog(self, match_result):
        dialog = customtkinter.CTkToplevel(self)

        dialog.title("Match Finished")
        dialog.geometry("420x330")
        dialog.resizable(False, False)
        dialog.configure(fg_color="#1B2838")
        dialog.transient(self)
        dialog.grab_set()

        result_text = match_result["result"].upper()

        result_color = (
            "#4ADE80"
            if match_result["result"] == "win"
            else "#FF6B6B"
        )

        customtkinter.CTkLabel(
            dialog,
            text=result_text,
            font=customtkinter.CTkFont(
                size=34,
                weight="bold"
            ),
            text_color=result_color
        ).pack(pady=(35, 15))

        customtkinter.CTkLabel(
            dialog,
            text=(
                f"Score: {match_result['score']} points\n\n"
                f"Wins: {match_result['details']['wins']}\n"
                f"Draws: {match_result['details']['draws']}\n"
                f"Loses: {match_result['details']['loses']}"
            ),
            font=customtkinter.CTkFont(size=17)
        ).pack(pady=10)

        buttons = customtkinter.CTkFrame(
            dialog,
            fg_color="transparent"
        )

        buttons.pack(pady=22)

        customtkinter.CTkButton(
            buttons,
            text="PLAY AGAIN",
            command=lambda: self.restart_from_dialog(dialog)
        ).grid(
            row=0,
            column=0,
            padx=8
        )

        customtkinter.CTkButton(
            buttons,
            text="BACK TO LAUNCHER",
            fg_color="#3E454D",
            hover_color="#4B5563",
            command=lambda: self.close_from_dialog(dialog)
        ).grid(
            row=0,
            column=1,
            padx=8
        )

    def restart_from_dialog(self, dialog):
        dialog.destroy()
        self.restart_game()

    def close_from_dialog(self, dialog):
        dialog.destroy()
        self.close_window()

    def restart_game(self):
        self.game = NumberGuessGame()
        self.round_number = 1

        self.round_label.configure(
            text="Round 1"
        )

        self.status_label.configure(
            text="Enter a whole number from 1 to 100",
            text_color="#B8C4D1"
        )

        self.guess_entry.configure(
            state="normal"
        )

        self.guess_entry.delete(0, "end")

        self.guess_button.configure(
            state="normal",
            text="GUESS ▶"
        )

        self.match_score_label.configure(
            text="YOU  0 : 0  BOT"
        )

        self.points_label.configure(
            text="Your points: 0\nBot points: 0"
        )

        self.record_label.configure(
            text="Wins: 0\nDraws: 0\nLoses: 0"
        )

        self.round_result_label.configure(
            text="READY",
            text_color="#B8C4D1"
        )

        self.result_details_label.configure(
            text=(
                "Secret number: -\n"
                "Your guess: -\n"
                "Bot guess: -\n\n"
                "Your round points: -\n"
                "Bot round points: -"
            )
        )

        self.guess_entry.focus()

    def close_window(self):
        self.grab_release()
        self.destroy()

        # Restore launcher
        if self.parent.winfo_exists():
            self.parent.deiconify()
            self.parent.focus_force()

