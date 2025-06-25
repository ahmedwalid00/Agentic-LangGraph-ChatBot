# src/Routes/chat_routes.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from src.Graph.graph_factory import graph_builder_instance

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    message: str
    thread_id: str

@router.post("/invoke")
async def invoke_chat(chat_request: ChatRequest):
    # The mount path for Render's persistent disk.
    # We will create this directory on the Render service.
    data_dir = "/var/data"
    db_path = f"{data_dir}/chatbot.sqlite"
    try:
        async with AsyncSqliteSaver.from_conn_string(db_path) as memory:
            agent_graph = graph_builder_instance.compile(checkpointer=memory)
            config = {"configurable": {"thread_id": chat_request.thread_id}}
            graph_input = {"messages": [HumanMessage(content=chat_request.message)]}
            
            final_state = await agent_graph.ainvoke(graph_input, config=config)
            
            final_messages = final_state.get("messages", [])
            final_answer = "Sorry, I couldn't find an answer."
            for msg in reversed(final_messages):
                if msg.name not in ["supervisor", "enhancer", "validator", "user"]:
                    final_answer = msg.content
                    break

            return JSONResponse(content={"response": final_answer, "thread_id": chat_request.thread_id})
    except Exception as e:
        print(f"FATAL ERROR during invoke: {e}")
        raise HTTPException(status_code=500, detail=str(e))