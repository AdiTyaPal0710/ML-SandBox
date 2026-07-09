import json
import os
import re
import shutil

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
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
DATA_DIR = os.path.abspath("./data")
os.makedirs(DATA_DIR, exist_ok=True)

# Upload constraints
ALLOWED_EXTENSIONS = {".csv", ".json"}
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def sanitize_filename(filename: str) -> str:
    """
    Strip path separators and dangerous characters from the filename.
    Prevents path traversal attacks like '../../etc/passwd'.
    """
    # Take only the basename (removes directory traversal)
    filename = os.path.basename(filename)
    # Remove any non-alphanumeric chars except dot, hyphen, underscore
    filename = re.sub(r"[^\w.\-]", "_", filename)
    # Collapse multiple underscores
    filename = re.sub(r"_+", "_", filename)
    # Don't allow hidden files
    filename = filename.lstrip(".")
    return filename or "upload"


@app.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Saves the uploaded dataset to the local ./data folder with validation."""

    # Validate filename exists
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    # Sanitize the filename
    safe_name = sanitize_filename(file.filename)

    # Validate extension
    _, ext = os.path.splitext(safe_name)
    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' is not allowed. Accepted: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file content and check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB."
        )

    # Write to data directory
    file_path = os.path.join(DATA_DIR, safe_name)
    with open(file_path, "wb") as buffer:
        buffer.write(content)

    return {"filename": safe_name, "message": "Successfully uploaded"}


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

        async for output in graph.astream(initial_state):
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
