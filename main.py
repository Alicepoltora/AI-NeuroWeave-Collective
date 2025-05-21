from fastapi import FastAPI, HTTPException, BackgroundTasks
from typing import Dict, List
import time
import httpx # For sending tasks to clients (in a real system, client would pull)

from models import WorkerInfo, WorkUnit, Task, TaskSubmission, WorkUnitResult

app = FastAPI(title="NeuroWeave Orchestrator")

# In-memory "databases" - IN A REAL SYSTEM, THIS WOULD BE A DATABASE!
WORKERS_DB: Dict[str, WorkerInfo] = {}
TASKS_DB: Dict[str, Task] = {}
WORK_UNITS_DB: Dict[str, WorkUnit] = {}
PENDING_WORK_UNITS_QUEUE: List[str] = [] # IDs of work units

# --- Resource Manager ---
@app.post("/workers/register", response_model=WorkerInfo)
async def register_worker(worker_info: WorkerInfo):
    if worker_info.worker_id in WORKERS_DB:
        raise HTTPException(status_code=400, detail="Worker already registered")
    worker_info.last_heartbeat = time.time()
    WORKERS_DB[worker_info.worker_id] = worker_info
    print(f"Worker registered: {worker_info.worker_id} at {worker_info.address}")
    return worker_info

@app.post("/workers/{worker_id}/heartbeat")
async def worker_heartbeat(worker_id: str):
    if worker_id not in WORKERS_DB:
        raise HTTPException(status_code=404, detail="Worker not found")
    WORKERS_DB[worker_id].last_heartbeat = time.time()
    WORKERS_DB[worker_id].status = "available" # Assume worker is available after heartbeat
    print(f"Heartbeat from {worker_id}")
    return {"message": "Heartbeat received"}

# --- Task Orchestrator ---
@app.post("/tasks", response_model=Task, status_code=201)
async def submit_task(task_submission: TaskSubmission, background_tasks: BackgroundTasks):
    task = Task(
        task_name=task_submission.task_name,
        model_config=task_submission.model_config,
        data_input=task_submission.data_input # Stored, but used directly for this example
    )
    TASKS_DB[task.task_id] = task
    print(f"Task submitted: {task.task_id} - {task.task_name}")

    # Split task into work units
    for i, data_chunk in enumerate(task_submission.data_input):
        work_unit = WorkUnit(
            task_id=task.task_id,
            data_payload=data_chunk # Each element of data_input becomes a work unit
        )
        WORK_UNITS_DB[work_unit.work_unit_id] = work_unit
        task.work_units_ids.append(work_unit.work_unit_id)
        PENDING_WORK_UNITS_QUEUE.append(work_unit.work_unit_id)
    
    TASKS_DB[task.task_id].status = "processing"
    print(f"Task {task.task_id} split into {len(task.work_units_ids)} work units.")
    
    # Start a background task to distribute work units (clients will pull in this version)
    # background_tasks.add_task(distribute_work_units_push_style) # Kept for reference, but not primary
    return task

@app.get("/work_units/request", response_model=WorkUnit)
async def request_work_unit(worker_id: str):
    if worker_id not in WORKERS_DB:
        raise HTTPException(status_code=404, detail="Worker not registered")
    if WORKERS_DB[worker_id].status != "available":
        # This might happen if server thinks worker is busy but worker requests again
        # Could be a race condition or a previous task failed on worker side without server knowing
        print(f"Warning: Worker {worker_id} requested work but status is {WORKERS_DB[worker_id].status}")
        # For simplicity, we'll allow it if there's work. In a real system, this needs careful handling.
        # raise HTTPException(status_code=409, detail="Worker is busy or unavailable")


    if not PENDING_WORK_UNITS_QUEUE:
        raise HTTPException(status_code=404, detail="No pending work units")

    work_unit_id = PENDING_WORK_UNITS_QUEUE.pop(0) # Get the first one from the queue
    work_unit = WORK_UNITS_DB[work_unit_id]
    
    work_unit.status = "assigned"
    work_unit.assigned_to_worker_id = worker_id
    WORKERS_DB[worker_id].status = "busy" # Mark worker as busy
    
    print(f"Assigned WorkUnit {work_unit.work_unit_id} to Worker {worker_id}")
    return work_unit

# --- Result Aggregator ---
@app.post("/work_units/submit_result")
async def submit_work_unit_result(result: WorkUnitResult, background_tasks: BackgroundTasks): # Added background_tasks
    if result.work_unit_id not in WORK_UNITS_DB:
        raise HTTPException(status_code=404, detail="Work unit not found")
    if result.worker_id not in WORKERS_DB:
        raise HTTPException(status_code=404, detail="Worker not found")

    work_unit = WORK_UNITS_DB[result.work_unit_id]
    if work_unit.assigned_to_worker_id != result.worker_id:
        # This could happen if work was reassigned or there's a stale request
        print(f"Warning: Result for {result.work_unit_id} submitted by {result.worker_id} but was assigned to {work_unit.assigned_to_worker_id}")
        # For simplicity, we'll accept it if the unit is still 'assigned'.
        # In a real system, verify if the current assignee matches.
        if work_unit.status != "assigned": # Or if it was already completed/failed by another
             raise HTTPException(status_code=403, detail="Worker not currently assigned to this work unit or unit already processed")

    work_unit.result = result.output
    work_unit.status = "completed"
    WORKERS_DB[result.worker_id].status = "available" # Free up the worker

    print(f"Result received for WorkUnit {result.work_unit_id} from Worker {result.worker_id}: {result.output}")
    
    # Check if all work units for the task are completed
    task = TASKS_DB.get(work_unit.task_id)
    if task:
        all_completed = True
        aggregated_results = [] # Simple aggregation: collect all results
        for wu_id in task.work_units_ids:
            current_wu = WORK_UNITS_DB[wu_id]
            if current_wu.status != "completed":
                all_completed = False
                break
            if current_wu.result: # Make sure result exists
                 aggregated_results.append(current_wu.result)

        if all_completed:
            task.status = "completed"
            # Actual aggregation logic would go here. For now, just collect everything.
            task.results_aggregated = {"all_outputs": aggregated_results}
            print(f"Task {task.task_id} completed! Aggregated results: {task.results_aggregated}")
    
    # After receiving a result, try to distribute more work (if any clients are polling)
    # No explicit push needed here as clients will poll /work_units/request
    return {"message": "Result received"}

@app.get("/tasks/{task_id}", response_model=Task)
async def get_task_status(task_id: str):
    if task_id not in TASKS_DB:
        raise HTTPException(status_code=404, detail="Task not found")
    return TASKS_DB[task_id]

# --- Helper function for push-style distribution (simplified, kept for reference) ---
# In a more robust system, clients would poll for work.
# This function is illustrative of a push model but has limitations.
# The primary mechanism in this version is clients polling `/work_units/request`.
async def distribute_work_units_push_style(): # Renamed to avoid confusion
    print("Attempting push-style distribution (for reference, primary is pull)...")
    # This function is largely superseded by clients pulling tasks.
    # It's kept as an example of a push mechanism.
    # for worker_id, worker_info in WORKERS_DB.items():
    #     if worker_info.status == "available" and PENDING_WORK_UNITS_QUEUE:
    #         work_unit_id = PENDING_WORK_UNITS_QUEUE.pop(0)
    #         work_unit = WORK_UNITS_DB[work_unit_id]
    #         work_unit.status = "assigned"
    #         work_unit.assigned_to_worker_id = worker_id
    #         worker_info.status = "busy"
    #         print(f"Pushing WorkUnit {work_unit.work_unit_id} to Worker {worker_id} at {worker_info.address}")
    #         try:
    #             async with httpx.AsyncClient() as client_http: # Renamed to avoid conflict
    #                 # Client needs an endpoint to receive tasks (not implemented in this client version)
    #                 # This is a conceptual push; the current client pulls work.
    #                 # await client_http.post(f"{worker_info.address}/execute_work_pushed", json=work_unit.model_dump(), timeout=5.0)
    #                 print(f"Conceptual push to {worker_info.address} - client needs /execute_work_pushed endpoint")
    #         except Exception as e:
    #             print(f"Failed to send work via push to {worker_id}: {e}")
    #             # Return work unit to queue and mark worker as potentially unavailable
    #             PENDING_WORK_UNITS_QUEUE.insert(0, work_unit_id)
    #             work_unit.status = "pending"
    #             work_unit.assigned_to_worker_id = None
    #             # worker_info.status = "unavailable" # Or some other status
    #         return # Only one at a time for simplicity in this example
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
