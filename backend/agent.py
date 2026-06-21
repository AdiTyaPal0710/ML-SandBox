from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict, Any

from sand_box import run_Sandbox

class AgentState(TypedDict):
    goal: str
    current_code: str
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
    result = run_Sandbox(code)

    new_logs = state.get("execution_logs",[]) 
    new_logs.append(result["logs"])

    print("   [Docker Output]:", result["logs"].strip())

    return {
        "execution_logs": result["logs"],
        "exit_code": result["exit_code"]
    }

def evaluate_Node(state: AgentState)->AgentState:
    
    print(f"\n[Node: Evaluate] Analyzing results from Iteration {state['iteration_count']}...")
    
    if state.get("exit_code") != 0:
        print("   [Evaluate] Code crashed! Needs debugging.")
        return {"status": "needs_debugging"}
        
    elif state["iteration_count"] >= 3:
        print("   [Evaluate] Goal reached! Metrics look good.")
        return {"status": "success"}
        
    else:
        print("   [Evaluate] Code ran, but metrics need improvement.")
        return {"status": "needs_improvement"}
        


# building the graph
workflow = StateGraph(AgentState)

workflow.add_node("ingest_state", ingest_state)
workflow.add_node("execute_code", Executore_Node)
workflow.add_node("evaluate_code", evaluate_Node)

workflow.add_edge(START, "ingest_state")
workflow.add_edge("ingest_state", "execute_code")
workflow.add_edge("execute_code", "evaluate_code")
workflow.add_edge("evaluate_code", END)

app = workflow.compile()

if __name__ == "__main__":
    initial_state = {
        "goal": "Run a simple print statement",
        "current_code": 'print("Hello from LangGraph!")',
        "iteration_count": 1,
        "latest_metrics": {},
        "status": "",
        "execution_logs": [],
        "exit_code": 0
    }

    print("Starting LangGraph workflow...")
    final_state = app.invoke(initial_state)
    print("\n--- Final Output ---")
    print(f"Status: {final_state.get('status')}")
    print(f"Exit Code: {final_state.get('exit_code')}")
    print(f"Logs: {final_state.get('execution_logs')}")
