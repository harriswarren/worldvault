import time
import uuid
from typing import Dict, Optional

from fastapi import FastAPI
from pydantic import BaseModel


class StartTaskRequest(BaseModel):
    subject_seed: str
    tone: Optional[str] = None


class TaskStatus(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, object]] = None


app = FastAPI(title="A2A Subject Optimizer Agent", version="0.1.0")

app.state.tasks = {}


@app.post("/start_task", response_model=TaskStatus)
def start_task(request: StartTaskRequest) -> TaskStatus:
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    optimized = f"{request.subject_seed} - personalized and concise"
    result = {
        "optimized_subject": optimized,
        "tone": request.tone or "direct",
        "completed_at": int(time.time()),
    }
    app.state.tasks[task_id] = {"status": "SUCCEEDED", "result": result}
    return TaskStatus(task_id=task_id, status="SUCCEEDED", result=result)


@app.get("/poll_task/{task_id}", response_model=TaskStatus)
def poll_task(task_id: str) -> TaskStatus:
    task = app.state.tasks.get(task_id)
    if not task:
        return TaskStatus(task_id=task_id, status="NOT_FOUND")
    return TaskStatus(task_id=task_id, status=task["status"], result=task["result"])
