## Structure

*   `server/`: Orchestrator, resource manager, and result aggregator (FastAPI).
*   `client/`: "Weaver" client application that executes tasks.
*   `task_submitter/`: "Requester" script to submit tasks to the server.

## How to Run

1.  **Install dependencies for each module:**
    Open your terminal and navigate to the project's root directory.
    ```bash
    pip install -r server/requirements.txt
    pip install -r client/requirements.txt
    pip install -r task_submitter/requirements.txt
    ```

2.  **Start the Server:**
    Open a terminal, navigate to the `server/` directory, and run:
    ```bash
    python main.py
    # or for development: uvicorn main:app --reload
    ```
    The server will listen on `http://localhost:8000`.

3.  **Start one or more Clients ("Weavers"):**
    Open a new terminal (or multiple terminals) for each client. Navigate to the `client/` directory and run:
    ```bash
    python client.py
    ```
    Each client will register with the server and start polling for work. Client IDs are generated automatically.

4.  **Submit a Task using the "Requester" script:**
    Open another terminal, navigate to the `task_submitter/` directory, and run:
    ```bash
    python submit_task.py
    ```
    This script will submit a sample task to the server. You should see logs in the server and client terminals as the task is broken down into work units, distributed, and executed. The `submit_task.py` script will periodically poll for the task's status.

## What's Next? (Directions for Development)

This skeleton is just a starting point. A real system would require:

*   **Database:** Replace in-memory dictionaries with a persistent database (e.g., PostgreSQL, MongoDB).
*   **Real Sandbox:** Use Docker or another containerization technology for secure code execution on clients.
*   **Actual ML Tasks:** Integrate PyTorch/TensorFlow for model training.
*   **Robustness:** Error handling, retries, fault tolerance.
*   **Security:** Authentication, authorization, encryption, protection against malicious code.
*   **Scalability:** Optimization for a large number of clients and tasks.
*   **Advanced Orchestrator:** Smarter task distribution, considering client GPU capabilities.
*   **Incentive System:** Tokenomics, reputation.
*   **User Interface:** GUI for clients and a web portal for requesters.
*   **Asynchronous Communication:** Use WebSockets or message queues (Kafka, RabbitMQ) for more efficient communication instead of constant polling.
