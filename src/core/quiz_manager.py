"""Quiz Manager - Handles quiz questions for each planet.
"""
import json
import random
import time
import os


class QuizManager:
    """
    Manages quiz questions for the game:
    - Loads questions from JSON file
    - Selects random subset for each quiz
    - Validates answers
    - Tracks score
    """
    _instance = None

    QUESTIONS_PER_QUIZ = 5  # Number of questions per planet quiz

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(QuizManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.all_questions = {}  # Dict of planet_name -> list of questions
        self.current_quiz = None  # Current active quiz session
        self._load_questions()

    def _load_questions(self):
        """Load all quiz questions from JSON file."""
        try:
            quiz_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "assets", "data", "quiz_questions.json"
            )
            with open(quiz_path, 'r') as f:
                data = json.load(f)
                self.all_questions = data.get("questions", {})
            print(
                f"[QuizManager] Loaded questions for {len(self.all_questions)} planets")
        except Exception as e:
            print(f"[QuizManager] Error loading questions: {e}")
            self.all_questions = {}

    def reload_questions(self):
        """Reload questions from file."""
        self._load_questions()

    def start_quiz(self, planet_name):
        """
        Start a new quiz for the specified planet.
        Returns the quiz session with selected questions.
        """
        questions = self.all_questions.get(planet_name, [])
        if not questions:
            print(f"[QuizManager] No questions available for {planet_name}")
            return None

        # Seed random with current time for true randomization
        random.seed(time.time())
        # Select random subset of questions
        num_questions = min(self.QUESTIONS_PER_QUIZ, len(questions))
        selected = random.sample(questions, num_questions)
        # Shuffle the selected questions order
        random.shuffle(selected)

        self.current_quiz = QuizSession(planet_name, selected)
        print(
            f"[QuizManager] Started quiz for {planet_name} with {num_questions} questions")
        return self.current_quiz

    def get_current_quiz(self):
        """Get the current active quiz session."""
        return self.current_quiz

    def end_quiz(self):
        """End the current quiz and return results."""
        if self.current_quiz:
            results = self.current_quiz.get_results()
            self.current_quiz = None
            return results
        return None

    def has_questions_for_planet(self, planet_name):
        """Check if questions exist for a planet."""
        return planet_name in self.all_questions and len(self.all_questions[planet_name]) > 0

    def get_question_count(self, planet_name):
        """Get total number of questions available for a planet."""
        return len(self.all_questions.get(planet_name, []))


class QuizSession:
    """
    Represents an active quiz session.
    """

    def __init__(self, planet_name, questions):
        self.planet_name = planet_name
        self.questions = questions  # List of question dicts
        self.current_index = 0
        self.answers = []  # List of (question, selected_answer, is_correct)
        self.score = 0
        self.completed = False

    def get_current_question(self):
        """Get the current question."""
        if self.completed or self.current_index >= len(self.questions):
            return None
        return self.questions[self.current_index]

    def get_question_number(self):
        """Get current question number (1-indexed)."""
        return self.current_index + 1

    def get_total_questions(self):
        """Get total number of questions."""
        return len(self.questions)

    def submit_answer(self, answer_index):
        """
        Submit an answer for the current question.
        Returns (is_correct, correct_answer_index, explanation)
        """
        if self.completed:
            return None, None, None

        question = self.get_current_question()
        if question is None:
            return None, None, None

        correct_index = question.get("correct", 0)
        is_correct = (answer_index == correct_index)

        if is_correct:
            self.score += 1

        self.answers.append({
            "question": question["question"],
            "selected": answer_index,
            "correct": correct_index,
            "is_correct": is_correct
        })

        # Move to next question
        self.current_index += 1
        if self.current_index >= len(self.questions):
            self.completed = True

        return is_correct, correct_index, question.get("explanation", "")

    def is_completed(self):
        """Check if all questions have been answered."""
        return self.completed

    def get_score(self):
        """Get current score."""
        return self.score

    def get_percentage(self):
        """Get score as percentage."""
        if not self.questions:
            return 0
        return (self.score / len(self.questions)) * 100

    def passed(self, threshold=60):
        """Check if quiz was passed (default 60% to pass)."""
        return self.get_percentage() >= threshold

    def get_results(self):
        """Get full quiz results."""
        return {
            "planet": self.planet_name,
            "score": self.score,
            "total": len(self.questions),
            "percentage": self.get_percentage(),
            "passed": self.passed(),
            "answers": self.answers
        }
