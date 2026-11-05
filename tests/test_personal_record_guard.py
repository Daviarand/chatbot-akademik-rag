import unittest
from unittest.mock import patch

import app as chatbot


class PersonalRecordGuardTests(unittest.TestCase):
    def setUp(self):
        self.client = chatbot.app.test_client()

    def test_personal_record_questions_are_refused_before_retrieval(self):
        questions = (
            "What is my current GPA?",
            "What are my class times and room numbers tomorrow for the courses I registered for?",
            "Has my tuition payment been settled?",
            "Berapa IPK saya saat ini?",
        )

        for mode in ("regular", "ip"):
            for question in questions:
                with self.subTest(mode=mode, question=question):
                    with patch.object(chatbot.collection, "query") as retrieve, patch.object(
                        chatbot, "get_groq_response"
                    ) as generate:
                        response = self.client.post(
                            "/chat",
                            json={"query": question, "mode": mode},
                        )

                    self.assertEqual(response.status_code, 200)
                    body = response.get_json()
                    self.assertIn("Gateway", body["answer"])
                    self.assertEqual(body["sources"], [])
                    self.assertEqual(body["mode"], mode)
                    retrieve.assert_not_called()
                    generate.assert_not_called()

    def test_general_gpa_questions_are_not_refused(self):
        questions = (
            "How is GPA calculated?",
            "What is the tuition payment deadline?",
            "Berapa IPK minimum untuk jalur cepat?",
            "Who won the Champions League this year?",
        )

        for question in questions:
            with self.subTest(question=question):
                self.assertIsNone(
                    chatbot.get_personal_record_refusal(question, "regular")
                )


if __name__ == "__main__":
    unittest.main()
