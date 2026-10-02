

import customtkinter


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
