from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid

class WorkerInfo(BaseModel):
    worker_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    address: str # e.g., http://localhost:8001
    gpus: List[str] = ["SimulatedGPU-1"] # Simplified for example
    status: str = "available" # available, busy
    last_heartbeat: Optional[float] = None

class WorkUnit(BaseModel):
    work_unit_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    data_payload: Dict[str, Any] # e.g., { "numbers": [1, 2, 3, 4] }
    status: str = "pending" # pending, assigned, completed, failed
    assigned_to_worker_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

class Task(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_name: str
    model_config: Dict[str, Any] # Information about the "model"
    data_input: List[Dict[str, Any]] # "Data" for the task, will be split into work units
    status: str = "pending" # pending, processing, completed, failed
    work_units_ids: List[str] = []
    results_aggregated: Optional[Dict[str, Any]] = None

class TaskSubmission(BaseModel):
    task_name: str
    model_config: Dict[str, Any]
    data_input: List[Dict[str, Any]] # List of data "chunks"

class WorkUnitResult(BaseModel):
    work_unit_id: str
    worker_id: str
    output: Dict[str, Any]
