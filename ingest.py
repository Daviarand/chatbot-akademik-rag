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


def build_metadata(source_name, file_name, question):
    normalized_source = source_name.lower()
    normalized_file = file_name.lower()

    if "profil" in normalized_source or "profil" in normalized_file:
        topic = "profil_prodi"
    elif "panduan" in normalized_source or "keyin" in normalized_source or "key-in" in normalized_file:
        topic = "panduan_keyin"
    elif "talk" in normalized_source or "talk" in normalized_file:
        topic = "keyin_talk"
    elif "penjelasan" in normalized_source or "penjelasan" in normalized_file or "akademik" in normalized_file:
        topic = "penjelasan_akademik"
    else:
        topic = "umum"

    if "ganjil" in normalized_file:
        period = "ganjil"
    elif "genap" in normalized_file:
        period = "genap"
    else:
        period = "all"

    metadata = {
        "source": source_name,
        "file": file_name,
        "question": question,
        "language": "multilingual",
        "program_scope": "all",
        "topic": topic,
        "subtopic": "general",
        "period": period,
    }

    if "keyin" in normalized_source or "keyin" in normalized_file:
        metadata["subtopic"] = "keyin"
    elif "pendukung" in normalized_source or "unit" in normalized_source:
        metadata["subtopic"] = "unit_pendukung"
    elif "kemitraan" in normalized_source or "kemitraan" in normalized_file:
        metadata["subtopic"] = "kemitraan"
    elif "profil" in normalized_source or "profil" in normalized_file:
        metadata["subtopic"] = "profil"

    if "ip" in question.lower() or "international program" in question.lower():
        metadata["program_scope"] = "ip"
    elif "reguler" in question.lower() and "ip" not in question.lower():
        metadata["program_scope"] = "regular"

    return metadata


def ingest_knowledge_base():
    client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)

    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="paraphrase-multilingual-MiniLM-L12-v2"
    )

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
                                metadatas.append(build_metadata(source_name, file, question))
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