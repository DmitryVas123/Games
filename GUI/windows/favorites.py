

import customtkinter


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

        favorite_ids = {
            game_id
            for game_id, _, _ in favorites
        }
        
        games = [
            game
            for game in self.db.get_games()
            if game[0] not in favorite_ids
        ]

        for i, (game_id, game_name) in enumerate(games):
            customtkinter.CTkButton(
            add_frame,
            text=f"Add {game_name}",
            command=lambda gid=game_id: self.add_fav(gid)
            ).grid(
            row=i // 2,
            column=i % 2,
            padx=5,
            pady=5,
            sticky="ew"
            )

        for i, (game_id, game_name, is_quickstart) in enumerate(favorites):

            marker = " [QUICKSTART]" if is_quickstart else ""

            fav_label = customtkinter.CTkLabel(
                self.frame,
                text=f"• {game_name}{marker}",
                font=customtkinter.CTkFont(size=15)
            )

            fav_label.grid(
                row=i + 1,
                column=0,
                sticky="w",
                padx=10
            )

            radio_btn = customtkinter.CTkRadioButton(
                self.frame,
                text="",
                variable=self.quickstart_var,
                value=str(game_id)
            )

            radio_btn.grid(
                row=i + 1,
                column=1,
                sticky="e"
            )

            if is_quickstart:
                radio_btn.select()

            remove_btn = customtkinter.CTkButton(
                self.frame,
                text="Remove",
                width=80,
                fg_color="#DC2626",
                hover_color="#991B1B",
                command=lambda gid=game_id: self.remove_fav(gid)
            )

            remove_btn.grid(
                row=i + 1,
                column=2,
                padx=5
            )
        
        customtkinter.CTkButton(self.frame, text="Set Quickstart", command=self.set_quickstart).grid(row=len(favorites)+3, column=0, columnspan=2, pady=10, sticky="ew")

    def add_fav(self, game_id):
        self.db.add_favorite(self.user_id, game_id)
        self.refresh_favorites_list()

    def set_quickstart(self):
        game_id_str = self.quickstart_var.get()
        if game_id_str:
            self.db.set_quickstart(self.user_id, int(game_id_str))
            self.refresh_favorites_list()

    def remove_fav(self, game_id):

        self.db.remove_favorite(
            self.user_id,
            game_id
        )

        self.refresh_favorites_list()
