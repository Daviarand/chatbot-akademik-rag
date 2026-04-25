# import os
# import chromadb
# from chromadb.utils import embedding_functions
# from flask import Flask, request, jsonify
# from flask_cors import CORS
# from dotenv import load_dotenv
# import google.generativeai as genai

# # Konfigurasi Path
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# CHROMA_DATA_PATH = os.path.join(BASE_DIR, "chroma_db")

# # Load variabel dari file .env
# load_dotenv()


# # Konfigurasi Gemini API
# # API Key akan diambil dari environment variable
# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# print("Daftar model yang tersedia untuk API Key Anda:")
# try:
#     for m in genai.list_models():
#         if 'generateContent' in m.supported_generation_methods:
#             print(f"- {m.name}")
# except Exception as e:
#     print(f"Gagal mengambil daftar model: {e}")

# app = Flask(__name__)
# CORS(app)

# # Inisialisasi ChromaDB
# client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
# embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
# collection = client.get_collection(name="akademik_uii", embedding_function=embedding_func)

# def get_gemini_response(question, context):
#     model = genai.GenerativeModel('gemini-2.0-flash-lite')

#     prompt = f"""
#     Anda adalah asisten akademik untuk Program Studi Informatika, Universitas Islam Indonesia (UII).
#     Gunakan potongan dokumen berikut untuk menjawab pertanyaan mahasiswa. 
#     Jika jawaban tidak ada dalam dokumen, katakan bahwa Anda tidak memiliki informasi tersebut dalam pedoman resmi dan sarankan untuk menghubungi staf prodi.
    
#     ATURAN:
#     1. Jawaban harus ramah, profesional, dan akurat.
#     2. HANYA gunakan informasi dari konteks di bawah ini.
#     3. Jangan mengarang informasi.
    
#     KONTEKS DOKUMEN:
#     {context}
    
#     PERTANYAAN MAHASISWA:
#     {question}
    
#     JAWABAN:
#     """
    
#     response = model.generate_content(prompt)
#     return response.text

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
    
#     # 2. Generation: Kirim ke Gemini API
#     try:
#         answer = get_gemini_response(user_query, context)
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
from groq import Groq # Import Groq sebagai pengganti Gemini

# Konfigurasi Path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DATA_PATH = os.path.join(BASE_DIR, "chroma_db")

# Load variabel dari file .env
load_dotenv()

print(f"DEBUG: Key yang terbaca adalah: {os.getenv('GROQ_API_KEY')}")

# Inisialisasi Client Groq
client_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = Flask(__name__)
CORS(app)

# Inisialisasi ChromaDB (Tetap sama seperti sebelumnya)
client_chroma = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = client_chroma.get_collection(name="akademik_uii", embedding_function=embedding_func)

def get_groq_response(question, context):
    # Menggunakan model Llama 3.1 8B yang sangat cepat dan gratis
    chat_completion = client_groq.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"""Anda adalah asisten akademik untuk Program Studi Informatika, Universitas Islam Indonesia (UII).
                Gunakan potongan dokumen berikut untuk menjawab pertanyaan mahasiswa.
                Jika jawaban tidak ada dalam dokumen, katakan bahwa Anda tidak memiliki informasi tersebut dalam pedoman resmi dan sarankan untuk menghubungi staf prodi.
                
                ATURAN:
                1. Jawaban harus ramah, profesional, dan akurat.
                2. HANYA gunakan informasi dari konteks di bawah ini.
                3. Jangan mengarang informasi.
                
                KONTEKS DOKUMEN:
                {context}"""
            },
            {
                "role": "user",
                "content": question,
            }
        ],
        model="llama-3.1-8b-instant",
        temperature=0.2, # Rendah agar jawaban lebih konsisten dan tidak mengarang
    )
    return chat_completion.choices[0].message.content

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_query = data.get("query", "")
    
    if not user_query:
        return jsonify({"error": "Query tidak boleh kosong"}), 400
    
    # 1. Retrieval: Cari dokumen relevan di ChromaDB (Semantic Similarity)
    results = collection.query(
        query_texts=[user_query],
        n_results=3
    )
    
    # Gabungkan hasil pencarian menjadi satu konteks
    context = "\n\n".join(results['documents'][0])
    
    # 2. Generation: Kirim ke Groq API
    try:
        answer = get_groq_response(user_query, context)
        return jsonify({
            "answer": answer,
            "sources": results['metadatas'][0]
        })
    except Exception as e:
        print(f"ERROR TERDETEKSI: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)