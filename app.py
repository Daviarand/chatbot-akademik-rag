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
collection = client_chroma.get_collection(name="akademik_uii", embedding_function=embedding_func)

def get_groq_response(question, context, conversation_history):
    history_messages = []
    for message in conversation_history[-10:]:
        role = message.get("role")
        content = message.get("content", "").strip()
        if role in {"user", "assistant"} and content:
            history_messages.append({"role": role, "content": content})

    chat_completion = client_groq.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"""Anda adalah Asisten Akademik resmi Program Studi Informatika UII.
Gunakan hanya informasi dari KONTEKS DOKUMEN untuk menjawab. Jangan mengarang jadwal, tanggal,
aturan, biaya, atau persyaratan yang tidak terdapat dalam konteks.

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
7. Jawab dalam Bahasa Indonesia dengan singkat, sopan, dan jelas. Jangan menyebut proses internal RAG.

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
    
    # Menigkatkan n_results agar hasil pencarian lebih luas
    results = collection.query(
        query_texts=[retrieval_query],
        n_results=5
    )
    
    context = "\n\n".join(results['documents'][0])
    
    try:
        answer = get_groq_response(user_query, context, conversation_history)
        return jsonify({
            "answer": answer,
            "sources": results['metadatas'][0]
        })
    except Exception as e:
        print(f"ERROR TERDETEKSI: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)




































