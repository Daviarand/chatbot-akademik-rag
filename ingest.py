import os
import json
import chromadb
from chromadb.utils import embedding_functions

# Konfigurasi Path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_DIR = os.path.join(BASE_DIR, "KnowledgeBase")
CHROMA_DATA_PATH = os.path.join(BASE_DIR, "chroma_db")

def ingest_knowledge_base():
    # Inisialisasi ChromaDB Client
    client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
    
    # Gunakan model embedding lokal yang ringan (all-MiniLM-L6-v2)
    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    # Hapus koleksi lama jika ada untuk memastikan data bersih dan terbaru
    try:
        client.delete_collection(name="akademik_uii")
        print("Koleksi lama dihapus untuk re-indexing...")
    except:
        pass

    # Buat koleksi baru
    collection = client.create_collection(
        name="akademik_uii",
        embedding_function=embedding_func
    )
    
    documents = []
    metadatas = []
    ids = []
    
    count = 0
    # Scan semua folder di KnowledgeBase
    for root, dirs, files in os.walk(KB_DIR):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                source_name = os.path.basename(root)
                
                print(f"Memproses file: {file} dari {source_name}...")
                
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
                                # OPTIMASI: Kita hanya meng-index PERTANYAAN sebagai dokumen utama
                                # agar semantic search fokus mencocokkan maksud pertanyaan user
                                # JAWABAN diletakkan di metadata untuk diambil saat retrieval
                                documents.append(question) 
                                metadatas.append({
                                    "source": source_name,
                                    "file": file,
                                    "original_question": question,
                                    "answer": answer # Simpan jawaban lengkap di metadata
                                })
                                ids.append(f"id_{count}")
                                count += 1
                    except Exception as e:
                        print(f"Error membaca {file}: {e}")

    # Masukkan ke ChromaDB
    if documents:
        print(f"Memasukkan {len(documents)} data ke ChromaDB...")
        # ChromaDB menyarankan batching jika data sangat besar
        # Untuk ratusan data, kita bisa masukkan sekaligus
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Ingestion selesai! Total {len(documents)} data berhasil di-index.")
    else:
        print("Tidak ada data yang ditemukan.")

if __name__ == "__main__":
    ingest_knowledge_base()
