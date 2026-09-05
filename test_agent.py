import tempfile
import unittest
from pathlib import Path

from agent import StudyMateAgent


class StudyMateAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.agent = StudyMateAgent(Path(self.temp_dir.name) / "data.json")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_all_eight_functionalities(self) -> None:
        self.assertIn("Definition", self.agent.explain("photosynthesis"))
        self.assertEqual(self.agent.calculate("(12 + 8) * 2"), "(12 + 8) * 2 = 40")
        self.assertEqual(self.agent.convert(2, "hours", "minutes"), "2 hours = 120.00 minutes")
        self.assertIn("Saved note", self.agent.add_note("Python", "Review lists"))
        self.assertIn("Python", self.agent.search_notes("lists"))
        self.assertIn("Reminder created", self.agent.add_reminder("Submit report", "Friday"))
        self.assertIn("Submit report", self.agent.list_reminders())
        self.assertIn("important", self.agent.summarize("This is important. This is extra. Important ideas matter. Important work helps."))
        self.assertIn("revision quiz", self.agent.quiz("python"))
        priorities = self.agent.prioritize(["Read a book", "Submit urgent assignment", "Organise desk"])
        self.assertIn("Submit urgent assignment", priorities.splitlines()[1])

    def test_data_persists_between_instances(self) -> None:
        self.agent.add_note("Persisted", "Stored locally")
        restored = StudyMateAgent(self.agent.data_file)
        self.assertIn("Persisted", restored.search_notes("stored"))

    def test_calculator_rejects_code(self) -> None:
        self.assertIn("could not calculate", self.agent.calculate("__import__('os').system('dir')").lower())


if __name__ == "__main__":
    unittest.main()