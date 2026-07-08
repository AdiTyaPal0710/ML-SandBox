from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict, Any
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI

from sand_box import run_Sandbox
from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(
    model = "gemini-2.5-flash",
    verbose = True,
    temperature = 0,
    google_api_key = GEMINI_API_KEY
)

class EvaluatingDecision(BaseModel):

    reasoning: str = Field(
        description="Explanation of what happened in the execution logs."
    )
    
    status: str = Field(
        description="MUST be exactly one of: 'success', 'needs_improvement', 'needs_debugging'"
    )
    

class AgentState(TypedDict):
    goal: str
    current_code: str
    requirements: str
    iteration_count: int
    latest_metrics: Dict[str, Any]
    status: str
    execution_logs: List[str]
    exit_code: int 

def ingest_state(state: AgentState):

    print("\n[Node: Ingest] Reading initial goal and baseline code...")

    return state


def Executore_Node(state: AgentState)->AgentState:

    print(f"\n[Node: Execute] Running Iteration {state['iteration_count']} in Docker...")
    code = state["current_code"]
    requirements = state.get("requirements", "")
    result = run_Sandbox(code, requirements)

    new_logs = state.get("execution_logs", [])
    new_logs.append(result["logs"])

    print("   [Docker Output]:", result["logs"].strip())

    return {
        "execution_logs": new_logs,
        "exit_code": result["exit_code"]
    }

def evaluate_Node(state: AgentState):
    
    print(f"\n[Node: Evaluate] Analyzing results from Iteration {state['iteration_count']}...")
    
    latest_logs = state["execution_logs"][-1]

    prompt = f"""
    You are a Senior ML Engineer.Evaluate ONLY the most recent execution results below.
    Goal: {state['goal']}
    Exit Code: {state['exit_code']}
    Logs: {latest_logs}
    
    If the code crashed (Exit Code != 0), the status is 'needs_debugging'.
    If the code ran but didn't meet the goal, the status is 'needs_improvement'.
    If the goal is fully met, the status is 'success'.
    """
    evaluator = llm.with_structured_output(EvaluatingDecision)
    result = evaluator.invoke(prompt)
    
    print(f"   [AI Thinking]: {result.reasoning}")
    print(f"   [AI Decision]: {result.status}")
    
    return {"status": result.status}

def modify_code(state: AgentState):

    latest_log = state["execution_logs"][-1]
    
    prompt = f"""
    You are an expert ML Engineer. Your last script resulted in the following logs:
    {latest_log}
    
    Your overall goal is: {state['goal']}
    
    Here is the current code:
    ```python
    {state['current_code']}
    ```
    
    Write the updated Python code to fix the errors or improve the metrics. 
    Return ONLY the raw python code. Do not include markdown formatting like ```python. 
    Do not include explanations. Just the raw text of the script.
    """
    
    response = llm.invoke(prompt)
    
    new_code = response.content.strip()
    if new_code.startswith("```python"):
        new_code = new_code[9:]
    if new_code.startswith("```"):
        new_code = new_code[3:]
    if new_code.endswith("```"):
        new_code = new_code[:-3]
    
    return {
        "current_code": new_code.strip(),
        "iteration_count": state["iteration_count"] + 1,
    }

def route_next_step(state: AgentState) -> str:
    status = state["status"]
    if status == "success":
        return END
    elif status in ["needs_improvement", "needs_debugging"]:
        if state["iteration_count"] >= 5: 
            print("\n[Failsafe] Reached 5 iterations. Stopping to save API costs.")
            return END
        return "modify"
    return END

# building the graph
workflow = StateGraph(AgentState)

workflow.add_node("ingest_state", ingest_state)
workflow.add_node("execute_code", Executore_Node)
workflow.add_node("evaluate_code", evaluate_Node)
workflow.add_node("modify_code", modify_code)

workflow.set_entry_point("ingest_state")
workflow.add_edge("ingest_state", "execute_code")
workflow.add_edge("execute_code", "evaluate_code")
workflow.add_conditional_edges("evaluate_code", route_next_step, {"modify": "modify_code", END: END})
workflow.add_edge("modify_code", "execute_code")

graph = workflow.compile()

if __name__ == "__main__":
    initial_state = {
        "goal": "Run a simple print statement",
        "current_code": 'print("Hello from LangGraph!")',
        "requirements": "",
        "iteration_count": 1,
        "latest_metrics": {},
        "status": "",
        "execution_logs": [],
        "exit_code": 0
    }

    print("Starting LangGraph workflow...")
    final_state = graph.invoke(initial_state)
    print("\n--- Final Output ---")
    print(f"Status: {final_state.get('status')}")
    print(f"Exit Code: {final_state.get('exit_code')}")
    print(f"Logs: {final_state.get('execution_logs')}")
