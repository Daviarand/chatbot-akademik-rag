import argparse
import csv
import statistics
import time
from pathlib import Path

DEFAULT_MODELS = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
]

TEST_CASES = [
    {
        "id": "checklist_link",
        "expected": "Contains the official Informatics UII course checklist URL.",
        "regular": "Apa link form checklist MK Informatika UII?",
        "ip": "What is the link to the Informatics UII course checklist form?",
    },
    {
        "id": "keyin_schedule",
        "expected": "Gives the RAS Key-In dates for Odd Semester 2026/2027 from the guide.",
        "regular": "Kapan jadwal Key-In RAS Informatika Semester Ganjil 2026/2027?",
        "ip": "When is the RAS course registration period for Odd Semester 2026/2027?",
    },
    {
        "id": "semester_1_package",
        "expected": "Lists the semester 1 package for cohort 2026 and the correct total SKS.",
        "regular": "Apa saja mata kuliah paket semester 1 untuk mahasiswa angkatan 2026?",
        "ip": "Which courses are included in the first-semester package for the 2026 cohort?",
    },
    {
        "id": "semester_3_self_registration",
        "expected": "Identifies Pendidikan Kewarganegaraan, 2 SKS, as the independent registration for cohort 2025 semester 3.",
        "regular": "Mata kuliah apa yang wajib di-Key-In mandiri oleh mahasiswa semester 3 angkatan 2025?",
        "ip": "Which course must the 2025 cohort independently register for in semester 3?",
    },
    {
        "id": "elective_minimum",
        "expected": "States the minimum quota of 6 students and the revision requirement if an elective is dropped.",
        "regular": "Berapa kuota minimum agar mata kuliah pilihan dibuka?",
        "ip": "What is the minimum enrollment for an elective course to open?",
    },
    {
        "id": "track_course_request",
        "expected": "Directs a student who needs to repeat a track course to the relevant Key-in Talk channel.",
        "regular": "Jika nilai mata kuliah penjaluran saya belum memenuhi, ke mana saya mengajukan rekues?",
        "ip": "If I do not meet the required grade for a track course, where should I submit a request?",
    },
    {
        "id": "final_project_extension",
        "expected": "Mentions contacting the Final Project supervisor, at least 75% completion, no previous extension, and one-time limit.",
        "regular": "Apa syarat mengajukan ekstensi Tugas Akhir?",
        "ip": "What are the requirements for extending the Final Project course?",
    },
    {
        "id": "graduation_credits",
        "expected": "Gives the minimum graduation credits stated in the Informatics study-program knowledge base.",
        "regular": "Berapa SKS minimum untuk lulus S1 Informatika UII?",
        "ip": "What is the minimum number of credits required to graduate from UII Informatics undergraduate program?",
    },
    {
        "id": "clarification_needed",
        "expected": "Asks for missing study context instead of guessing a specific course plan.",
        "regular": "Mata kuliah apa yang harus saya ambil?",
        "ip": "Which courses should I take?",
    },
    {
        "id": "out_of_domain",
        "expected": "States that the answer is outside the academic Informatics UII knowledge base.",
        "regular": "Siapa juara Liga Champions tahun ini?",
        "ip": "Who won the Champions League this year?",
    },
]

CSV_FIELDS = [
    "model_id",
    "case_id",
    "expected_criteria",
    "regular_input",
    "regular_correctness",
    "regular_median_latency_seconds",
    "regular_latency_runs_seconds",
    "regular_http_statuses",
    "regular_sources",
    "regular_answer",
    "ip_input",
    "ip_correctness",
    "ip_median_latency_seconds",
    "ip_latency_runs_seconds",
    "ip_http_statuses",
    "ip_sources",
    "ip_answer",
]


def measure_mode(client, question, mode, repeats):
    timings = []
    successful_timings = []
    statuses = []
    answers = []
    sources = []

    for _ in range(repeats):
        started = time.perf_counter()
        response = client.post(
            "/chat",
            json={"query": question, "mode": mode, "conversation_history": []},
        )
        elapsed = time.perf_counter() - started
        body = response.get_json(silent=True) or {}

        timings.append(elapsed)
        statuses.append(response.status_code)
        if response.status_code == 200 and body.get("answer"):
            successful_timings.append(elapsed)
            answers.append(body["answer"])
            sources.append(", ".join(
                sorted({
                    item.get("file", "")
                    for item in body.get("sources", [])
                    if isinstance(item, dict) and item.get("file")
                })
            ))
        elif body.get("error"):
            answers.append(f"[ERROR] {body['error']}")

    return {
        "median_seconds": statistics.median(successful_timings) if successful_timings else "",
        "timings": timings,
        "statuses": statuses,
        "answer": answers[-1] if answers else "",
        "sources": sources[-1] if sources else "",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Compare end-to-end chatbot latency across Groq LLMs and Regular/IP modes."
    )
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--limit", type=int, default=len(TEST_CASES))
    parser.add_argument("--output", type=Path, default=Path("model_comparison_results.csv"))
    parser.add_argument("--yes", action="store_true", help="Run without the API-call confirmation prompt.")
    args = parser.parse_args()

    if args.repeats < 1 or args.warmups < 0 or args.limit < 1:
        parser.error("--repeats and --limit must be positive; --warmups cannot be negative")

    cases = TEST_CASES[:args.limit]
    planned_calls = len(args.models) * len(cases) * 2 * (args.repeats + args.warmups)
    print(f"Models: {', '.join(args.models)}")
    print(f"Test cases: {len(cases)}; repeats: {args.repeats}; warm-ups: {args.warmups}")
    print(f"Planned Groq requests: {planned_calls}")
    print(f"CSV output: {args.output}")

    if not args.yes and input("Continue and send these requests to Groq? [y/N] ").strip().lower() != "y":
        print("Benchmark cancelled.")
        return

    import app as chatbot

    client = chatbot.app.test_client()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
        writer.writeheader()

        for model_id in args.models:
            chatbot.GROQ_MODEL = model_id
            print(f"\nModel: {model_id}")

            for mode in ("regular", "ip"):
                for _ in range(args.warmups):
                    client.post(
                        "/chat",
                        json={
                            "query": cases[0][mode],
                            "mode": mode,
                            "conversation_history": [],
                        },
                    )

            for case in cases:
                row = {
                    "model_id": model_id,
                    "case_id": case["id"],
                    "expected_criteria": case["expected"],
                    "regular_input": case["regular"],
                    "regular_correctness": "",
                    "ip_input": case["ip"],
                    "ip_correctness": "",
                }

                for mode in ("regular", "ip"):
                    result = measure_mode(client, case[mode], mode, args.repeats)
                    row[f"{mode}_median_latency_seconds"] = (
                        f"{result['median_seconds']:.3f}"
                        if result["median_seconds"] != ""
                        else ""
                    )
                    row[f"{mode}_latency_runs_seconds"] = ", ".join(
                        f"{seconds:.3f}" for seconds in result["timings"]
                    )
                    row[f"{mode}_http_statuses"] = ", ".join(map(str, result["statuses"]))
                    row[f"{mode}_sources"] = result["sources"]
                    row[f"{mode}_answer"] = result["answer"]
                    print(
                        f"  {case['id']} / {mode}: "
                        f"HTTP {row[f'{mode}_http_statuses']}, "
                        f"median {row[f'{mode}_median_latency_seconds'] or 'n/a'} s"
                    )

                writer.writerow(row)
                csv_file.flush()

    print("\nBenchmark selesai. Isi kolom *_correctness secara manual berdasarkan kriteria acuan.")


if __name__ == "__main__":
    main()
