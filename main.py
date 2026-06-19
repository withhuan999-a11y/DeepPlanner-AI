from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from core.agent import chat_with_agent
from core.scraper import perform_deep_search

app = FastAPI()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    query: str
    history: list[Message]
    use_deep_search: bool

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    history_dicts = [{"role": m.role, "content": m.content} for m in request.history]
    
    if request.use_deep_search:
        scraped_context = await perform_deep_search(request.query)
        reply = await chat_with_agent(
            query=request.query,
            context=scraped_context,
            tools_enabled=True
        )
    else:
        reply = await chat_with_agent(
            query=request.query,
            history=history_dicts,
            tools_enabled=False
        )
        
    return {"reply": reply}

@app.get("/")
async def get_index():
    return FileResponse("index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)