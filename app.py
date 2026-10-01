import customtkinter
from database.db_manager import DatabaseManager
from users.user_manager import UserManager
from GUI.login_window import LoginWindow
from GUI.launcher import GameLauncher

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.withdraw() 
        
        customtkinter.set_appearance_mode("Dark")
        
        self.db = DatabaseManager()
        self.user_manager = UserManager(self.db)
        
        self.show_login_window()
        
    def show_login_window(self):
        """Displays the login window and passes the close handler."""
        self.login_window = LoginWindow(
            self, 
            self.user_manager, 
            self.db, 
            on_login_success=self.show_launcher,
            on_close=self.on_close # This call is correct
        )
        
    def show_launcher(self, user_info):
        """Displays the main game launcher after a successful login."""
        self.launcher_window = GameLauncher(
            parent=self, 
            on_logout=self.handle_logout,
            username=user_info['username'],
            user_id=user_info['id'],
            db=self.db
        )

    def handle_logout(self):
        """Closes the launcher and shows the login window again."""
        if self.launcher_window:
            self.launcher_window.destroy()
        self.show_login_window()

    def on_close(self):
        """
        This method is called when a window's close button is pressed.
        It ensures the database is closed and the entire application exits cleanly.
        """
        print("Close button pressed. Shutting down application.")
        self.db.close()
        self.destroy() # Destroy the root window, which stops the mainloop
      
        
    def run(self):
        self.mainloop()
        # Ensure the database is closed when the app finally exits
        self.db.close()
        print("Application closed.")

if __name__ == "__main__":
    app = App()
    app.run()
