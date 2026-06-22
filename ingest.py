# import os
# import json
# import chromadb
# from chromadb.utils import embedding_functions

# # Konfigurasi Path
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# KB_DIR = os.path.join(BASE_DIR, "KnowledgeBase")
# CHROMA_DATA_PATH = os.path.join(BASE_DIR, "chroma_db")

# def ingest_knowledge_base():
#     # Inisialisasi ChromaDB Client
#     # Menggunakan PersistentClient agar data tersimpan di disk
#     client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
    
#     # Gunakan model embedding lokal yang ringan (all-MiniLM-L6-v2)
#     # Ini gratis dan cepat untuk dijalankan di sandbox
#     embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
#     # Buat atau ambil koleksi
#     collection = client.get_or_create_collection(
#         name="akademik_uii",
#         embedding_function=embedding_func
#     )
    
#     documents = []
#     metadatas = []
#     ids = []
    
#     count = 0
#     # Scan semua folder di KnowledgeBase
#     for root, dirs, files in os.walk(KB_DIR):
#         for file in files:
#             if file.endswith(".json"):
#                 file_path = os.path.join(root, file)
#                 source_name = os.path.basename(root)
                
#                 print(f"Memproses file: {file} dari {source_name}...")
                
#                 with open(file_path, "r", encoding="utf-8") as f:
#                     try:
#                         data = json.load(f)
#                         # Format data bisa list of objects atau list of lists of objects (hasil gabungan jq)
#                         items = []
#                         if isinstance(data, list):
#                             for element in data:
#                                 if isinstance(element, list):
#                                     items.extend(element)
#                                 else:
#                                     items.append(element)
                        
#                         for item in items:
#                             question = item.get("question", "")
#                             answer = item.get("answer", "")
                            
#                             if question and answer:
#                                 # Gabungkan pertanyaan dan jawaban sebagai dokumen yang di-index
#                                 # Ini membantu semantic search menemukan konteks yang tepat
#                                 content = f"Pertanyaan: {question}\nJawaban: {answer}"
                                
#                                 documents.append(content)
#                                 metadatas.append({
#                                     "source": source_name,
#                                     "file": file,
#                                     "question": question
#                                 })
#                                 ids.append(f"id_{count}")
#                                 count += 1
#                     except Exception as e:
#                         print(f"Error membaca {file}: {e}")

#     # Masukkan ke ChromaDB
#     if documents:
#         print(f"Memasukkan {len(documents)} data ke ChromaDB...")
#         # ChromaDB menyarankan batching jika data sangat besar, tapi untuk ratusan data ini aman
#         collection.add(
#             documents=documents,
#             metadatas=metadatas,
#             ids=ids
#         )
#         print("Ingestion selesai!")
#     else:
#         print("Tidak ada data yang ditemukan.")

# if __name__ == "__main__":
#     ingest_knowledge_base()












import os
import json
import chromadb
from chromadb.utils import embedding_functions

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_DIR = os.path.join(BASE_DIR, "KnowledgeBase")
CHROMA_DATA_PATH = os.path.join(BASE_DIR, "chroma_db")

def ingest_knowledge_base():
    client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
    
    # Menggunakan model Multilingual
    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="paraphrase-multilingual-MiniLM-L12-v2"
    )
    
    # Hapus database lama agar tidak ada data yang tumpang tindih 
    try:
        client.delete_collection(name="akademik_uii")
        print("Database lama berhasil direset.")
    except Exception:
        print("Database belum ada, membuat baru...")
        
    collection = client.create_collection(
        name="akademik_uii",
        embedding_function=embedding_func
    )
    
    documents = []
    metadatas = []
    ids = []
    
    count = 0
    for root, dirs, files in os.walk(KB_DIR):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                source_name = os.path.basename(root)
                
                print(f"Memproses file: {file}...")
                
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                        items = []
                        if isinstance(data, list):
                            for element in data:
                                if isinstance(element, list):
                                    items.extend(element)
                                else:
                                    items.append(element)
                        
                        for item in items:
                            question = item.get("question", "")
                            answer = item.get("answer", "")
                            
                            if question and answer:
                                content = f"Pertanyaan: {question}\nJawaban: {answer}"
                                documents.append(content)
                                metadatas.append({
                                    "source": source_name,
                                    "file": file,
                                    "question": question
                                })
                                # Membuat ID yang dijamin Unik
                                ids.append(f"doc_{source_name}_{file}_{count}")
                                count += 1
                    except Exception as e:
                        print(f"Error membaca {file}: {e}")

    if documents:
        print(f"Memasukkan {len(documents)} data ke ChromaDB...")
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print("Ingestion selesai dengan sukses!")
    else:
        print("Tidak ada data yang ditemukan.")

if __name__ == "__main__":
    ingest_knowledge_base()