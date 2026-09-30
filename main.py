from database.db_manager import DatabaseManager
from users.user_manager import UserManager
from games.numguess import NumberGuessGame
from games.rps import RPSGame
from utils import *

def logged_in_menu(user_manager, db):

    while True:

        print_header("GAMES WITH BOT")
        print("1 - Quickstart")
        print("2 - Number Guess")
        print("3 - Rock Paper Scissors")
        print("4 - Match History")
        print("5 - Leaderboard")
        print("6 - Favorites")
        print("7 - Logout")

        choice = input("Choice: ")

        if choice == "1":
            quickstart = db.get_quickstart(user_manager.current_user["id"])
            if quickstart is None:
                print("No quickstart game selected.")
                input("Press Enter...")
                continue
                
            game_id = quickstart[0]
                
            if game_id == 1:
                game = NumberGuessGame()
                result = game.play_numguess_cli()
                db.save_match(
                    user_id=user_manager.current_user["id"],
                    game_id=1,
                    result=result["result"],
                    score=result["score"],
                    details=result["details"]
                    )
                print("\nGame Result:")
                print(result)
                input("Press Enter to continue...")
                
            elif game_id == 2:
                game = RPSGame()
                result = game.play_rps_cli()
                db.save_match(
                    user_id=user_manager.current_user["id"],
                    game_id=2,
                    result=result["result"],
                    score=result["score"],
                    details=result["details"]
                )
                print("\nGame Result:")
                print(result)
                input("Press Enter to continue...")


        if choice == "2":
            game = NumberGuessGame()
            result = game.play_numguess_cli()
            db.save_match(
                user_id=user_manager.current_user["id"],
                game_id=1,
                result=result["result"],
                score=result["score"],
                details=result["details"]
                )
            print("\nGame Result:")
            print(result)
            input("Press Enter to continue...")


        elif choice == "3":

            game = RPSGame()
            result = game.play_rps_cli()
            db.save_match(
                user_id=user_manager.current_user["id"],
                game_id=2,
                result=result["result"],
                score=result["score"],
                details=result["details"]
            )
            
        elif choice == "4":

            history = db.get_match_history(
                user_manager.current_user["id"]
            )
            print_header("MATCH HISTORY")

            if not history:
                print("No matches played yet.")
            else:

                for game, result, score, played_at in history:
                    print(
                        f"{played_at} | "
                        f"{game} | "
                        f"{result.upper()} | "
                        f"{score} points"
                    )

            input("\nPress Enter...")

        elif choice == "5":
            leaderboard = db.get_leaderboard()
            print_header("LEADERBOARD")
            
            position = 1
            
            for username, score in leaderboard:
                print(
                f"{position}. "
                f"{username:<15} "
                f"{score} points"
                )
            position += 1
            
            input("\nPress Enter...")

        elif choice == "6":
            favorites_menu(user_manager, db)

        elif choice == "7":
            user_manager.logout()
            break

        else:
            print("Invalid choice!")


def favorites_menu(user_manager, db):

    while True:

        print_header("FAVORITES")

        favorites = db.get_favorites(
            user_manager.current_user["id"]
        )

        if favorites:
            print("Current favorites:")

            for game_id, game_name, quickstart in favorites:

                marker = ""

                if quickstart:
                    marker = " [QUICKSTART]"

                print(f"{game_id} - {game_name}{marker}")

        else:
            print("No favorite games.")

        print("\n1 - Add Number Guess")
        print("2 - Add Rock Paper Scissors")
        print("3 - Set Quickstart")
        print("4 - Back")

        choice = input("\nChoice: ")

        if choice == "1":

            db.add_favorite(
                user_manager.current_user["id"],
                1
            )

            input("Press Enter...")

        elif choice == "2":

            db.add_favorite(
                user_manager.current_user["id"],
                2
            )

            input("Press Enter...")

        elif choice == "3":

            print("\nSelect quickstart game:")

            for game_id, game_name, quickstart in favorites:

                print(f"{game_id} - {game_name}")

            try:

                game_id = int(
                    input("\nGame ID: ")
                )

                db.set_quickstart(
                    user_manager.current_user["id"],
                    game_id
                )

                print("Quickstart updated.")

            except:
                print("Invalid game.")

            input("Press Enter...")

        elif choice == "4":

            break

        else:

            print("Invalid choice.")
            input("Press Enter...")

def main():

    db = DatabaseManager()

    user_manager = UserManager(db)

    while True:
        print_header("MAIN MENU")
        print("1 - Register")
        print("2 - Login")
        print("3 - Exit")

        choice = input("Choice: ")

        if choice == "1":

            user_manager.register()

        elif choice == "2":

            success = user_manager.login()

            if success:
                logged_in_menu(user_manager, db)

        elif choice == "3":

            db.close()
            print("Bye!")
            break

        else:

            print("Invalid choice!")


if __name__ == "__main__":
    
    main()

"""
Minimal 2 Games
R-P-S: win - 10 points, draw - 5 points, lose - 0 points (each game, then BO5 -> result, sum of points -> score)
Guess Number: number guessed - 10 points, +-5 from number - 7 points, +-10 from number - 5 points, +-25 from number - 2 points, 
lose - 0 points (each game, then BO5 -> result, sum of points -> score)

"""