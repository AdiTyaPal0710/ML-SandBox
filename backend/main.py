import json
import os
import shutil

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
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
            "goal": payload.get("goal", ""),
            "current_code": payload.get("code", ""),
            "requirements": payload.get("requirements", ""),
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
