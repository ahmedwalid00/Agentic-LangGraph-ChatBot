from typing import Annotated, Literal
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

class BasicChatState(TypedDict):
    
    messages: Annotated[list[BaseMessage], add_messages]
    next: Literal["enhancer", "researcher", "coder", "supervisor", "validator", "__end__"]