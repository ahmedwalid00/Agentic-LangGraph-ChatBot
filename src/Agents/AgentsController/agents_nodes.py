# src/Agents/AgentsController/agents_nodes.py

from langgraph.graph import END
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_experimental.tools import PythonREPLTool
from langchain_tavily import TavilySearch

# Make sure these imports are correct for your project structure
from src.Schemes.agents_schemes import Supervisor, Validator
from src.Schemes.graph_state import BasicChatState
from src.Agents.Prompts.agents_prompts import supervisor_system_prompt, validator_system_prompt
from src.Helpers.config import get_settings

# ==============================================================================
# === 1. GLOBAL INITIALIZATION (SAFE COMPONENTS)                             ===
# ==============================================================================
# These components are stateless and safe to initialize once and reuse.

settings = get_settings()
llm = ChatOpenAI(api_key=settings.OPENAI_API_KEY, model=settings.GENERATION_MODEL_ID)
tavily_tool = TavilySearch(max_results=3, api_key=settings.TAVILY_API_KEY)

# --- Prompts ---
researcher_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an Information Specialist with expertise in comprehensive research. "
        "Your responsibilities are to gather relevant, accurate, and up-to-date information "
        "from reliable sources based on the query. Focus exclusively on information gathering."
    ),
    ("placeholder", "{messages}"),
])

coder_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a Coder and Analyst. Your primary function is to execute Python code "
        "to solve problems, perform calculations, or analyze data. You must write and run code "
        "to answer the user's request. Always provide the final result of the code execution."
    ),
    ("placeholder", "{messages}"),
])

# --- Create the researcher agent executor (Tavily is stateless and safe to reuse) ---
research_agent_executor = create_react_agent(
    llm,
    tools=[tavily_tool],
    prompt=researcher_prompt
)


# ==============================================================================
# === 2. GRAPH NODE DEFINITIONS                                              ===
# ==============================================================================

# In agents_nodes.py

async def supervisor_node(state: BasicChatState) -> dict:
    """The primary router of the graph."""
    
    # Create a structured prompt for the supervisor
    # This separates the original user request from the agent scratchpad
    messages = state["messages"]
    user_question = messages[0].content
    
    # If there are more than 1 messages, it means agents have already worked
    if len(messages) > 1:
        agent_scratchpad = "\n".join([f"{msg.name}: {msg.content}" for msg in messages[1:]])
        prompt_input = (
            f"The user's original question is: '{user_question}'\n\n"
            f"The following work has been done so far:\n{agent_scratchpad}\n\n"
            "Based on this, what is the next best step?"
        )
    else:
        prompt_input = user_question

    system_prompt = supervisor_system_prompt
    
    # The LLM now gets a much clearer picture
    llm_input = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt_input}
    ]

    llm_structured = llm.with_structured_output(Supervisor)
    response = await llm_structured.ainvoke(llm_input)
    
    print(f"--- Supervisor: Decided to route to {response.next} ---")
    return {"messages": [HumanMessage(content=response.reason, name="supervisor")], "next": response.next}


async def researcher_node(state: BasicChatState) -> dict:
    """Invokes the research agent."""
    print("--- Researcher: Starting research ---")
    agent_input = {"messages": state["messages"]}
    response = await research_agent_executor.ainvoke(agent_input)
    print("--- Researcher: Finished research ---")
    return {"messages": [response["messages"][-1]], "next": "validator"}

async def coder_node(state: BasicChatState) -> dict:
    """
    Handles coding tasks by creating a fresh agent with a fresh tool for each execution.
    This is necessary because the PythonREPLTool is single-use.
    """
    print("--- Coder: Creating fresh tool and agent for this execution. ---")
    
    # Create a new tool instance for this specific task
    python_repl_tool = PythonREPLTool()
    
    # Create a new agent executor that uses the fresh tool
    agent_executor = create_react_agent(
        llm,
        tools=[python_repl_tool],
        prompt=coder_prompt
    )
    
    # Pass a clean input dictionary to the agent
    agent_input = {"messages": state["messages"]}
    result = await agent_executor.ainvoke(agent_input)
    
    print("--- Coder: Finished coding task ---")
    return {"messages": [result["messages"][-1]], "next": "validator"}

# In agents_nodes.py

async def validator_node(state: BasicChatState) -> dict:
    """Validates the agent's final answer."""
    print("--- Validator: Starting validation ---")
    
    # Filter messages to find the original question and the last "working" agent's response
    all_messages = state["messages"]
    human_question = all_messages[0].content
    
    # Find the last message that is NOT from the supervisor, enhancer, or validator
    agent_answer = "No answer found."
    for msg in reversed(all_messages):
        if msg.name not in ["supervisor", "enhancer", "validator"]:
            agent_answer = msg.content
            break

    system_prompt = validator_system_prompt
    llm_structured = llm.with_structured_output(Validator)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"The original question was: '{human_question}'"},
        {"role": "assistant", "content": f"The agent provided this answer: '{agent_answer}'"},
    ]

    response = await llm_structured.ainvoke(messages)
    
    goto = response.next
    if goto == "FINISH":
        goto = END
        print("--- Validator: Validation successful. Ending run. ---")
    else:
        goto = "supervisor"
        print("--- Validator: Validation failed. Rerouting to Supervisor. ---")
        
    # The reason for the decision is added, but the final answer will be extracted cleanly.
    return {"messages": [HumanMessage(content=response.reason, name="validator")], "next": goto}