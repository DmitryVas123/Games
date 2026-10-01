from random import choice


# This code goes inside your rps_window.py file, replacing the existing RPSGame class

class RPSGame:
    def __init__(self):
        self.score = 0
        self.score_bot = 0
        self.wins = 0
        self.draws = 0
        self.loses = 0
        self.choices = ["rock", "paper", "scissors"]

    def play_round(self, user_choice):
        bot_choice = choice(self.choices)
        
        if user_choice == bot_choice:
            self.draws += 1
            round_result = "draw"
            score_round = 5
        elif (
            (user_choice == "rock" and bot_choice == "scissors") or
            (user_choice == "paper" and bot_choice == "rock") or
            (user_choice == "scissors" and bot_choice == "paper")
        ):
            self.wins += 1
            round_result = "win"
            score_round = 10
        else:
            self.loses += 1
            round_result = "lose"
            score_round = 0
            
        self.score += score_round
        
        # We don't need to track bot score for this logic, but it's here if you ever need it
        # self.score_bot += score_round_bot 
        
        return {
            "round_result": round_result,
            "user_choice": user_choice,
            "bot_choice": bot_choice,
            "wins": self.wins, "draws": self.draws, "loses": self.loses,
            "score": self.score,
            "finished": self.is_finished()
        }

    def is_finished(self):
        return self.wins >= 3 or self.loses >= 3

    def get_match_result(self):
        result = "win" if self.wins >= 3 else "lose"
        
        # --- THE FIX IS HERE ---
        # Cap the score at a maximum of 50 points.
        final_score = min(self.score, 50)
        
        return {
            "result": result,
            "score": final_score, # Return the capped score
            "details": {"wins": self.wins, "draws": self.draws, "loses": self.loses}
        }


    def play_rps_cli(self):

        while not self.is_finished():

            user = input(
                "Rock, Paper or Scissors? "
            ).lower()

            print(
                self.play_round(user)
            )

        return self.get_match_result()