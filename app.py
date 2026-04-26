import os
import chromadb
from chromadb.utils import embedding_functions
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai

# Konfigurasi Path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DATA_PATH = os.path.join(BASE_DIR, "chroma_db")

# Load variabel dari file .env
load_dotenv()

# Konfigurasi Gemini API
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

app = Flask(__name__)
CORS(app)

# Inisialisasi ChromaDB
client_chroma = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# Pastikan koleksi ada
try:
    collection = client_chroma.get_collection(name="akademik_uii", embedding_function=embedding_func)
except Exception as e:
    print(f"Peringatan: Koleksi belum dibuat. Jalankan ingest.py terlebih dahulu. Error: {e}")

def get_gemini_response(question, context):
    # Gunakan model yang tersedia di akun user (berdasarkan pengecekan sebelumnya)
    # Default ke gemini-2.0-flash yang sangat cepat
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    model = genai.GenerativeModel(model_name)

    prompt = f"""
    Anda adalah asisten akademik untuk Program Studi Informatika, Universitas Islam Indonesia (UII).
    Gunakan potongan dokumen (Konteks) berikut untuk menjawab pertanyaan mahasiswa.
    
    ATURAN JAWABAN:
    1. Jawaban harus ramah, profesional, dan akurat sesuai data resmi.
    2. HANYA gunakan informasi dari konteks di bawah ini.
    3. Jika jawaban tidak ada dalam konteks, katakan bahwa Anda tidak memiliki informasi tersebut dalam pedoman resmi dan sarankan untuk menghubungi staf prodi melalui layanan Key-In Talk.
    4. Jangan mengarang informasi di luar konteks yang diberikan.
    
    KONTEKS DOKUMEN (Hasil Pencarian):
    {context}
    
    PERTANYAAN MAHASISWA:
    {question}
    
    JAWABAN:
    """
    
    response = model.generate_content(prompt)
    return response.text

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_query = data.get("query", "")
    
    if not user_query:
        return jsonify({"error": "Query tidak boleh kosong"}), 400
    
    try:
        # 1. Retrieval: Cari dokumen relevan di ChromaDB (Semantic Similarity)
        # Kita naikkan n_results menjadi 5 agar cakupan informasi lebih luas
        results = collection.query(
            query_texts=[user_query],
            n_results=5
        )
        
        # Gabungkan hasil pencarian menjadi satu konteks
        # Karena kita menyimpan jawaban di metadata, kita ambil metadatas['answer']
        contexts = []
        for i in range(len(results['documents'][0])):
            q = results['metadatas'][0][i].get('original_question', '')
            a = results['metadatas'][0][i].get('answer', '')
            contexts.append(f"Pertanyaan: {q}\nJawaban: {a}")
            
        full_context = "\n\n---\n\n".join(contexts)
        
        # 2. Generation: Kirim ke Gemini API
        answer = get_gemini_response(user_query, full_context)
        
        return jsonify({
            "answer": answer,
            "sources": results['metadatas'][0]
        })
    except Exception as e:
        print(f"ERROR TERDETEKSI: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Gunakan debug=True untuk pengembangan lokal agar auto-reload
    app.run(host='0.0.0.0', port=5000, debug=True)
