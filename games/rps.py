from random import choice


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

            score_round = 5
            score_round_bot = 5

            round_result = "draw"

        elif (
            (user_choice == "rock" and bot_choice == "scissors")
            or
            (user_choice == "paper" and bot_choice == "rock")
            or
            (user_choice == "scissors" and bot_choice == "paper")
        ):

            self.wins += 1

            score_round = 10
            score_round_bot = 0

            round_result = "win"

        else:

            self.loses += 1

            score_round = 0
            score_round_bot = 10

            round_result = "lose"

        self.score += score_round
        self.score_bot += score_round_bot

        return {
            "round_result": round_result,
            "user_choice": user_choice,
            "bot_choice": bot_choice,
            "wins": self.wins,
            "draws": self.draws,
            "loses": self.loses,
            "score": self.score,
            "score_bot": self.score_bot,
            "finished": self.is_finished()
        }

    def is_finished(self):
        return self.wins >= 3 or self.loses >= 3

    def get_match_result(self):

        if self.wins >= 3:
            result = "win"
        else:
            result = "lose"

        return {
            "result": result,
            "score": self.score,
            "details": {
                "wins": self.wins,
                "draws": self.draws,
                "loses": self.loses
            }
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