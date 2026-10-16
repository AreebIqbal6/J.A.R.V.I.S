import os
import uuid
import sqlite3

try:
    import chromadb
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False

# --- MEMORY DATABASE SETUP ---
DB_DIR = os.path.join("Data", "VectorMemory")
SQLITE_DB = os.path.join("Data", "JarvisMemory.db")
os.makedirs("Data", exist_ok=True)

client = None
collection = None

if HAS_CHROMADB:
    try:
        os.makedirs(DB_DIR, exist_ok=True)
        client = chromadb.PersistentClient(path=DB_DIR)
        collection = client.get_or_create_collection(name="jarvis_memory")
    except Exception as e:
        HAS_CHROMADB = False

def _init_sqlite():
    conn = sqlite3.connect(SQLITE_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fact TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

_init_sqlite()

def Remember(data):
    """Embeds a new fact into the memory database."""
    try:
        clean_data = data.lower().replace("jarvis", "").strip()
        clean_data = clean_data.replace("remember that", "").replace("remember", "").strip(',. ')
        
        if clean_data:
            clean_data = clean_data.capitalize()
        else:
            return "You didn't tell me what to remember, sir."

        doc_id = str(uuid.uuid4())
        
        if HAS_CHROMADB and collection:
            collection.add(
                documents=[clean_data],
                metadatas=[{"source": "user"}],
                ids=[doc_id]
            )
        else:
            conn = sqlite3.connect(SQLITE_DB)
            c = conn.cursor()
            c.execute("INSERT INTO memories (fact) VALUES (?)", (clean_data,))
            conn.commit()
            conn.close()
        
        return f"I have committed that to my memory, sir: {clean_data}"
        
    except Exception as e:
        return f"Error saving memory: {e}"

def Recall(query=None):
    """Retrieves memories. If a query is given, performs a semantic or keyword search."""
    try:
        if HAS_CHROMADB and collection:
            if not query or query.strip() == "":
                results = collection.get(limit=5)
                docs = results.get('documents', [])
                if not docs:
                    return "My memory banks are currently empty, sir."
                result = "Here are my most recent memories:\n"
                for i, doc in enumerate(docs, 1):
                    result += f"{i}. {doc}\n" 
                return result.strip()

            clean_query = query.lower().replace("jarvis", "").replace("recall", "").replace("what do you remember about", "").strip()
            results = collection.query(
                query_texts=[clean_query],
                n_results=2
            )
            docs = results.get('documents', [[]])[0]
            if not docs:
                return "I have no memory of that, sir."
            res = "Based on my memory:\n"
            for i, doc in enumerate(docs, 1):
                res += f"{i}. {doc}\n"
            return res.strip()
        else:
            conn = sqlite3.connect(SQLITE_DB)
            c = conn.cursor()
            if not query or query.strip() == "":
                c.execute("SELECT fact FROM memories ORDER BY timestamp DESC LIMIT 5")
                rows = c.fetchall()
                conn.close()
                if not rows:
                    return "My memory banks are currently empty, sir."
                result = "Here are my most recent memories:\n"
                for i, row in enumerate(rows, 1):
                    result += f"{i}. {row[0]}\n"
                return result.strip()

            clean_query = query.lower().replace("jarvis", "").replace("recall", "").replace("what do you remember about", "").strip()
            c.execute("SELECT fact FROM memories WHERE fact LIKE ? ORDER BY timestamp DESC LIMIT 3", (f"%{clean_query}%",))
            rows = c.fetchall()
            conn.close()
            if not rows:
                return "I have no memory of that, sir."
            res = "Based on my memory:\n"
            for i, row in enumerate(rows, 1):
                res += f"{i}. {row[0]}\n"
            return res.strip()
            
    except Exception as e:
        return f"Error retrieving memories: {e}"

def Forget(query):
    """Searches for matching memory and deletes it."""
    global collection
    try:
        target = query.lower().replace("jarvis", "").replace("forget that", "").replace("forget", "").strip()
        
        if HAS_CHROMADB and collection and client:
            if "everything" in target or "all" in target:
                client.delete_collection(name="jarvis_memory")
                collection = client.get_or_create_collection(name="jarvis_memory")
                return "I have completely wiped my neural memory banks, sir."

            if len(target) < 3: 
                return "Please be more specific. That phrase is too short to safely delete without clearing other memories."

            results = collection.query(
                query_texts=[target],
                n_results=1
            )
            
            if results['ids'] and results['ids'][0]:
                target_id = results['ids'][0][0]
                deleted_doc = results['documents'][0][0]
                collection.delete(ids=[target_id])
                return f"I have purged the memory '{deleted_doc}' from my neural net, sir."
            else:
                return f"I couldn't find any related records to '{target}', sir."
        else:
            conn = sqlite3.connect(SQLITE_DB)
            c = conn.cursor()
            if "everything" in target or "all" in target:
                c.execute("DELETE FROM memories")
                conn.commit()
                conn.close()
                return "I have completely wiped my neural memory banks, sir."

            if len(target) < 3:
                conn.close()
                return "Please be more specific. That phrase is too short to safely delete without clearing other memories."

            c.execute("SELECT id, fact FROM memories WHERE fact LIKE ? LIMIT 1", (f"%{target}%",))
            row = c.fetchone()
            if row:
                c.execute("DELETE FROM memories WHERE id = ?", (row[0],))
                conn.commit()
                conn.close()
                return f"I have purged the memory '{row[1]}' from my records, sir."
            conn.close()
            return f"I couldn't find any related records to '{target}', sir."
            
    except Exception as e:
        return f"Error editing database: {e}"