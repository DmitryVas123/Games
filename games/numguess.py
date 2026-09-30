# games/numguess.py

from random import randint


class NumberGuessGame:

    def __init__(self):

        self.score = 0
        self.score_bot = 0

        self.wins = 0
        self.draws = 0
        self.loses = 0

    def play_round(self, user_guess):

        number_to_guess = randint(1, 100)
        bot_guess = randint(1, 100)

        distance = abs(number_to_guess - user_guess)
        distance_bot = abs(number_to_guess - bot_guess)

        score_round = self.calculate_points(distance)
        score_round_bot = self.calculate_points(distance_bot)

        if score_round > score_round_bot:

            self.wins += 1
            round_result = "win"

        elif score_round < score_round_bot:

            self.loses += 1
            round_result = "lose"

        else:

            self.draws += 1
            round_result = "draw"

        self.score += score_round
        self.score_bot += score_round_bot

        return {
            "round_result": round_result,
            "number_to_guess": number_to_guess,
            "user_guess": user_guess,
            "bot_guess": bot_guess,
            "user_points": score_round,
            "bot_points": score_round_bot,
            "wins": self.wins,
            "draws": self.draws,
            "loses": self.loses,
            "score": self.score,
            "score_bot": self.score_bot,
            "finished": self.is_finished()
        }

    def calculate_points(self, distance):

        if distance == 0:
            return 10

        elif distance <= 5:
            return 7

        elif distance <= 10:
            return 5

        elif distance <= 25:
            return 2

        return 0

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

    def play_numguess_cli(self):

        while not self.is_finished():

            try:
                guess = int(
                    input("Guess a number (1-100): ")
                )

            except ValueError:

                print("Invalid number!")
                continue

            data = self.play_round(guess)

            print(
                f"Secret: {data['number_to_guess']}"
            )

            print(
                f"You guessed: {data['user_guess']} "
                f"(+{data['user_points']})"
            )

            print(
                f"Bot guessed: {data['bot_guess']} "
                f"(+{data['bot_points']})"
            )

            print(
                f"Round result: "
                f"{data['round_result'].upper()}"
            )

            print(
                f"BO5 Score: "
                f"{data['wins']}:{data['loses']}"
            )

        return self.get_match_result()