# src/main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from src.Routes import chat_route

app = FastAPI(
    title="Wello Agentic Chatbot",
    description="An asynchronous agentic chatbot using LangGraph and FastAPI.",
    version="1.0.0"
)

# 1. Mount the 'static' directory
# This makes files in the 'static' folder accessible via the /static URL path
# Note: The path to the directory is relative to where you run uvicorn
app.mount("/static", StaticFiles(directory="static"), name="static")

# 2. Include your API router for the chat endpoint
app.include_router(chat_route.router)

# 3. Create an endpoint to serve the index.html file at the root URL
@app.get("/", response_class=FileResponse)
async def read_index():
    """Serves the main HTML file for the chatbot UI."""
    return "static/index.html"