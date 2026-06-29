import json
import os
import shutil

from fastapi import FastAPI, WebSocket, WebSocketDisconnect,UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from agent import graph

app = FastAPI(title = "AI Code Sandbox")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure the data directory exists
os.makedirs("./data", exist_ok=True)

@app.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Saves the uploaded dataset to the local ./data folder"""
    file_path = f"./data/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename, "message": "Successfully uploaded"}


@app.websocket("/ws/agent")
async def websocket_endpoint(websocket: WebSocket):

    await websocket.accept()

    try:
        data = await websocket.receive_text()
        payload = json.loads(data)

        initial_state = {
            "goal": payload.get("goal", "Calculate the square root of 144 without crashing."),
            "current_code": payload.get("code", "import math\nprint(10/0) # Bug!"),
            "iteration_count": 1,
            "latest_metrics": {},
            "status": "starting",
            "execution_logs": [],
            "exit_code": 0
        }

        await websocket.send_text(json.dumps({
            "node": "system",
            "message": "Agent loop started..."
        }))

        for output in graph.stream(initial_state):
             for node_name, state_update in output.items():
                
                response_payload = {
                    "node": node_name,
                    "data": state_update
                }

                await websocket.send_text(json.dumps(response_payload))
        
        await websocket.send_text(json.dumps({"node": "system", "message": "Agent finished execution."}))

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_text(json.dumps({"node": "error", "message": str(e)}))


html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Test API Bridge</title>
        <style>
            body { font-family: sans-serif; background: #1e1e1e; color: #d4d4d4; padding: 20px; }
            #logs { background: #000; padding: 10px; height: 500px; overflow-y: scroll; border-radius: 5px; font-family: monospace; }
            button { padding: 10px 20px; background: #007acc; color: white; border: none; cursor: pointer; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h2>🔌 WebSocket Test Client</h2>
        <button onclick="startAgent()">Trigger AI Agent</button>
        <br><br>
        <div id="logs"></div>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws/agent");
            var logs = document.getElementById("logs");
            
            ws.onmessage = function(event) {
                var message = document.createElement("div");
                message.textContent = event.data;
                message.style.borderBottom = "1px solid #333";
                message.style.padding = "5px 0";
                logs.appendChild(message);
                logs.scrollTop = logs.scrollHeight; // Auto-scroll to bottom
            };
            
            function startAgent() {
                logs.innerHTML = "";
                // Send a dummy payload to kick off the graph
                ws.send(JSON.stringify({
                    goal: "Calculate the square root of 144.",
                    code: "import math\\nprint(10/0)"
                }));
            }
        </script>
    </body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)