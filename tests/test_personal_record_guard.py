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
            "Semester berapa yang sebaiknya saya ambil untuk program MBKM?",
        )

        for question in questions:
            with self.subTest(question=question):
                self.assertIsNone(
                    chatbot.get_personal_record_refusal(question, "regular")
                )

    def test_parent_cannot_request_a_childs_private_academic_record(self):
        response = chatbot.get_personal_record_refusal(
            "Semester anak saya sekarang berapa?",
            "regular",
        )

        self.assertIn("tidak dapat mengakses", response)
        self.assertIn("UII Gateway/UIIRAS", response)


class SessionIdentityTests(unittest.TestCase):
    def setUp(self):
        self.client = chatbot.app.test_client()

    def test_explicit_name_is_preserved_in_indonesian_and_english_introductions(self):
        examples = (
            ("Saya Daviarr XyZ, mahasiswa Informatika.", "Daviarr XyZ"),
            ("My name is Daviarr XyZ, and I study Informatics.", "Daviarr XyZ"),
        )

        for introduction, expected_name in examples:
            with self.subTest(introduction=introduction):
                identity, name_to_redact = chatbot.identify_user(introduction)
                self.assertEqual(identity["preferred_name"], expected_name)
                self.assertEqual(name_to_redact, expected_name)
                self.assertNotIn(
                    expected_name,
                    chatbot.redact_personal_name(introduction, [name_to_redact]),
                )

    @patch.object(chatbot, "get_groq_response", return_value="Jadwal tersedia di panduan.")
    @patch.object(
        chatbot.collection,
        "query",
        return_value={"documents": [["Panduan Key-In"]], "metadatas": [[{"file": "guide.json"}]]},
    )
    def test_student_name_is_greeted_verbatim_and_redacted_from_model_input(
        self, retrieve, generate
    ):
        response = self.client.post(
            "/chat",
            json={
                "query": "Saya Daviarr XyZ, mahasiswa Informatika angkatan 2023. Kapan Key-In?",
                "mode": "regular",
                "conversation_history": [],
            },
        )

        body = response.get_json()
        self.assertEqual(body["greeting"], "Halo, Daviarr XyZ.")
        self.assertEqual(body["session_context"]["preferred_name"], "Daviarr XyZ")
        self.assertNotIn("Daviarr XyZ", generate.call_args.args[0])
        self.assertNotIn("Daviarr XyZ", retrieve.call_args.kwargs["query_texts"][0])

    @patch.object(chatbot, "get_groq_response", return_value="Jadwal tersedia di panduan.")
    @patch.object(
        chatbot.collection,
        "query",
        return_value={"documents": [["Panduan Key-In"]], "metadatas": [[{"file": "guide.json"}]]},
    )
    def test_parent_is_greeted_without_repeating_child_name(self, retrieve, generate):
        response = self.client.post(
            "/chat",
            json={
                "query": "Saya orang tua dari Daviar, bagaimana jadwal Key-In Ganjil 2026/2027?",
                "mode": "regular",
                "conversation_history": [],
            },
        )

        body = response.get_json()
        self.assertEqual(body["greeting"], "Baik, Bapak/Ibu.")
        self.assertEqual(body["session_context"], {"role": "parent"})
        self.assertNotIn("Daviar", generate.call_args.args[0])
        self.assertNotIn("Daviar", retrieve.call_args.kwargs["query_texts"][0])

    @patch.object(chatbot, "get_groq_response")
    @patch.object(chatbot.collection, "query")
    def test_parent_private_record_question_is_refused_without_model_call(
        self, retrieve, generate
    ):
        response = self.client.post(
            "/chat",
            json={
                "query": "Saya orang tua dari Daviar. Semester anak saya sekarang berapa?",
                "mode": "ip",
                "conversation_history": [],
            },
        )

        body = response.get_json()
        self.assertEqual(body["greeting"], "Hello, and thank you for reaching out.")
        self.assertIn("student's semester", body["answer"])
        retrieve.assert_not_called()
        generate.assert_not_called()

    @patch.object(chatbot, "get_groq_response", return_value="Silakan lihat panduan.")
    @patch.object(
        chatbot.collection,
        "query",
        return_value={"documents": [["Panduan Key-In"]], "metadatas": [[{"file": "guide.json"}]]},
    )
    def test_session_name_is_remembered_but_not_repeated_or_sent_to_model(
        self, retrieve, generate
    ):
        response = self.client.post(
            "/chat",
            json={
                "query": "Bagaimana dengan jadwal Key-In?",
                "mode": "regular",
                "session_context": {
                    "role": "student",
                    "preferred_name": "Daviarr XyZ",
                },
                "conversation_history": [
                    {"role": "user", "content": "Saya Daviarr XyZ, mahasiswa Informatika."}
                ],
            },
        )

        body = response.get_json()
        self.assertNotIn("greeting", body)
        self.assertEqual(body["session_context"]["preferred_name"], "Daviarr XyZ")
        self.assertNotIn("Daviarr XyZ", generate.call_args.args[0])
        self.assertNotIn(
            "Daviarr XyZ",
            generate.call_args.args[2][0]["content"],
        )


if __name__ == "__main__":
    unittest.main()
