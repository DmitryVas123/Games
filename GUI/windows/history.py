

import customtkinter


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

