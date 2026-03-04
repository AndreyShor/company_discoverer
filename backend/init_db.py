import os
import json
import uuid
from pymongo import MongoClient
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance
from sentence_transformers import SentenceTransformer

def init_mongodb():
    print("Initializing MongoDB...")
    try:
        client = MongoClient("mongodb://mongodb:27017")
        profiles = client["db_main"]["profiles"]
        
        personName = "andrejs"
        pathToFile = "/parser/UserData/" + personName + ".json"
        
        if os.path.exists(pathToFile):
            with open(pathToFile, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["_id"] = personName
            profiles.update_one({"_id": personName}, {"$set": data}, upsert=True)
            print("MongoDB profiles updated.")
        else:
            print(f"File {pathToFile} not found. Skipping MongoDB insertion.")
    except Exception as e:
        print(f"Failed to initialize MongoDB: {e}")

def init_qdrant():
    print("Initializing Qdrant...")
    try:
        docs_dir = "/parser/Books/txt"
        qdrant_host = "qdrant"
        qdrant_port = 6333
        embedding_dim = 384
        
        collections = ["portfolio_documents", "physics_papers_random_300_pages_v2"]

        client = QdrantClient(host=qdrant_host, port=qdrant_port)
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        for collection_name in collections:
            if not client.collection_exists(collection_name):
                print(f"Creating Qdrant collection: {collection_name}...", flush=True)
                client.recreate_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE),
                )
                
                if os.path.exists(docs_dir):
                    all_txt_files = [os.path.join(docs_dir, f) for f in os.listdir(docs_dir) if f.endswith(".txt")]
                    
                    portfolio_files = [f for f in all_txt_files if "legalmate_assistant" in f or "geopost_system" in f or "ai_evaluation" in f or "jobfair" in f or "greengish" in f]
                    physics_files = [f for f in all_txt_files if f not in portfolio_files]
                    
                    target_files = portfolio_files if collection_name == "portfolio_documents" else physics_files
                    batch_size = 64
                    points_batch = []
                    total_inserted = 0
                    
                    for file_path in target_files:
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read()
                            if not content.strip():
                                continue
                            
                            embedding = embedder.encode(content).tolist()
                            point = PointStruct(
                                id=str(uuid.uuid4()),
                                vector=embedding,
                                payload={
                                    "text": content,
                                    "source_file": os.path.basename(file_path)
                                }
                            )
                            points_batch.append(point)
                            
                            if len(points_batch) >= batch_size:
                                client.upsert(collection_name=collection_name, points=points_batch)
                                total_inserted += len(points_batch)
                                print(f"Inserted {total_inserted} documents into {collection_name}...", flush=True)
                                points_batch = []
                        except Exception as e:
                            print(f"Error processing {file_path}: {e}", flush=True)
                    
                    # Insert any remaining documents
                    if points_batch:
                        client.upsert(collection_name=collection_name, points=points_batch)
                        total_inserted += len(points_batch)
                    
                    if total_inserted > 0:
                        print(f"Finished inserting {total_inserted} total documents to {collection_name}.", flush=True)
                    else:
                        print(f"No documents found for {collection_name}.", flush=True)
            else:
                print(f"Qdrant collection {collection_name} already exists. Skipping.", flush=True)
    except Exception as e:
         print(f"Failed to initialize Qdrant: {e}")

def init_all():
    init_mongodb()
    init_qdrant()

if __name__ == "__main__":
    init_all()
