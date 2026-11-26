import unittest
from unittest.mock import patch

import app as chatbot


REGULAR_PACKAGE_2026 = (
    "Paket semester 1 angkatan 2026 terdiri dari Pendidikan Agama Islam (2 SKS), "
    "Pendidikan Pancasila (2 SKS), Pemikiran Desain (4 SKS), Fundamen Matematika "
    "(6 SKS), Fundamen Informatika (3 SKS), dan Logika Pemrograman (3 SKS), total 20 SKS."
)
IP_PACKAGE_2026 = (
    "The first-semester package for the 2026 cohort consists of six courses, "
    "for a total of 20 credits (SKS)."
)


class CoursePackageScopeTests(unittest.TestCase):
    def test_extracts_indonesian_and_english_cohort_scopes(self):
        examples = (
            ("Apa saja mata kuliah paket semester 1 angkatan 2026?", (2026, 1)),
            ("Paket mata kuliah semester pertama untuk cohort 2026?", (2026, 1)),
            ("Which courses are in the first-semester package for the 2026 cohort?", (2026, 1)),
            ("What is the course package for semester 1, cohort 2040?", (2040, 1)),
        )

        for question, expected in examples:
            with self.subTest(question=question):
                self.assertEqual(
                    chatbot.extract_course_package_scope(question),
                    expected,
                )

    def test_does_not_handle_questions_without_explicit_cohort(self):
        self.assertIsNone(
            chatbot.extract_course_package_scope(
                "Apa saja mata kuliah paket semester 1?"
            )
        )
        self.assertIsNone(
            chatbot.extract_course_package_scope(
                "Kapan jadwal Key-In angkatan 2026?"
            )
        )


class CoursePackageRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = chatbot.app.test_client()

    def test_known_cohort_package_is_returned_without_llm(self):
        metadata = {
            "answer_regular": REGULAR_PACKAGE_2026,
            "answer_ip": IP_PACKAGE_2026,
            "source": "KnowledgeBasePanduanKeyIn",
            "file": "keyin_ganjil2627.json",
            "question": "Apa saja mata kuliah paket semester 1 untuk mahasiswa angkatan 2026?",
        }

        for mode, expected_answer in (
            ("regular", REGULAR_PACKAGE_2026),
            ("ip", IP_PACKAGE_2026),
        ):
            with self.subTest(mode=mode):
                with patch.object(
                    chatbot.collection,
                    "get",
                    return_value={"metadatas": [metadata]},
                ) as lookup, patch.object(chatbot, "get_groq_response") as generate:
                    response = self.client.post(
                        "/chat",
                        json={
                            "query": "Apa saja mata kuliah paket semester 1 angkatan 2026?",
                            "mode": mode,
                        },
                    )

                body = response.get_json()
                self.assertEqual(response.status_code, 200)
                self.assertEqual(body["answer"], expected_answer)
                self.assertEqual(body["sources"][0]["file"], "keyin_ganjil2627.json")
                lookup.assert_called_once()
                generate.assert_not_called()

    def test_unknown_cohort_is_not_answered_from_another_cohort(self):
        with patch.object(
            chatbot.collection,
            "get",
            return_value={"metadatas": []},
        ) as lookup, patch.object(chatbot, "get_groq_response") as generate, patch.object(
            chatbot.collection, "query"
        ) as retrieve:
            response = self.client.post(
                "/chat",
                json={
                    "query": "Apa saja mata kuliah paket semester 1 angkatan 2040?",
                    "mode": "regular",
                },
            )

        body = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertIn("angkatan 2040", body["answer"])
        self.assertIn("tidak dapat menganggap paketnya sama", body["answer"])
        self.assertEqual(body["sources"], [])
        lookup.assert_called_once()
        generate.assert_not_called()
        retrieve.assert_not_called()

    def test_package_question_without_semester_asks_for_clarification(self):
        with patch.object(chatbot.collection, "get") as lookup, patch.object(
            chatbot, "get_groq_response"
        ) as generate:
            response = self.client.post(
                "/chat",
                json={
                    "query": "Apa paket mata kuliah angkatan 2040?",
                    "mode": "regular",
                },
            )

        self.assertIn("semester berapa", response.get_json()["answer"])
        lookup.assert_not_called()
        generate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
