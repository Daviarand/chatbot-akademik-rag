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

    previous_user_queries = [
        message.get("content", "").strip()
        for message in conversation_history[-10:]
        if message.get("role") == "user" and message.get("content", "").strip()
    ]
    retrieval_query = " ".join(previous_user_queries + [user_query])
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
        answer = get_groq_response(user_query, context, conversation_history, mode=mode)
        return jsonify({
            "answer": answer,
            "sources": results['metadatas'][0],
            "mode": mode
        })
    except Exception as e:
        print(f"ERROR TERDETEKSI: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)




































