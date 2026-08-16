import unittest

from recoup import FailedClosed, choose_message_from_feedback


class TeracFeedbackTest(unittest.TestCase):
    def test_feedback_is_required_before_message_selection(self):
        with self.assertRaises(FailedClosed):
            choose_message_from_feedback([])
        feedback = [{"preference": "deadline" if index < 3 else "current", "trust_current": 3, "trust_deadline": 4} for index in range(5)]
        result = choose_message_from_feedback(feedback)
        self.assertEqual(result["message_variant"], "deadline")
        self.assertEqual(result["human_feedback"]["responses"], 5)


if __name__ == "__main__":
    unittest.main()
