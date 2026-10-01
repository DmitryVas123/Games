import customtkinter

class RegistrationWindow(customtkinter.CTkToplevel):
    """A pop-up window for user registration."""
    def __init__(self, parent, user_manager, on_success):
        super().__init__(parent)
        self.user_manager = user_manager
        self.on_success = on_success # Callback function for successful registration

        self.title("Register New User")
        self.geometry("400x350")
        self.transient(parent)
        self.grab_set()

        self.status_label = customtkinter.CTkLabel(self, text="")
        self.status_label.pack(pady=(20, 0))

        self.username_entry = customtkinter.CTkEntry(self, placeholder_text="Username")
        self.username_entry.pack(padx=40, pady=10)
        self.password_entry = customtkinter.CTkEntry(self, placeholder_text="Password", show="*")
        self.password_entry.pack(padx=40, pady=10)
        self.confirm_password_entry = customtkinter.CTkEntry(self, placeholder_text="Confirm Password", show="*")
        self.confirm_password_entry.pack(padx=40, pady=10)

        customtkinter.CTkButton(self, text="Register", command=self.register).pack(pady=20)

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()

        if not (username and password and confirm_password):
            self.show_error("All fields are required.")
            return
        if password != confirm_password:
            self.show_error("Passwords do not match.")
            return

        result, message = self.user_manager.register_gui(username, password)

        if result:
            self.on_success(message) # Call the success callback from the parent
            self.destroy()
        else:
            self.show_error(message)

    def show_error(self, message):
        self.status_label.configure(text=message, text_color="#FF6B6B")

class LoginWindow(customtkinter.CTkToplevel):
    # **THE FIX IS HERE**: Added 'on_close' to the function definition
    def __init__(self, parent, user_manager, db, on_login_success, on_close):
        super().__init__(parent)
        self.user_manager = user_manager
        self.db = db
        self.on_login_success = on_login_success
        
        self.title("Games With Bot - Login")
        self.geometry("500x400")
        
        # Connect the window's "X" button to the main app's close function
        self.protocol("WM_DELETE_WINDOW", on_close)

        # --- Widgets ---
        self.status_label = customtkinter.CTkLabel(self, text="Please log in or register.", font=customtkinter.CTkFont(size=14))
        self.status_label.pack(pady=(40, 10))
        self.username_entry = customtkinter.CTkEntry(self, placeholder_text="Username", width=250)
        self.username_entry.pack(padx=50, pady=10)
        self.password_entry = customtkinter.CTkEntry(self, placeholder_text="Password", show="*", width=250)
        self.password_entry.pack(padx=50, pady=10)
        customtkinter.CTkButton(self, text="Login", command=self.login, width=250).pack(pady=10)
        customtkinter.CTkButton(self, text="Register", command=self.open_registration_window, width=250, fg_color="#3E454D", hover_color="#4B5563").pack()
        
        self.transient(parent)
        self.grab_set()

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if not username or not password:
            self.show_error("Username and password are required.")
            return
        user = self.user_manager.login_gui(username, password)
        if user:
            self.destroy()
            self.on_login_success(user)
        else:
            self.show_error("Invalid username or password.")

    def open_registration_window(self):
        RegistrationWindow(self, self.user_manager, on_success=self.handle_registration_success)

    def handle_registration_success(self, message):
        self.status_label.configure(text=message, text_color="#4ADE80")

    def show_error(self, message):
        self.status_label.configure(text=message, text_color="#FF6B6B")
        self.username_entry.configure(border_color="#FF6B6B")
        self.password_entry.configure(border_color="#FF6B6B")
