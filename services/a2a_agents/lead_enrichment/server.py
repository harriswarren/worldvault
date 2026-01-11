import os
import time
import uuid
from typing import Dict, List, Optional

import httpx
from fastapi import FastAPI
from pydantic import BaseModel


APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")
APIFY_TASK_ID_ENRICH = os.getenv("APIFY_TASK_ID_ENRICH", "")
APIFY_BASE_URL = os.getenv("APIFY_BASE_URL", "https://api.apify.com")


class StartTaskRequest(BaseModel):
    lead_names: List[str]
    notes: Optional[str] = None


class TaskStatus(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, object]] = None


app = FastAPI(title="A2A Lead Enrichment Agent", version="0.1.0")

app.state.tasks = {}


def _stub_enrich(lead_names: List[str]) -> List[Dict[str, object]]:
    return [{"name": name, "company": "Acme Co", "role": "VP Growth"} for name in lead_names]


def _apify_enrich(lead_names: List[str], notes: Optional[str]) -> List[Dict[str, object]]:
    if not APIFY_TOKEN or not APIFY_TASK_ID_ENRICH:
        return _stub_enrich(lead_names)

    url = f"{APIFY_BASE_URL.rstrip('/')}/v2/actor-tasks/{APIFY_TASK_ID_ENRICH}/run-sync-get-dataset-items"
    params = {"token": APIFY_TOKEN}
    payload = {"lead_names": lead_names, "notes": notes}

    with httpx.Client(timeout=60.0) as client:
        response = client.post(url, params=params, json=payload)
        response.raise_for_status()
        items = response.json()
        if isinstance(items, list):
            return items
        return [items]


@app.post("/start_task", response_model=TaskStatus)
def start_task(request: StartTaskRequest) -> TaskStatus:
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    try:
        enriched = _apify_enrich(request.lead_names, request.notes)
        result = {"enriched": enriched, "completed_at": int(time.time()), "source": "apify"}
    except Exception:
        result = {"enriched": _stub_enrich(request.lead_names), "completed_at": int(time.time()), "source": "stub"}
    app.state.tasks[task_id] = {"status": "SUCCEEDED", "result": result}
    return TaskStatus(task_id=task_id, status="SUCCEEDED", result=result)


@app.get("/poll_task/{task_id}", response_model=TaskStatus)
def poll_task(task_id: str) -> TaskStatus:
    task = app.state.tasks.get(task_id)
    if not task:
        return TaskStatus(task_id=task_id, status="NOT_FOUND")
    return TaskStatus(task_id=task_id, status=task["status"], result=task["result"])
