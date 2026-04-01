"""Terminal Mini-Games Collection — Quick games playable in the terminal.

A collection of small terminal-based games that can be played during development
breaks or as part of quest rewards. Includes word puzzles, number games, and
quick reflex challenges.

Zeta34: Build terminal mini-games collection.

OmniTag: {
    "purpose": "terminal_games",
    "tags": ["Games", "Terminal", "MiniGames", "Fun"],
    "category": "game_systems",
    "evolution_stage": "v1.0"
}
"""

import logging
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar

logger = logging.getLogger(__name__)


class GameResult(Enum):
    """Result of a mini-game."""

    WIN = "win"
    LOSE = "lose"
    TIMEOUT = "timeout"
    QUIT = "quit"


@dataclass
class MiniGameScore:
    """Score from a mini-game play."""

    game_name: str
    result: GameResult
    score: int
    time_taken: float
    attempts: int = 1
    xp_earned: int = 0


class NumberGuess:
    """Guess the number game."""

    name = "Number Guess"
    description = "Guess the secret number between 1 and 100"
    xp_win = 25
    xp_close = 10

    def __init__(self, max_attempts: int = 7):
        """Initialize NumberGuess with max_attempts."""
        self.max_attempts = max_attempts
        self.secret = 0
        self.attempts = 0

    def start(self) -> str:
        """Start a new game."""
        self.secret = random.randint(1, 100)
        self.attempts = 0
        return f"I'm thinking of a number between 1 and 100. You have {self.max_attempts} attempts."

    def guess(self, number: int) -> tuple[str, MiniGameScore | None]:
        """Make a guess.

        Returns:
            Tuple of (feedback message, score if game ended)
        """
        self.attempts += 1

        if number == self.secret:
            # Win!
            xp = max(self.xp_win - (self.attempts - 1) * 3, self.xp_close)
            score = MiniGameScore(
                game_name=self.name,
                result=GameResult.WIN,
                score=100 - (self.attempts - 1) * 10,
                time_taken=0,
                attempts=self.attempts,
                xp_earned=xp,
            )
            return (
                f"🎉 Correct! The number was {self.secret}. You got it in {self.attempts} attempts! +{xp}XP",
                score,
            )

        if self.attempts >= self.max_attempts:
            score = MiniGameScore(
                game_name=self.name,
                result=GameResult.LOSE,
                score=0,
                time_taken=0,
                attempts=self.attempts,
                xp_earned=0,
            )
            return f"❌ Out of attempts! The number was {self.secret}.", score

        hint = "higher" if number < self.secret else "lower"
        remaining = self.max_attempts - self.attempts
        return f"Go {hint}! ({remaining} attempts left)", None


class WordScramble:
    """Unscramble the word game."""

    name = "Word Scramble"
    description = "Unscramble the programming-related word"
    xp_win = 20

    WORDS: ClassVar[list] = [
        "function",
        "variable",
        "algorithm",
        "recursion",
        "iteration",
        "compiler",
        "debugger",
        "interface",
        "abstract",
        "polymorphism",
        "inheritance",
        "encapsulation",
        "constructor",
        "exception",
        "synchronous",
        "asynchronous",
        "callback",
        "promise",
        "decorator",
        "generator",
        "coroutine",
        "protocol",
        "singleton",
        "factory",
        "observer",
    ]

    def __init__(self, max_attempts: int = 3):
        """Initialize WordScramble with max_attempts."""
        self.max_attempts = max_attempts
        self.word = ""
        self.scrambled = ""
        self.attempts = 0
        self.start_time = 0.0

    def start(self) -> str:
        """Start a new game."""
        self.word = random.choice(self.WORDS)
        letters = list(self.word)
        random.shuffle(letters)
        self.scrambled = "".join(letters)
        self.attempts = 0
        self.start_time = time.time()

        # Ensure it's actually scrambled
        while self.scrambled == self.word:
            random.shuffle(letters)
            self.scrambled = "".join(letters)

        return f"Unscramble this programming word: {self.scrambled.upper()}"

    def guess(self, answer: str) -> tuple[str, MiniGameScore | None]:
        """Submit an answer."""
        self.attempts += 1
        elapsed = time.time() - self.start_time

        if answer.lower() == self.word:
            # Bonus for speed
            time_bonus = max(0, 10 - int(elapsed // 3))
            xp = self.xp_win + time_bonus
            score = MiniGameScore(
                game_name=self.name,
                result=GameResult.WIN,
                score=100 + time_bonus * 5,
                time_taken=elapsed,
                attempts=self.attempts,
                xp_earned=xp,
            )
            return f"🎉 Correct! '{self.word}' in {elapsed:.1f}s! +{xp}XP", score

        if self.attempts >= self.max_attempts:
            score = MiniGameScore(
                game_name=self.name,
                result=GameResult.LOSE,
                score=0,
                time_taken=elapsed,
                attempts=self.attempts,
                xp_earned=0,
            )
            return f"❌ Out of attempts! The word was '{self.word}'.", score

        remaining = self.max_attempts - self.attempts
        return f"Not quite! Try again ({remaining} attempts left)", None


class CodeQuiz:
    """Programming trivia quiz."""

    name = "Code Quiz"
    description = "Answer programming trivia questions"
    xp_per_correct = 15

    QUESTIONS: ClassVar[list] = [
        ("What does 'API' stand for?", "application programming interface"),
        ("In Python, what keyword is used to define a function?", "def"),
        ("What data structure uses LIFO (Last In, First Out)?", "stack"),
        ("What does 'SQL' stand for?", "structured query language"),
        ("In git, what command saves your changes locally?", "commit"),
        ("What symbol starts a comment in Python?", "#"),
        ("What is the output of: print(2 ** 3)?", "8"),
        ("What data structure uses FIFO (First In, First Out)?", "queue"),
        ("What does JSON stand for?", "javascript object notation"),
        ("What Python keyword creates a generator?", "yield"),
        ("What does HTML stand for?", "hypertext markup language"),
        ("In Python, what function returns the length of a list?", "len"),
        ("What does CSS stand for?", "cascading style sheets"),
        ("What symbol denotes a decorator in Python?", "@"),
        ("What does 'OOP' stand for?", "object oriented programming"),
    ]

    def __init__(self, num_questions: int = 5):
        """Initialize CodeQuiz with num_questions."""
        self.num_questions = min(num_questions, len(self.QUESTIONS))
        self.questions: list[tuple[str, str]] = []
        self.current_index = 0
        self.correct = 0
        self.start_time = 0.0

    def start(self) -> str:
        """Start a new quiz."""
        self.questions = random.sample(self.QUESTIONS, self.num_questions)
        self.current_index = 0
        self.correct = 0
        self.start_time = time.time()
        return f"Code Quiz! {self.num_questions} questions. Let's go!\n\nQ1: {self.questions[0][0]}"

    def answer(self, response: str) -> tuple[str, MiniGameScore | None]:
        """Submit an answer."""
        _question, correct_answer = self.questions[self.current_index]

        is_correct = response.lower().strip() == correct_answer.lower()
        if is_correct:
            self.correct += 1
            feedback = "✓ Correct!"
        else:
            feedback = f"✗ Wrong! Answer: {correct_answer}"

        self.current_index += 1

        if self.current_index >= self.num_questions:
            # Quiz complete
            elapsed = time.time() - self.start_time
            xp = self.correct * self.xp_per_correct
            result = GameResult.WIN if self.correct > self.num_questions // 2 else GameResult.LOSE
            score = MiniGameScore(
                game_name=self.name,
                result=result,
                score=int((self.correct / self.num_questions) * 100),
                time_taken=elapsed,
                attempts=self.num_questions,
                xp_earned=xp,
            )
            return (
                f"{feedback}\n\n📊 Quiz Complete! {self.correct}/{self.num_questions} correct. +{xp}XP",
                score,
            )

        next_q = self.questions[self.current_index][0]
        return f"{feedback}\n\nQ{self.current_index + 1}: {next_q}", None


class ReactionTest:
    """Test your reaction speed."""

    name = "Reaction Test"
    description = "How fast can you react?"
    xp_win = 30

    def __init__(self):
        """Initialize ReactionTest."""
        self.target_number = 0
        self.start_time = 0.0
        self.state = "waiting"

    def start(self) -> str:
        """Start a new test."""
        self.target_number = random.randint(1, 9)
        self.state = "countdown"
        return (
            f"When you see the number {self.target_number}, type it as fast as you can!\nReady..."
        )

    def go(self) -> str:
        """Signal to start timing."""
        self.start_time = time.time()
        self.state = "active"
        # Generate distractor numbers then show target
        distractors = [str(random.randint(1, 9)) for _ in range(random.randint(2, 5))]
        display = (
            " ".join(distractors)
            + f" ➤ {self.target_number} ➤ "
            + " ".join([str(random.randint(1, 9)) for _ in range(random.randint(2, 5))])
        )
        return f"GO! Find the target in: {display}"

    def respond(self, number: int) -> tuple[str, MiniGameScore | None]:
        """Submit response."""
        elapsed = time.time() - self.start_time

        if number == self.target_number:
            if elapsed < 1.0:
                rating = "Lightning fast!"
                score_val = 100
            elif elapsed < 2.0:
                rating = "Quick!"
                score_val = 75
            elif elapsed < 3.0:
                rating = "Not bad!"
                score_val = 50
            else:
                rating = "A bit slow..."
                score_val = 25

            xp = max(5, int(self.xp_win * (1 - elapsed / 5)))
            score = MiniGameScore(
                game_name=self.name,
                result=GameResult.WIN,
                score=score_val,
                time_taken=elapsed,
                xp_earned=xp,
            )
            return f"⚡ {elapsed:.2f}s — {rating} +{xp}XP", score

        score = MiniGameScore(
            game_name=self.name,
            result=GameResult.LOSE,
            score=0,
            time_taken=elapsed,
            xp_earned=0,
        )
        return f"❌ Wrong number! Target was {self.target_number}.", score


class BinaryChallenge:
    """Convert decimal to binary."""

    name = "Binary Challenge"
    description = "Convert numbers to binary"
    xp_per_correct = 20

    def __init__(self, rounds: int = 5):
        """Initialize BinaryChallenge with rounds."""
        self.rounds = rounds
        self.current_round = 0
        self.correct = 0
        self.current_number = 0

    def start(self) -> str:
        """Start challenging."""
        self.current_round = 0
        self.correct = 0
        return self._next_challenge()

    def _next_challenge(self) -> str:
        """Generate next number."""
        self.current_round += 1
        # Increase difficulty with rounds
        max_val = 16 * self.current_round
        self.current_number = random.randint(1, max_val)
        return f"Round {self.current_round}/{self.rounds}: Convert {self.current_number} to binary"

    def answer(self, binary_str: str) -> tuple[str, MiniGameScore | None]:
        """Check binary answer."""
        correct_binary = bin(self.current_number)[2:]  # Remove '0b' prefix

        # Clean input
        clean = binary_str.strip().lstrip("0b")

        is_correct = clean == correct_binary
        if is_correct:
            self.correct += 1
            feedback = f"✓ Correct! {self.current_number} = {correct_binary}"
        else:
            feedback = f"✗ Wrong! {self.current_number} in binary is {correct_binary}"

        if self.current_round >= self.rounds:
            xp = self.correct * self.xp_per_correct
            result = GameResult.WIN if self.correct > self.rounds // 2 else GameResult.LOSE
            score = MiniGameScore(
                game_name=self.name,
                result=result,
                score=int((self.correct / self.rounds) * 100),
                time_taken=0,
                attempts=self.rounds,
                xp_earned=xp,
            )
            return (
                f"{feedback}\n\n📊 Challenge Complete! {self.correct}/{self.rounds} correct. +{xp}XP",
                score,
            )

        return f"{feedback}\n\n{self._next_challenge()}", None


# Game registry
MINI_GAMES: dict[str, type] = {
    "number_guess": NumberGuess,
    "word_scramble": WordScramble,
    "code_quiz": CodeQuiz,
    "reaction_test": ReactionTest,
    "binary_challenge": BinaryChallenge,
}


def list_games() -> list[dict[str, str]]:
    """List all available mini-games."""
    return [
        {"id": gid, "name": cls.name, "description": cls.description}
        for gid, cls in MINI_GAMES.items()
    ]


def create_game(game_id: str) -> object | None:
    """Create a game instance."""
    cls = MINI_GAMES.get(game_id)
    if cls:
        return cls()
    return None


# Quick play functions for terminal use
def quick_number_guess() -> str:
    """Play a quick number guess round."""
    game = NumberGuess()
    output = [game.start()]

    for number in [50, 25, 75, 63, 69, 65, 66]:  # Demo sequence
        msg, score = game.guess(number)
        output.append(f"> {number}")
        output.append(msg)
        if score:
            break

    return "\n".join(output)


def quick_code_quiz() -> str:
    """Play a quick 3-question quiz."""
    game = CodeQuiz(num_questions=3)
    return game.start()


logger.info(f"Terminal mini-games loaded: {len(MINI_GAMES)} games available")
