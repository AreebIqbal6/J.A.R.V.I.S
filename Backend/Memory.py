import os
import chromadb
import uuid

# --- VECTOR DATABASE SETUP ---
# We store the neural embeddings inside Data/VectorMemory
DB_PATH = os.path.join("Data", "VectorMemory")
os.makedirs(DB_PATH, exist_ok=True)

# Initialize ChromaDB Persistent Client
# The first time this runs, it will quietly download a small embedding model (~80MB) to handle the math
try:
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_or_create_collection(name="jarvis_memory")
except Exception as e:
    print(f"!! Vector Memory Init Error: {e}")

def Remember(data):
    """Embeds a new fact into the vector database."""
    try:
        clean_data = data.lower().replace("jarvis", "").strip()
        clean_data = clean_data.replace("remember that", "").replace("remember", "").strip()
        
        if clean_data:
            clean_data = clean_data.capitalize()
        else:
            return "You didn't tell me what to remember, sir."

        # Generate a unique ID for the memory
        doc_id = str(uuid.uuid4())
        
        # Insert into ChromaDB (automatically generates vector embeddings)
        collection.add(
            documents=[clean_data],
            metadatas=[{"source": "user"}],
            ids=[doc_id]
        )
        
        return f"I have committed that to my neural memory: {clean_data}"
        
    except Exception as e:
        return f"Error saving to Vector Database: {e}"

def Recall(query=None):
    """Retrieves memories. If a query is given, performs a semantic search."""
    try:
        # If no specific query is provided, just return the 5 most recent memories
        if not query or query.strip() == "":
            results = collection.get(limit=5)
            docs = results.get('documents', [])
            
            if not docs:
                return "My memory banks are currently empty, sir."
                
            result = "Here are my most recent memories:\n"
            for i, doc in enumerate(docs, 1):
                result += f"{i}. {doc}\n" 
            return result.strip()

        # --- SEMANTIC SEARCH ---
        # If a query IS provided, we search for the mathematical closest match
        clean_query = query.lower().replace("jarvis", "").replace("recall", "").replace("what do you remember about", "").strip()
        
        results = collection.query(
            query_texts=[clean_query],
            n_results=2 # Return top 2 closest matches
        )
        
        docs = results.get('documents', [[]])[0]
        
        if not docs:
            return "I have no memory of that, sir."
            
        res = "Based on my semantic memory:\n"
        for i, doc in enumerate(docs, 1):
            res += f"{i}. {doc}\n"
        return res.strip()
        
    except Exception as e:
        return f"Error retrieving memories: {e}"

def Forget(query):
    """Searches for the closest matching memory and deletes it."""
    try:
        target = query.lower().replace("jarvis", "").replace("forget that", "").replace("forget", "").strip()
        
        # WIPE ALL
        if "everything" in target or "all" in target:
            client.delete_collection(name="jarvis_memory")
            global collection
            collection = client.get_or_create_collection(name="jarvis_memory")
            return "I have completely wiped my neural memory banks, sir."

        if len(target) < 3: 
            return "Please be more specific. That phrase is too short to safely delete without clearing other memories."

        # Search for the closest match to delete
        results = collection.query(
            query_texts=[target],
            n_results=1
        )
        
        if results['ids'] and results['ids'][0]:
            target_id = results['ids'][0][0]
            deleted_doc = results['documents'][0][0]
            
            # Delete by ID
            collection.delete(ids=[target_id])
            return f"I have purged the memory '{deleted_doc}' from my neural net, sir."
        else:
            return f"I couldn't find any related records to '{target}', sir."
            
    except Exception as e:
        return f"Error editing database: {e}"