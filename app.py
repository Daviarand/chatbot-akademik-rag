# import os
# import chromadb
# from chromadb.utils import embedding_functions
# from flask import Flask, request, jsonify
# from flask_cors import CORS
# from dotenv import load_dotenv
# from groq import Groq # Import Groq sebagai pengganti Gemini

# # Konfigurasi Path
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# CHROMA_DATA_PATH = os.path.join(BASE_DIR, "chroma_db")

# # Load variabel dari file .env
# load_dotenv()

# print(f"DEBUG: Key yang terbaca adalah: {os.getenv('GROQ_API_KEY')}")

# # Inisialisasi Client Groq
# client_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

# app = Flask(__name__)
# CORS(app)

# # Inisialisasi ChromaDB (Tetap sama seperti sebelumnya)
# client_chroma = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
# embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
# collection = client_chroma.get_collection(name="akademik_uii", embedding_function=embedding_func)

# def get_groq_response(question, context):
#     # Menggunakan model Llama 3.1 8B yang sangat cepat dan gratis
#     chat_completion = client_groq.chat.completions.create(
#         messages=[
#             {
#                 "role": "system",
#                 "content": f"""Anda adalah asisten akademik untuk Program Studi Informatika, Universitas Islam Indonesia (UII).
#                 Gunakan potongan dokumen berikut untuk menjawab pertanyaan mahasiswa.
#                 Jika jawaban tidak ada dalam dokumen, katakan bahwa Anda tidak memiliki informasi tersebut dalam pedoman resmi dan sarankan untuk menghubungi staf prodi.
                
#                 ATURAN:
#                 1. Jawaban harus ramah, profesional, dan akurat.
#                 2. HANYA gunakan informasi dari konteks di bawah ini.
#                 3. Jangan mengarang informasi.
                
#                 KONTEKS DOKUMEN:
#                 {context}"""
#             },
#             {
#                 "role": "user",
#                 "content": question,
#             }
#         ],
#         model="llama-3.1-8b-instant",
#         temperature=0.2, # Rendah agar jawaban lebih konsisten dan tidak mengarang
#     )
#     return chat_completion.choices[0].message.content

# @app.route('/chat', methods=['POST'])
# def chat():
#     data = request.json
#     user_query = data.get("query", "")
    
#     if not user_query:
#         return jsonify({"error": "Query tidak boleh kosong"}), 400
    
#     # 1. Retrieval: Cari dokumen relevan di ChromaDB (Semantic Similarity)
#     results = collection.query(
#         query_texts=[user_query],
#         n_results=3
#     )
    
#     # Gabungkan hasil pencarian menjadi satu konteks
#     context = "\n\n".join(results['documents'][0])
    
#     # 2. Generation: Kirim ke Groq API
#     try:
#         answer = get_groq_response(user_query, context)
#         return jsonify({
#             "answer": answer,
#             "sources": results['metadatas'][0]
#         })
#     except Exception as e:
#         print(f"ERROR TERDETEKSI: {str(e)}")
#         return jsonify({"error": str(e)}), 500

# if __name__ == "__main__":
#     app.run(host='0.0.0.0', port=5000, debug=True)


















import os
import re
import chromadb
from chromadb.utils import embedding_functions
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from groq import Groq

# Konfigurasi Path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DATA_PATH = os.path.join(BASE_DIR, "chroma_db")

# Load variabel dari file .env
load_dotenv()

# Inisialisasi Client Groq
client_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

app = Flask(__name__)
CORS(app)

# Inisialisasi ChromaDB
client_chroma = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
# Samakan dengan model di ingest.py
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)
try:
    collection = client_chroma.get_collection(name="akademik_uii", embedding_function=embedding_func)
except Exception:
    collection = client_chroma.create_collection(name="akademik_uii", embedding_function=embedding_func)

MODE_ALIASES = {
    "regular": "regular",
    "reg": "regular",
    "indonesia": "regular",
    "indonesian": "regular",
    "ip": "ip",
    "international": "ip",
    "international_program": "ip",
    "internasional": "ip",
    "program_internasional": "ip",
}

MODE_GUIDES = {
    "regular": {
        "label": "Regular",
        "language": "Bahasa Indonesia",
        "instruction": "Jawab dalam Bahasa Indonesia yang jelas dan singkat. Gunakan istilah lokal yang akrab untuk mahasiswa UII seperti 'Key-In', 'DPA', 'Prodi', 'Gateway', 'Sekawan', dan 'Reguler/IP' ketika istilah tersebut relevan."
    },
    "ip": {
        "label": "International Program",
        "language": "Bahasa Inggris",
        "instruction": "Jawab dalam Bahasa Inggris yang jelas dan profesional. Gunakan istilah akademik dan operasional yang umum dipahami dalam konteks internasional, tetapi tetap pertahankan nama resmi seperti 'Key-In', 'DPA', 'Prodi', 'Gateway', 'Sekawan', dan 'International Program' jika nama tersebut merupakan istilah resmi di lingkungan UII."
    }
}

LOCAL_GLOSSARY = {
    "key-in": {
        "regular": "Key-In adalah proses pendaftaran atau penyesuaian mata kuliah yang dilakukan mahasiswa melalui sistem Gateway/UIIRAS.",
        "ip": "Key-In is the course registration and enrollment process conducted through the Gateway/UIIRAS system."
    },
    "dpa": {
        "regular": "DPA = Dosen Pembimbing Akademik.",
        "ip": "DPA = Academic Advisor (faculty advisor)."
    },
    "prodi": {
        "regular": "Prodi = Program Studi.",
        "ip": "Prodi = Study Program."
    },
    "gateway": {
        "regular": "Gateway adalah portal/layanan digital utama yang dipakai mahasiswa untuk kegiatan akademik dan pendaftaran.",
        "ip": "Gateway is the main digital portal used by students for academic services and registration."
    },
    "sekawan": {
        "regular": "Sekawan adalah kelompok/komunitas akademik atau unit pendukung yang berfungsi sebagai lingkungan belajar dan layanan mahasiswa.",
        "ip": "Sekawan refers to the academic peer support group or support community within the student ecosystem."
    },
    "mkwu": {
        "regular": "MKWU = Mata Kuliah Wajib Umum.",
        "ip": "MKWU = General Compulsory Courses."
    },
    "uiiras": {
        "regular": "UIIRAS adalah sistem penjadwalan dan registrasi mata kuliah mahasiswa.",
        "ip": "UIIRAS is the student course registration and scheduling system."
    },
    "regular": {
        "regular": "Regular = jalur Reguler berdasarkan program studi utama.",
        "ip": "Regular = the regular study track."
    },
    "international program": {
        "regular": "International Program = jalur program internasional yang mengikuti format dan kebutuhan akademik khusus.",
        "ip": "International Program = the international study track with its own academic requirements."
    },
    "fakultas": {
        "regular": "Fakultas = unit akademik yang menaungi beberapa program studi.",
        "ip": "Faculty = the academic unit that oversees multiple study programs."
    }
}


def normalize_mode(mode):
    mode_key = str(mode or "regular").strip().lower()
    return MODE_ALIASES.get(mode_key, "regular")


PACKAGE_QUESTION_PATTERN = re.compile(
    r"\b(?:paket|package)\b.*\b(?:mata kuliah|matkul|course|courses|kelas|class)\b"
    r"|\b(?:mata kuliah|matkul|course|courses|kelas|class)\b.*\b(?:paket|package)\b",
    re.IGNORECASE,
)
COHORT_YEAR_PATTERN = re.compile(
    r"\b(?:angkatan|cohort(?:\s+of)?|class\s+of)\s*(20\d{2})\b"
    r"|\b(20\d{2})\s+cohort\b",
    re.IGNORECASE,
)
SEMESTER_PATTERN = re.compile(
    r"\bsemester\s*(?:ke[- ]?)?(?P<number>[1-9]|pertama|kedua|ketiga|keempat|"
    r"kelima|keenam|ketujuh|kedelapan)\b"
    r"|\b(?P<ordinal>first|second|third|fourth|fifth|sixth|seventh|eighth)"
    r"[- ]semester\b",
    re.IGNORECASE,
)
SEMESTER_WORDS = {
    "pertama": 1,
    "kedua": 2,
    "ketiga": 3,
    "keempat": 4,
    "kelima": 5,
    "keenam": 6,
    "ketujuh": 7,
    "kedelapan": 8,
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "fifth": 5,
    "sixth": 6,
    "seventh": 7,
    "eighth": 8,
}


def extract_course_package_scope(question):
    normalized_question = " ".join(str(question or "").split())
    if not PACKAGE_QUESTION_PATTERN.search(normalized_question):
        return None

    cohort_match = COHORT_YEAR_PATTERN.search(normalized_question)
    if not cohort_match:
        return None

    cohort_year = int(cohort_match.group(1) or cohort_match.group(2))
    semester_match = SEMESTER_PATTERN.search(normalized_question)
    semester = None
    if semester_match:
        semester_value = semester_match.group("number") or semester_match.group("ordinal")
        semester = int(semester_value) if semester_value.isdigit() else SEMESTER_WORDS[semester_value.lower()]

    return cohort_year, semester


def resolve_course_package(question, mode):
    scope = extract_course_package_scope(question)
    if scope is None:
        return None

    cohort_year, semester = scope
    if semester is None:
        if normalize_mode(mode) == "ip":
            answer = f"Which semester's course package for the {cohort_year} cohort are you asking about?"
        else:
            answer = f"Paket mata kuliah semester berapa untuk angkatan {cohort_year} yang Anda maksud?"
        return {"answer": answer, "sources": []}

    where = {
        "$and": [
            {"fact_type": {"$eq": "course_package"}},
            {"cohort_year": {"$eq": cohort_year}},
            {"semester": {"$eq": semester}},
        ]
    }
    results = collection.get(where=where, include=["metadatas"])
    metadatas = results.get("metadatas") or []
    if not metadatas:
        if normalize_mode(mode) == "ip":
            answer = (
                f"The available knowledge base does not contain a verified course package "
                f"for semester {semester} of the {cohort_year} cohort. I cannot assume it "
                "matches another cohort; please check the latest official curriculum or "
                "contact the Informatics Study Program."
            )
        else:
            answer = (
                f"Knowledge Base yang tersedia belum memuat paket mata kuliah semester "
                f"{semester} yang terverifikasi untuk angkatan {cohort_year}. Saya tidak "
                "dapat menganggap paketnya sama dengan angkatan lain. Silakan cek kurikulum "
                "resmi terbaru atau hubungi Prodi Informatika."
            )
        return {"answer": answer, "sources": []}

    metadata = metadatas[0]
    answer_field = "answer_ip" if normalize_mode(mode) == "ip" else "answer_regular"
    answer = metadata.get(answer_field)
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError(
            f"Indexed course package for cohort {cohort_year}, semester {semester} "
            f"is missing {answer_field}"
        )

    source = {
        key: metadata[key]
        for key in ("source", "file", "question")
        if metadata.get(key)
    }
    return {"answer": answer, "sources": [source]}


PERSONAL_RECORD_TERMS = (
    r"(?:gpa|ipk|grade|grades|nilai|tuition|payment|fee|spp|ukt|tagihan|"
    r"class times|class schedule|classes?|courses?|schedule|timetable|"
    r"room numbers?|registered courses|enrolled courses|course registration|"
    r"jadwal|kelas|mata kuliah|ruangan|semester|angkatan|academic record)"
)
PERSONAL_RECORD_REFERENCE_PATTERN = re.compile(
    r"\b(?:my|mine|my own|saya|aku|milik saya|punya saya)\s+"
    r"(?:(?:current|currently|personal|saat ini|sekarang)\s+)?"
    + PERSONAL_RECORD_TERMS
    + r"\b|\b"
    + PERSONAL_RECORD_TERMS
    + r"(?:\s+[\w'’-]+){0,2}\s+(?:saya|aku|milik saya|my|mine)\b",
    re.IGNORECASE,
)
FAMILY_MEMBER_PATTERN = r"(?:anak saya|putra saya|putri saya|my child|my son|my daughter)"
FAMILY_RECORD_REFERENCE_PATTERN = re.compile(
    r"\b"
    + FAMILY_MEMBER_PATTERN
    + r"(?:\s+[\w'’-]+){0,4}\s+"
    + PERSONAL_RECORD_TERMS
    + r"\b|\b"
    + PERSONAL_RECORD_TERMS
    + r"(?:\s+[\w'’-]+){0,4}\s+"
    + FAMILY_MEMBER_PATTERN
    + r"\b",
    re.IGNORECASE,
)
PERSONAL_CLAUSE_SEPARATOR_PATTERN = re.compile(
    r"[,;.!?]|\b(?:dan|and)\b",
    re.IGNORECASE,
)

NAME_TOKEN = r"[^\W\d_][\w.'’\-]*(?:\s+[^\W\d_][\w.'’\-]*){0,3}"
PARENT_INTRO_PATTERN = re.compile(
    r"\b(?:saya|aku)\s+(?:adalah\s+)?(?:orang tua|wali)"
    r"(?:\s+dari\s+(?P<child_name>" + NAME_TOKEN + r")(?=\s+(?:mahasiswa|mahasiswi|"
    r"student|dan saya|dan ingin|yang)\b|[,.;!?]|$))?",
    re.IGNORECASE,
)
ENGLISH_PARENT_INTRO_PATTERN = re.compile(
    r"\b(?:i am|i'm|we are|we're)\s+(?:a\s+)?(?:parent|guardian|mother|father)"
    r"(?:\s+of\s+(?P<child_name>" + NAME_TOKEN + r")(?=,|[.;!?]|$))?",
    re.IGNORECASE,
)
STUDENT_NAME_PATTERN = re.compile(
    r"\b(?:saya|aku)\s+(?:(?:bernama|adalah)\s+)?(?P<name>" + NAME_TOKEN + r")"
    r"\s*,?\s+(?:(?:saya|aku)\s+)?(?:adalah\s+)?(?:mahasiswa|mahasiswi)\b",
    re.IGNORECASE,
)
ENGLISH_STUDENT_NAME_PATTERN = re.compile(
    r"\b(?:i am|i'm)\s+(?P<name>" + NAME_TOKEN + r")\s*,?\s+(?:a\s+)?student\b",
    re.IGNORECASE,
)
EXPLICIT_NAME_PATTERN = re.compile(
    r"\b(?:nama saya|my name is)\s+(?P<name>" + NAME_TOKEN + r")"
    r"(?=\s*(?:[,.;!?]|$)|\s+(?:dan saya|and i|mahasiswa|mahasiswi|student|"
    r"ingin|mau|saya)\b)",
    re.IGNORECASE,
)


def get_personal_record_refusal(question, mode):
    normalized_question = " ".join(str(question or "").split())
    clauses = PERSONAL_CLAUSE_SEPARATOR_PATTERN.split(normalized_question)
    if not any(
        PERSONAL_RECORD_REFERENCE_PATTERN.search(clause)
        or FAMILY_RECORD_REFERENCE_PATTERN.search(clause)
        for clause in clauses
    ):
        return None

    if normalize_mode(mode) == "ip":
        return (
            "I cannot access or disclose individual student records, including a "
            "student's semester, GPA, tuition-payment status, or personal class "
            "schedule. Please have the student check their own UII Gateway/UIIRAS account."
        )

    return (
        "Saya tidak dapat mengakses atau membagikan data akademik pribadi mahasiswa, "
        "termasuk semester, IPK, status pembayaran, atau jadwal kuliah individual. "
        "Silakan minta mahasiswa mengecek akun UII Gateway/UIIRAS miliknya sendiri."
    )


def _validated_session_context(value):
    if not isinstance(value, dict):
        return None

    role = value.get("role")
    if role not in {"student", "parent", "unknown"}:
        return None

    context = {"role": role}
    name = value.get("preferred_name")
    if isinstance(name, str):
        name = name.strip()
        if (
            0 < len(name) <= 60
            and all(character.isalpha() or character in " .'’-"
                    for character in name)
        ):
            context["preferred_name"] = name
    return context


def identify_user(question):
    normalized_question = str(question or "")
    parent_match = PARENT_INTRO_PATTERN.search(normalized_question)
    english_parent_match = ENGLISH_PARENT_INTRO_PATTERN.search(normalized_question)
    if parent_match or english_parent_match:
        child_name = (
            parent_match.group("child_name")
            if parent_match
            else english_parent_match.group("child_name")
        )
        return {"role": "parent"}, child_name

    for pattern in (STUDENT_NAME_PATTERN, ENGLISH_STUDENT_NAME_PATTERN):
        match = pattern.search(normalized_question)
        if match:
            return {
                "role": "student",
                "preferred_name": match.group("name").strip(),
            }, match.group("name").strip()

    match = EXPLICIT_NAME_PATTERN.search(normalized_question)
    if match:
        name = match.group("name").strip()
        return {"role": "unknown", "preferred_name": name}, name

    return None, None


def build_session_greeting(session_context, mode):
    if not session_context:
        return None
    if session_context.get("role") == "parent":
        if normalize_mode(mode) == "ip":
            return "Hello, and thank you for reaching out."
        return "Baik, Bapak/Ibu."

    name = session_context.get("preferred_name")
    if not name:
        return None
    greeting = "Hello" if normalize_mode(mode) == "ip" else "Halo"
    return f"{greeting}, {name}."


def redact_personal_name(text, names):
    redacted_text = str(text or "")
    redacted_text = PARENT_INTRO_PATTERN.sub("", redacted_text)
    redacted_text = ENGLISH_PARENT_INTRO_PATTERN.sub("", redacted_text)
    for name in names:
        if name:
            redacted_text = re.sub(
                r"(?<!\w)" + re.escape(name) + r"(?!\w)",
                "",
                redacted_text,
                flags=re.IGNORECASE,
            )
    redacted_text = re.sub(
        r"\b(?:nama saya|my name is)\s*(?=[,.;!?]|\b(?:dan saya|and i)\b)",
        "",
        redacted_text,
        flags=re.IGNORECASE,
    )
    redacted_text = re.sub(r"\b(saya|aku)\s*,\s*", r"\1 ", redacted_text, flags=re.IGNORECASE)
    redacted_text = re.sub(r"\s+([,.;:!?])", r"\1", redacted_text)
    redacted_text = re.sub(r"([,.;:])(?:\s*[,.;:])+", r"\1", redacted_text)
    return re.sub(r"\s+", " ", redacted_text).strip(" ,;:.!?")


def is_contextual_follow_up(question):
    normalized_question = " ".join(str(question or "").lower().split())
    follow_up_markers = (
        "bagaimana dengan ",
        "bagaimana jika ",
        "kalau begitu",
        "lalu bagaimana",
        "terus bagaimana",
        "yang tadi",
        "hal tersebut",
        "dan untuk ",
        "what about ",
        "how about ",
        "and what about ",
        "in that case",
        "what if ",
        "which one",
        "what does that",
    )
    return any(marker in normalized_question for marker in follow_up_markers)


def build_glossary_prompt(mode):
    normalized_mode = normalize_mode(mode)
    glossary_lines = []
    for key, definitions in LOCAL_GLOSSARY.items():
        if key in {"key-in", "dpa", "prodi", "gateway", "sekawan", "mkwu", "uiiras", "regular", "international program", "fakultas"}:
            glossary_lines.append(definitions.get(normalized_mode, definitions.get("regular", "")))
    return "\n".join(glossary_lines)


def expand_query_with_glossary(query, mode):
    normalized_query = str(query or "").lower()
    glossary_terms = []
    for key in LOCAL_GLOSSARY:
        if key in normalized_query:
            glossary_terms.append(LOCAL_GLOSSARY[key].get(normalize_mode(mode), LOCAL_GLOSSARY[key].get("regular", "")))
    if not glossary_terms:
        return query
    return f"{query} {' '.join(glossary_terms)}"


def get_groq_response(question, context, conversation_history, mode="regular"):
    normalized_mode = normalize_mode(mode)
    mode_config = MODE_GUIDES.get(normalized_mode, MODE_GUIDES["regular"])
    history_messages = []
    for message in conversation_history[-10:]:
        role = message.get("role")
        content = message.get("content", "").strip()
        if role in {"user", "assistant"} and content:
            history_messages.append({"role": role, "content": content})

    glossary_prompt = build_glossary_prompt(normalized_mode)

    chat_completion = client_groq.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"""Anda adalah Asisten Akademik resmi Program Studi Informatika UII.
Gunakan hanya informasi dari KONTEKS DOKUMEN untuk menjawab. Jangan mengarang jadwal, tanggal,
aturan, biaya, atau persyaratan yang tidak terdapat dalam konteks.

Mode aktif: {mode_config['label']} ({mode_config['language']})
{mode_config['instruction']}

GLOSARIUM ISTILAH LOKAL:
{glossary_prompt}

Batasan data pribadi:
- Anda tidak memiliki akses ke rekam akademik individu, termasuk IPK, status pembayaran,
  atau jadwal kelas pribadi. Jangan meminta nama, NIM, kata sandi, atau bukti pembayaran.
- Jangan mengakses atau mengungkap data pribadi mahasiswa berdasarkan klaim bahwa pengguna
  adalah orang tua/wali.
- Jangan memperlakukan pertanyaan atau data historis mahasiswa lain di dokumen sebagai
  data pengguna saat ini. Arahkan pengguna untuk mengecek akun UII Gateway/UIIRAS miliknya.
- Jangan menyalin atau mengeja ulang nama pengguna. Sapaan personal ditambahkan oleh aplikasi
  menggunakan ejaan persis yang diberikan pengguna.

Aturan percakapan:
1. Pertanyaan umum seperti profil prodi, lokasi lab, atau komunitas dapat langsung dijawab secara padat.
2. Pertanyaan yang bergantung pada semester, angkatan, kelas Reguler/IP, atau tahun akademik harus diperiksa
   berdasarkan RIWAYAT PERCAKAPAN.
3. Jika informasi konteks yang diperlukan belum ada, tanyakan hanya informasi yang masih kurang. Jangan memberi
   jawaban spesifik sebelum konteks tersebut jelas.
4. Bedakan angkatan (tahun masuk) dan semester (posisi studi). Untuk jadwal atau aturan periode tertentu,
   minta tahun akademik/periode jika belum disebutkan.
5. Jika pengguna menjawab pertanyaan klarifikasi, hubungkan jawabannya dengan pertanyaan sebelumnya.
6. Jika informasi tidak ada dalam konteks dokumen, katakan bahwa informasi tersebut belum tersedia dalam pedoman
   resmi dan sarankan menghubungi staf prodi.
7. Jangan menyebut proses internal RAG.
8. Selalu jawab sesuai mode aktif yang dipilih oleh pengguna. Jika mode IP dipilih, jawaban seluruhnya harus dalam Bahasa Inggris.
9. Gunakan istilah lokal dan definisi glosarium di atas secara konsisten agar nama lembaga, istilah akademik, dan jalur studi tidak terdistorsi.
10. Prioritaskan pertanyaan terbaru dan KONTEKS DOKUMEN. Gunakan riwayat hanya untuk menyelesaikan pertanyaan lanjutan; jangan biarkan topik lama mengubah jawaban atas pertanyaan baru yang sudah jelas.
11. Untuk jawaban yang bergantung pada angkatan, semester, atau periode, prioritaskan dokumen yang secara eksplisit cocok dengan semua konteks pada pertanyaan terbaru. Jangan memindahkan fakta dari angkatan atau periode lain. Jika dokumen yang cocok tidak tersedia, minta klarifikasi atau nyatakan keterbatasan informasi.

RIWAYAT PERCAKAPAN:
{history_messages}

KONTEKS DOKUMEN:
{context}"""
            },
            *history_messages,
            {"role": "user", "content": question}
        ],
        model=GROQ_MODEL,
        temperature=0.2,
    )
    return chat_completion.choices[0].message.content


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True) or {}
    user_query = data.get("query", "")
    conversation_history = data.get("conversation_history", [])
    mode = normalize_mode(data.get("mode"))

    if not isinstance(conversation_history, list):
        conversation_history = []

    if not user_query:
        return jsonify({"error": "Query tidak boleh kosong"}), 400

    identified_context, identified_name = identify_user(user_query)
    session_context = _validated_session_context(data.get("session_context")) or {}
    if identified_context:
        if identified_context["role"] in {"student", "parent"}:
            session_context = identified_context
        elif session_context.get("role") != "parent":
            session_context.update(identified_context)
    elif not session_context:
        for message in conversation_history:
            if isinstance(message, dict) and message.get("role") == "user":
                previous_identity, _ = identify_user(message.get("content", ""))
                if previous_identity:
                    session_context = previous_identity

    personal_names = [identified_name, session_context.get("preferred_name")]
    greeting = (
        build_session_greeting(identified_context, mode)
        if identified_context
        else None
    )

    personal_record_refusal = get_personal_record_refusal(user_query, mode)
    if personal_record_refusal:
        response_body = {
            "answer": personal_record_refusal,
            "sources": [],
            "mode": mode,
            "session_context": session_context,
        }
        if greeting:
            response_body["greeting"] = greeting
        return jsonify(response_body)

    try:
        course_package_response = resolve_course_package(user_query, mode)
    except Exception as e:
        app.logger.exception("Failed to resolve the requested course package")
        return jsonify({"error": str(e)}), 500

    if course_package_response:
        response_body = {
            **course_package_response,
            "mode": mode,
            "session_context": session_context,
        }
        if greeting:
            response_body["greeting"] = greeting
        return jsonify(response_body)

    contextual_history = conversation_history[-6:] if is_contextual_follow_up(user_query) else []
    sanitized_history = []
    for message in contextual_history:
        if not isinstance(message, dict):
            continue
        content = str(message.get("content", ""))
        _, history_name = identify_user(content)
        sanitized_history.append({
            "role": message.get("role"),
            "content": redact_personal_name(content, personal_names + [history_name]),
        })

    previous_user_queries = [
        message["content"].strip()
        for message in sanitized_history
        if message.get("role") == "user" and message.get("content", "").strip()
    ]
    safe_query = redact_personal_name(user_query, personal_names)
    retrieval_query = " ".join(previous_user_queries[-2:] + [safe_query])
    retrieval_query = expand_query_with_glossary(retrieval_query, mode)

    mode_filter = {
        "$or": [
            {"program_scope": "all"},
            {"program_scope": mode}
        ]
    }

    try:
        results = collection.query(
            query_texts=[retrieval_query],
            n_results=5,
            where=mode_filter,
        )
    except Exception:
        results = collection.query(
            query_texts=[retrieval_query],
            n_results=5
        )

    context = "\n\n".join(results['documents'][0])

    try:
        answer = get_groq_response(safe_query, context, sanitized_history, mode=mode)
        response_body = {
            "answer": answer,
            "sources": results['metadatas'][0],
            "mode": mode,
            "session_context": session_context,
        }
        if greeting:
            response_body["greeting"] = greeting
        return jsonify(response_body)
    except Exception as e:
        print(f"ERROR TERDETEKSI: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
































