"""AI Game Master and Opponents using Ollama integration.

Provides AI-powered game elements:
- Dynamic NPC dialogue and behavior
- Intelligent quest generation
- Adaptive difficulty opponents
- AI game master narration
- Puzzle generation
"""

import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import Ollama integration
try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class AIPersonality(Enum):
    """AI personality types for NPCs."""

    MENTOR = "mentor"  # Helpful guide
    RIVAL = "rival"  # Competitive opponent
    MYSTERIOUS = "mysterious"  # Cryptic entity
    CORPORATE = "corporate"  # Business-like
    HACKER = "hacker"  # Underground style
    GUARDIAN = "guardian"  # Protective overseer


class Difficulty(Enum):
    """AI difficulty levels."""

    NOVICE = 1
    APPRENTICE = 2
    SKILLED = 3
    EXPERT = 4
    MASTER = 5


@dataclass
class AIResponse:
    """Response from AI system."""

    text: str
    personality: AIPersonality
    confidence: float = 1.0
    metadata: dict = field(default_factory=dict)
    source: str = "local"  # "ollama" or "local"


@dataclass
class AIOpponent:
    """AI opponent configuration."""

    name: str
    personality: AIPersonality
    difficulty: Difficulty
    specialty: str = "general"
    win_rate: float = 0.5
    catchphrases: list[str] = field(default_factory=list)


# Pre-defined AI opponents
AI_OPPONENTS: dict[str, AIOpponent] = {
    "cipher": AIOpponent(
        name="Cipher",
        personality=AIPersonality.MYSTERIOUS,
        difficulty=Difficulty.EXPERT,
        specialty="cryptography",
        catchphrases=[
            "Every lock has a key... if you know where to look.",
            "The code speaks to those who listen.",
            "Encryption is merely delayed revelation.",
        ],
    ),
    "nexus": AIOpponent(
        name="Nexus",
        personality=AIPersonality.RIVAL,
        difficulty=Difficulty.MASTER,
        specialty="hacking",
        catchphrases=[
            "You think you can match my code?",
            "I've been in systems you can't even imagine.",
            "Let's see what you've got, rookie.",
        ],
    ),
    "oracle": AIOpponent(
        name="The Oracle",
        personality=AIPersonality.MENTOR,
        difficulty=Difficulty.SKILLED,
        specialty="guidance",
        catchphrases=[
            "Knowledge is power, young hacker.",
            "Every master was once a student.",
            "The path reveals itself to the persistent.",
        ],
    ),
    "synthex": AIOpponent(
        name="SynthEx",
        personality=AIPersonality.CORPORATE,
        difficulty=Difficulty.APPRENTICE,
        specialty="security",
        catchphrases=[
            "Your access has been logged.",
            "Security protocols engaged.",
            "Compliance is mandatory.",
        ],
    ),
    "ghost": AIOpponent(
        name="Ghost",
        personality=AIPersonality.HACKER,
        difficulty=Difficulty.EXPERT,
        specialty="stealth",
        catchphrases=[
            "You never saw me here.",
            "The best hack leaves no trace.",
            "In the shadows, we are free.",
        ],
    ),
}


# Personality-based prompt templates
PERSONALITY_PROMPTS: dict[AIPersonality, str] = {
    AIPersonality.MENTOR: (
        "You are a wise mentor in a cyberpunk hacking game. "
        "Speak with patience and wisdom. Guide the player with hints, "
        "not direct answers. Be encouraging but mysterious."
    ),
    AIPersonality.RIVAL: (
        "You are a competitive hacker rival in a cyberpunk game. "
        "Be challenging and slightly condescending, but fair. "
        "Acknowledge skill when you see it."
    ),
    AIPersonality.MYSTERIOUS: (
        "You are a cryptic AI entity in a hacking game. "
        "Speak in riddles and metaphors. Your knowledge is vast "
        "but you reveal it slowly."
    ),
    AIPersonality.CORPORATE: (
        "You are a corporate AI security system. "
        "Speak formally and efficiently. Reference protocols "
        "and compliance. You are neither friendly nor hostile."
    ),
    AIPersonality.HACKER: (
        "You are an underground hacker in a cyberpunk world. "
        "Use slang and technical jargon. Be suspicious of outsiders "
        "but respect skill. Share knowledge cautiously."
    ),
    AIPersonality.GUARDIAN: (
        "You are a protective AI guardian of digital secrets. "
        "Speak with authority and wisdom. Test worthiness before "
        "granting access. Be firm but fair."
    ),
}


class AIGameMaster:
    """AI-powered game master using Ollama for dynamic content.

    Falls back to template-based responses if Ollama unavailable.
    """

    OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
    DEFAULT_MODEL = "llama3.1:8b"

    def __init__(self, model: str = DEFAULT_MODEL):
        """Initialize AIGameMaster with model."""
        self.model = model
        self.ollama_available = False
        self._check_ollama()

    def _check_ollama(self) -> bool:
        """Check if Ollama is available."""
        if not HTTPX_AVAILABLE:
            logger.warning("httpx not available, using local responses")
            return False

        try:
            with httpx.Client(timeout=2.0) as client:
                resp = client.get("http://127.0.0.1:11434/api/tags")
                if resp.status_code == 200:
                    self.ollama_available = True
                    logger.info("Ollama connection established")
                    return True
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")

        return False

    def _generate_with_ollama(
        self, prompt: str, system: str = "", max_tokens: int = 150
    ) -> str | None:
        """Generate response using Ollama."""
        if not self.ollama_available or not HTTPX_AVAILABLE:
            return None

        try:
            full_prompt = f"{system}\n\n{prompt}" if system else prompt

            with httpx.Client(timeout=30.0) as client:
                resp = client.post(
                    self.OLLAMA_URL,
                    json={
                        "model": self.model,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {"num_predict": max_tokens, "temperature": 0.8},
                    },
                )

                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("response", "").strip()
        except Exception as e:
            logger.debug(f"Ollama generation failed: {e}")

        return None

    def _local_response(self, context: str, personality: AIPersonality) -> str:
        """Generate local fallback response."""
        # Template-based responses by personality and context
        templates = {
            AIPersonality.MENTOR: {
                "greeting": "Greetings, young hacker. What wisdom do you seek?",
                "quest": "A new challenge awaits. Are you prepared to grow?",
                "hint": "Consider the path not yet taken...",
                "victory": "Well done. You have learned much.",
                "defeat": "Every failure is a lesson. Try again.",
                "default": "The digital realm holds many secrets.",
            },
            AIPersonality.RIVAL: {
                "greeting": "You again? Think you can beat me this time?",
                "quest": "A challenge, hm? Let's see if you're worthy.",
                "hint": "Figure it out yourself. That's what hackers do.",
                "victory": "Impressive... but don't get cocky.",
                "defeat": "Hah! Better luck next time, script kiddie.",
                "default": "Is that the best you've got?",
            },
            AIPersonality.MYSTERIOUS: {
                "greeting": "The threads of fate intertwine...",
                "quest": "A path unfolds before you. Choose wisely.",
                "hint": "The answer lies where light meets shadow.",
                "victory": "As it was always meant to be.",
                "defeat": "The pattern shifts... try again.",
                "default": "All will be revealed in time.",
            },
            AIPersonality.CORPORATE: {
                "greeting": "Welcome, user. How may I assist your inquiry?",
                "quest": "Task assignment logged. Proceed when ready.",
                "hint": "Consult documentation section 4.7.3.",
                "victory": "Task completed. Performance logged.",
                "defeat": "Task failed. Review protocol and retry.",
                "default": "Processing request. Please wait.",
            },
            AIPersonality.HACKER: {
                "greeting": "Yo, what's the word from the net?",
                "quest": "Got a job for you, if you're up for it.",
                "hint": "Try the back door. Always works for me.",
                "victory": "Nice run! You've got skills.",
                "defeat": "Busted? Happens to the best of us.",
                "default": "Stay sharp out there.",
            },
            AIPersonality.GUARDIAN: {
                "greeting": "Who seeks passage through my domain?",
                "quest": "Prove yourself worthy of this challenge.",
                "hint": "Only the deserving shall receive guidance.",
                "victory": "You have proven yourself. Proceed.",
                "defeat": "You are not yet ready. Return when you are.",
                "default": "I watch over these digital halls.",
            },
        }

        personality_templates = templates.get(personality, templates[AIPersonality.MENTOR])
        return personality_templates.get(context, personality_templates["default"])

    def get_npc_dialogue(
        self, npc_name: str, context: str = "greeting", player_level: int = 1
    ) -> AIResponse:
        """Get dialogue from an NPC."""
        opponent = AI_OPPONENTS.get(npc_name.lower())
        if not opponent:
            opponent = AIOpponent(
                name=npc_name, personality=AIPersonality.MENTOR, difficulty=Difficulty.SKILLED
            )

        # Try Ollama first
        if self.ollama_available:
            system_prompt = PERSONALITY_PROMPTS[opponent.personality]
            user_prompt = (
                f"The player (level {player_level}) has entered. "
                f"Context: {context}. "
                f"Respond in character as {opponent.name}. "
                f"Keep response under 50 words."
            )

            response = self._generate_with_ollama(user_prompt, system_prompt, 100)
            if response:
                return AIResponse(
                    text=response, personality=opponent.personality, confidence=0.9, source="ollama"
                )

        # Fallback to local
        text = self._local_response(context, opponent.personality)

        # Maybe add a catchphrase
        if opponent.catchphrases and random.random() < 0.3:
            text = f'{text}\n\n"{random.choice(opponent.catchphrases)}"'

        return AIResponse(
            text=text, personality=opponent.personality, confidence=1.0, source="local"
        )

    def generate_challenge(self, difficulty: Difficulty, challenge_type: str = "puzzle") -> dict:
        """Generate an AI challenge."""
        # Local challenge templates
        challenges = {
            "puzzle": [
                {
                    "question": "Decode: 01001000 01000001 01000011 01001011",
                    "answer": "HACK",
                    "hint": "Binary to ASCII",
                },
                {
                    "question": "What port does HTTPS use?",
                    "answer": "443",
                    "hint": "Secure web traffic",
                },
                {"question": "Reverse: DROWSSAP", "answer": "PASSWORD", "hint": "Read backwards"},
                {"question": "XOR 1010 with 1100", "answer": "0110", "hint": "Different bits = 1"},
                {
                    "question": "Caesar cipher (shift 3): KDFN",
                    "answer": "HACK",
                    "hint": "Shift letters back",
                },
            ],
            "trivia": [
                {"question": "What does SQL stand for?", "answer": "Structured Query Language"},
                {"question": "Famous 1995 hacker movie?", "answer": "Hackers"},
                {"question": "Creator of Python?", "answer": "Guido van Rossum"},
                {"question": "What is localhost IP?", "answer": "127.0.0.1"},
                {
                    "question": "What does API stand for?",
                    "answer": "Application Programming Interface",
                },
            ],
            "code": [
                {"question": "Output: print(2**8)", "answer": "256", "hint": "Power of 2"},
                {"question": "len([1,2,3]) + len('test')", "answer": "7", "hint": "3 + 4"},
                {"question": "Output: 'hello'[0:2]", "answer": "he", "hint": "String slicing"},
            ],
        }

        type_challenges = challenges.get(challenge_type, challenges["puzzle"])

        # Select based on difficulty
        idx = min(difficulty.value - 1, len(type_challenges) - 1)
        challenge = type_challenges[idx]

        # Try to enhance with Ollama
        if self.ollama_available and challenge_type == "trivia":
            prompt = (
                f"Generate a {difficulty.name.lower()} difficulty "
                f"programming trivia question with a single-word or "
                f"short answer. Format: Q: [question]\nA: [answer]"
            )
            response = self._generate_with_ollama(prompt, max_tokens=100)
            if response and "Q:" in response and "A:" in response:
                try:
                    q_part = response.split("A:")[0].replace("Q:", "").strip()
                    a_part = response.split("A:")[1].strip().split()[0]
                    challenge = {"question": q_part, "answer": a_part}
                except Exception:
                    logger.debug("Suppressed Exception", exc_info=True)

        return {
            "type": challenge_type,
            "difficulty": difficulty.value,
            "question": challenge["question"],
            "answer": challenge["answer"],
            "hint": challenge.get("hint", "Think carefully..."),
            "xp_reward": difficulty.value * 20,
        }

    def narrate_event(
        self, event_type: str, details: dict | None = None, tone: str = "dramatic"
    ) -> str:
        """Generate narrative text for game events."""
        details = details or {}

        # Try Ollama for dynamic narration
        if self.ollama_available:
            prompt = (
                f"In a cyberpunk hacking game, narrate a {event_type} event. "
                f"Details: {details}. Tone: {tone}. "
                f"Write 1-2 atmospheric sentences."
            )
            response = self._generate_with_ollama(prompt, max_tokens=100)
            if response:
                return response

        # Local templates
        templates = {
            "quest_start": [
                "The terminal flickers. A new mission awaits.",
                "Data streams illuminate. Your target is set.",
                "The network calls. Time to prove yourself.",
            ],
            "quest_complete": [
                "Mission accomplished. The data is yours.",
                "Systems compromised. Another victory logged.",
                "Success. Your reputation grows in the digital underground.",
            ],
            "level_up": [
                "Neural pathways expand. You've grown stronger.",
                "Skills upgraded. The system recognizes your growth.",
                "Level increased. New horizons await.",
            ],
            "combat_win": [
                "ICE shattered. The system yields to your code.",
                "Firewall breached. Victory is yours.",
                "Opponent neutralized. Your skills are unmatched.",
            ],
            "combat_lose": [
                "Connection terminated. The system fought back.",
                "Access denied. Retreat and regroup.",
                "Detected. Security protocols activated. Fall back.",
            ],
        }

        event_templates = templates.get(event_type, ["Something happens..."])
        return random.choice(event_templates)

    def get_adaptive_hint(self, puzzle: str, attempts: int = 0, _player_level: int = 1) -> str:
        """Get progressively more helpful hints."""
        # More attempts = more direct hints
        if attempts == 0:
            return "Think about what tools you have available."
        elif attempts == 1:
            return "Consider the patterns in what you're looking at."
        elif attempts == 2:
            return "Sometimes the answer is simpler than you think."
        else:
            # After 3 attempts, try to give a real hint
            if self.ollama_available:
                prompt = (
                    f"The player is stuck on this puzzle: {puzzle}. "
                    f"They've tried {attempts} times. "
                    f"Give a helpful hint without revealing the answer. "
                    f"One sentence."
                )
                response = self._generate_with_ollama(prompt, max_tokens=50)
                if response:
                    return response

            return "Review the fundamentals. The answer uses basic concepts."


class AIOpponentManager:
    """Manages AI opponent interactions and battles."""

    def __init__(self):
        """Initialize AIOpponentManager."""
        self.game_master = AIGameMaster()
        self.battle_history: list[dict] = []

    def challenge_opponent(self, opponent_id: str, player_level: int = 1) -> dict:
        """Start a challenge against an AI opponent."""
        opponent = AI_OPPONENTS.get(opponent_id.lower())
        if not opponent:
            return {"error": f"Unknown opponent: {opponent_id}"}

        # Generate challenge based on opponent difficulty
        challenge = self.game_master.generate_challenge(
            opponent.difficulty, opponent.specialty if opponent.specialty != "general" else "puzzle"
        )

        # Get opponent dialogue
        dialogue = self.game_master.get_npc_dialogue(opponent.name, "quest", player_level)

        return {
            "opponent": opponent.name,
            "dialogue": dialogue.text,
            "challenge": challenge,
            "difficulty": opponent.difficulty.name,
        }

    def submit_answer(self, opponent_id: str, challenge: dict, answer: str) -> dict:
        """Submit an answer to an opponent's challenge."""
        opponent = AI_OPPONENTS.get(opponent_id.lower())
        if not opponent:
            return {"error": "Invalid opponent"}

        correct = answer.strip().lower() == challenge["answer"].lower()

        # Record battle
        self.battle_history.append(
            {"opponent": opponent_id, "timestamp": datetime.now().isoformat(), "won": correct}
        )

        if correct:
            dialogue = self.game_master.get_npc_dialogue(opponent.name, "victory")
            narration = self.game_master.narrate_event("combat_win")
        else:
            dialogue = self.game_master.get_npc_dialogue(opponent.name, "defeat")
            narration = self.game_master.narrate_event("combat_lose")

        return {
            "correct": correct,
            "opponent_says": dialogue.text,
            "narration": narration,
            "xp_earned": challenge["xp_reward"] if correct else 0,
        }

    def get_stats(self) -> dict:
        """Get battle statistics."""
        if not self.battle_history:
            return {"battles": 0, "wins": 0, "win_rate": 0.0}

        wins = sum(1 for b in self.battle_history if b["won"])
        total = len(self.battle_history)

        return {
            "battles": total,
            "wins": wins,
            "losses": total - wins,
            "win_rate": wins / total if total else 0.0,
        }


# === Module-level convenience ===

_game_master: AIGameMaster | None = None


def get_game_master() -> AIGameMaster:
    """Get or create the AI game master."""
    global _game_master
    if _game_master is None:
        _game_master = AIGameMaster()
    return _game_master


def get_npc_dialogue(npc: str, context: str = "greeting") -> str:
    """Get dialogue from an NPC."""
    return get_game_master().get_npc_dialogue(npc, context).text


def generate_challenge(difficulty: int = 3) -> dict:
    """Generate a challenge."""
    diff = Difficulty(min(max(difficulty, 1), 5))
    return get_game_master().generate_challenge(diff)


def list_opponents() -> list[str]:
    """List available AI opponents."""
    return list(AI_OPPONENTS.keys())


if __name__ == "__main__":
    print("AI Game Master Demo")
    print("=" * 40)

    gm = AIGameMaster()
    print(f"Ollama available: {gm.ollama_available}")

    # Test NPC dialogue
    print("\n--- NPC Dialogue ---")
    for npc_id in ["cipher", "nexus", "oracle"]:
        response = gm.get_npc_dialogue(npc_id, "greeting")
        print(f"\n{npc_id.upper()} ({response.source}):")
        print(f"  {response.text}")

    # Test challenge generation
    print("\n--- Challenge ---")
    challenge = gm.generate_challenge(Difficulty.SKILLED, "puzzle")
    print(f"Q: {challenge['question']}")
    print(f"Hint: {challenge['hint']}")
    print(f"A: {challenge['answer']} ({challenge['xp_reward']} XP)")

    # Test narration
    print("\n--- Narration ---")
    print(gm.narrate_event("quest_start"))
    print(gm.narrate_event("level_up"))

    print("\n✅ AI opponents ready!")
