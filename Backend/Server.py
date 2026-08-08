from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import your newly upgraded Agentic brain
from Backend.Chatbot import ChatBot

# Initialize the High-Speed API Server
app = FastAPI(title="J.A.R.V.I.S. Mark IV Central Nervous System")

# Allow our upcoming Next.js Web UI to talk to this Python server securely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import asyncio
from Backend import real_data
app.include_router(real_data.router)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(real_data.broadcast_loop())

# Define the data structure we expect from the UI
class UserQuery(BaseModel):
    text: str

@app.get("/")
async def root():
    return {"status": "J.A.R.V.I.S. Core Online", "version": "Mark IV"}

@app.post("/api/think")
@app.post("/api/chat")
async def process_query(query: UserQuery):
    try:
        print(f">> [API RECEIVE]: {query.text}")
        
        # Send the text to the Agentic LLM (which handles tools automatically)
        response_text = ChatBot(query.text)
        
        print(f">> [API RESPONSE]: {response_text}")
        return {"text": response_text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("\n>> IGNITING FASTAPI SERVER ON PORT 8000...")
    # Run the server on the local machine
    uvicorn.run(app, host="127.0.0.1", port=8000)