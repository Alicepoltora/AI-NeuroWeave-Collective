# AI-NeuroWeave-Collective
Collective ai
neuro_weave_collective/
├── server/
│   ├── main.py             # FastAPI приложение, оркестратор, менеджер ресурсов, агрегатор
│   ├── models.py           # Pydantic модели для данных
│   └── requirements.txt
├── client/
│   ├── client.py           # "Ткач" - клиентское приложение
│   └── requirements.txt
├── task_submitter/
│   ├── submit_task.py      # Скрипт для "Заказчика" для отправки задачи
│   └── requirements.txt
└── README.md
