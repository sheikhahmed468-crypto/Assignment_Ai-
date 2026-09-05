"""StudyMate: a code-first personal productivity AI agent.

The project intentionally uses only Python's standard library so it can be
run locally without API keys or third-party automation platforms.
"""

from __future__ import annotations

import ast
import json
import re
import shlex
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


DATA_FILE = Path(__file__).with_name("agent_data.json")


@dataclass
class Note:
    title: str
    content: str
    created_at: str


@dataclass
class Reminder:
    task: str
    due: str
    completed: bool = False


class StudyMateAgent:
    """Route natural-language commands to eight useful local automations."""

    def __init__(self, data_file: Path = DATA_FILE) -> None:
        self.data_file = data_file
        self.notes: list[Note] = []
        self.reminders: list[Reminder] = []
        self._load()

    # Functionality 1: explain a topic with a concise, structured response.
    def explain(self, topic: str) -> str:
        topic = topic.strip()
        if not topic:
            return "Please provide a topic to explain."
        return (
            f"{topic.title()}\n"
            f"  Definition: {topic} is a concept to investigate by identifying "
            "its purpose, parts, and practical examples.\n"
            "  Study path: define it -> break it into steps -> test it with an example."
        )

    # Functionality 2: safely evaluate arithmetic expressions.
    def calculate(self, expression: str) -> str:
        try:
            tree = ast.parse(expression, mode="eval")
            result = self._evaluate_node(tree.body)
        except (SyntaxError, ValueError, TypeError, ZeroDivisionError):
            return "I could not calculate that. Use numbers and +, -, *, /, //, %, or **."
        return f"{expression} = {result:g}" if isinstance(result, float) else f"{expression} = {result}"

    def _evaluate_node(self, node: ast.AST) -> int | float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = self._evaluate_node(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and isinstance(
            node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)
        ):
            left = self._evaluate_node(node.left)
            right = self._evaluate_node(node.right)
            operations = {
                ast.Add: lambda: left + right,
                ast.Sub: lambda: left - right,
                ast.Mult: lambda: left * right,
                ast.Div: lambda: left / right,
                ast.FloorDiv: lambda: left // right,
                ast.Mod: lambda: left % right,
                ast.Pow: lambda: left**right,
            }
            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise ValueError("exponent is too large")
            return operations[type(node.op)]()
        raise ValueError("unsupported expression")

    # Functionality 3: convert common units.
    def convert(self, amount: float, source: str, target: str) -> str:
        source, target = source.lower(), target.lower()
        conversions = {
            ("km", "miles"): lambda value: value * 0.621371,
            ("miles", "km"): lambda value: value / 0.621371,
            ("kg", "lb"): lambda value: value * 2.20462,
            ("lb", "kg"): lambda value: value / 2.20462,
            ("c", "f"): lambda value: value * 9 / 5 + 32,
            ("f", "c"): lambda value: (value - 32) * 5 / 9,
            ("hours", "minutes"): lambda value: value * 60,
            ("minutes", "hours"): lambda value: value / 60,
        }
        try:
            result = conversions[(source, target)](amount)
        except KeyError:
            return "Supported conversions: km/miles, kg/lb, C/F, and hours/minutes."
        return f"{amount:g} {source} = {result:.2f} {target}"

    # Functionality 4: create and search persistent notes.
    def add_note(self, title: str, content: str) -> str:
        self.notes.append(Note(title.strip(), content.strip(), datetime.now().isoformat(timespec="seconds")))
        self._save()
        return f"Saved note: {title.strip()}"

    def search_notes(self, query: str) -> str:
        matches = [note for note in self.notes if query.lower() in f"{note.title} {note.content}".lower()]
        if not matches:
            return "No matching notes found."
        return "\n".join(f"- {note.title}: {note.content}" for note in matches)

    # Functionality 5: create and list persistent reminders.
    def add_reminder(self, task: str, due: str) -> str:
        self.reminders.append(Reminder(task.strip(), due.strip()))
        self._save()
        return f"Reminder created: {task.strip()} ({due.strip()})"

    def list_reminders(self) -> str:
        if not self.reminders:
            return "No reminders yet."
        return "\n".join(
            f"{index}. [{'x' if reminder.completed else ' '}] {reminder.task} - {reminder.due}"
            for index, reminder in enumerate(self.reminders, start=1)
        )

    # Functionality 6: summarize text using sentence ranking by word frequency.
    def summarize(self, text: str, sentence_count: int = 2) -> str:
        sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text.strip()) if sentence.strip()]
        if len(sentences) <= sentence_count:
            return " ".join(sentences)
        words = re.findall(r"[A-Za-z']+", text.lower())
        stop_words = {"the", "a", "an", "and", "of", "to", "in", "is", "it", "for", "on", "that", "with"}
        frequencies: dict[str, int] = {}
        for word in words:
            if word not in stop_words:
                frequencies[word] = frequencies.get(word, 0) + 1
        ranked = sorted(
            enumerate(sentences),
            key=lambda item: sum(frequencies.get(word, 0) for word in re.findall(r"[A-Za-z']+", item[1].lower())),
            reverse=True,
        )
        selected = {index for index, _ in ranked[:sentence_count]}
        return " ".join(sentence for index, sentence in enumerate(sentences) if index in selected)

    # Functionality 7: generate a short revision quiz from a topic bank.
    def quiz(self, topic: str) -> str:
        question_banks = {
            "python": [
                "What keyword defines a function in Python?",
                "Which data type stores an ordered, mutable collection?",
                "What does a for loop commonly iterate over?",
            ],
            "computing": [
                "What does CPU stand for?",
                "What is the purpose of an operating system?",
                "What does an algorithm provide?",
            ],
            "business": [
                "What is a target market?",
                "What does a budget help an organisation control?",
                "What is the purpose of customer feedback?",
            ],
        }
        questions = question_banks.get(topic.strip().lower())
        if questions is None:
            return "No quiz bank found. Try: python, computing, or business."
        return f"{topic.title()} revision quiz:\n" + "\n".join(
            f"{index}. {question}" for index, question in enumerate(questions, start=1)
        )

    # Functionality 8: rank tasks using transparent urgency and importance signals.
    def prioritize(self, tasks: list[str]) -> str:
        if not tasks:
            return "Provide tasks separated with |."
        urgent_words = {"urgent", "today", "deadline", "due", "exam", "submit"}
        important_words = {"important", "report", "assignment", "project", "study"}

        def score(task: str) -> tuple[int, int]:
            words = set(re.findall(r"[a-z]+", task.lower()))
            return (len(words & urgent_words) * 2 + len(words & important_words), -len(task))

        ranked = sorted(enumerate(tasks), key=lambda item: score(item[1]), reverse=True)
        return "Priority order:\n" + "\n".join(
            f"{index}. {task.strip()} (score {score(task)[0]})"
            for index, (_, task) in enumerate(ranked, start=1)
        )

    def handle(self, command: str) -> str:
        """Interpret a simple command language suitable for a terminal demo."""
        try:
            parts = shlex.split(command)
        except ValueError:
            return "Could not read that command. Check quotation marks."
        if not parts:
            return "Enter a command. Type 'help' to see options."
        action = parts[0].lower()
        try:
            if action == "explain":
                return self.explain(" ".join(parts[1:]))
            if action == "calculate":
                return self.calculate(" ".join(parts[1:]))
            if action == "convert" and len(parts) == 4:
                return self.convert(float(parts[1]), parts[2], parts[3])
            if action == "note" and len(parts) >= 3:
                return self.add_note(parts[1], " ".join(parts[2:]))
            if action == "search" and len(parts) >= 2:
                return self.search_notes(" ".join(parts[1:]))
            if action == "remind" and len(parts) >= 3:
                return self.add_reminder(" ".join(parts[1:-1]), parts[-1])
            if action == "reminders":
                return self.list_reminders()
            if action == "summarize":
                return self.summarize(" ".join(parts[1:]))
            if action == "quiz":
                return self.quiz(" ".join(parts[1:]))
            if action == "prioritize" and len(parts) >= 2:
                return self.prioritize(" ".join(parts[1:]).split("|"))
            if action == "help":
                return self.help_text()
        except (ValueError, IndexError):
            pass
        return "Invalid command. Type 'help' to see the correct format."

    @staticmethod
    def help_text() -> str:
        return """Commands:
  explain <topic>
  calculate <expression>
  convert <amount> <from> <to>
  note <title> <content>
  search <keywords>
  remind <task> <due date>
  reminders
  summarize <text>
    quiz <topic>
    prioritize <task 1> | <task 2> | <task 3>
  help / quit"""

    def _load(self) -> None:
        if not self.data_file.exists():
            return
        try:
            data: dict[str, Any] = json.loads(self.data_file.read_text(encoding="utf-8"))
            self.notes = [Note(**item) for item in data.get("notes", [])]
            self.reminders = [Reminder(**item) for item in data.get("reminders", [])]
        except (OSError, json.JSONDecodeError, TypeError):
            self.notes, self.reminders = [], []

    def _save(self) -> None:
        data = {"notes": [asdict(note) for note in self.notes], "reminders": [asdict(item) for item in self.reminders]}
        self.data_file.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> None:
    agent = StudyMateAgent()
    print("StudyMate Agent | Type 'help' for commands, 'quit' to exit.")
    while True:
        try:
            command = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        if command.lower() in {"quit", "exit"}:
            print("Goodbye!")
            break
        print(f"Agent: {agent.handle(command)}")


if __name__ == "__main__":
    main()