# 🏗️ ChatDev Integration - Visual Architecture & Workflow

## High-Level ChatDev Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                         USER REQUEST                                   │
│                  "Generate a REST API with auth"                       │
└────────────────┬───────────────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    AGENT TASK ROUTER                                   │
│                 (src/tools/agent_task_router.py)                       │
│                                                                        │
│  • Parse natural language task                                         │
│  • Determine task_type = "generate"                                    │
│  • Select target_system = "chatdev" (or auto)                          │
│  • Create OrchestrationTask with full context                          │
└────────────────┬───────────────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│         UNIFIED AI ORCHESTRATOR ROUTE DECISION                         │
│                                                                        │
│  IF task_type == "generate":                                           │
│      IF target_system in ["auto", "chatdev"]:                          │
│          ✓ Use ChatDev (multi-agent for complete project)              │
│      ELIF target_system == "factory":                                  │
│          ✓ Use ProjectFactory (intelligent provider selection)         │
│      ELIF target_system == "ollama":                                   │
│          ✓ Use Ollama (single model, can't create complete project)    │
│                                                                        │
│  ChatDev is OPTIMAL for generate tasks (full 5-agent pipeline)         │
└────────────────┬───────────────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│              _route_to_chatdev() HANDLER                               │
│         (src/tools/agent_task_router.py : lines 1642-1721)             │
│                                                                        │
│  1. Validate: task.task_type must be "generate"                        │
│  2. Import: from src.integration.chatdev_launcher import ChatDevLauncher
│  3. Extract parameters:                                                │
│     • project_name (from context or use default)                       │
│     • model (qwen2.5-coder:7b, :14b recommended)                       │
│     • organization (KiloFoolish or custom)                             │
│     • config (Default or custom config file)                           │
│  4. Launch: launcher.launch_chatdev(task, name, model, org, config)    │
│  5. Return: {status: "success", pid, project_name, model, ...}         │
└────────────────┬───────────────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│            CHATDEV LAUNCHER                                            │
│       (src/integration/chatdev_launcher.py)                            │
│                                                                        │
│  • Load KILO-FOOLISH secrets (API keys, configs)                       │
│  • Detect ChatDev path (searches multiple locations)                   │
│  • Verify ChatDev installation (run.py or run_ollama.py)               │
│  • Set up environment (OLLAMA_API_BASE, API keys, etc.)                │
│  • Spawn subprocess: python run_ollama.py --task --model --name ...    │
│  • Return process info (PID, status, project path)                     │
└────────────────┬───────────────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│         CHATDEV MULTI-AGENT TEAM EXECUTION                             │
│     (C:\\Users\\keath\\NuSyQ\\ChatDev)                                   │
│                                                                        │
│  STEP 1: CEO AGENT (Requirements Analysis)                             │
│  ───────────────────────────────────────                               │
│  Input: "Create a REST API with JWT authentication"                    │
│         + System prompt about product strategy                         │
│  Output:                                                               │
│    • Product Requirements Document (PRD)                               │
│    • Feature list                                                      │
│    • User stories                                                      │
│    • Success criteria                                                  │
│                                                                        │
│  STEP 2: CTO AGENT (Architecture Design)                               │
│  ────────────────────────────────────────                              │
│  Input: CEO's PRD                                                      │
│  Output:                                                               │
│    • Architecture diagram                                              │
│    • Technology stack choices (FastAPI, SQLAlchemy, pytest, etc.)      │
│    • File structure                                                    │
│    • Database schema                                                   │
│    • API endpoint definitions                                          │
│                                                                        │
│  STEP 3: PROGRAMMER AGENT (Code Development)                           │
│  ──────────────────────────────────────────                            │
│  Input: CTO's architecture                                             │
│  Output:                                                               │
│    • main.py (application entry point)                                 │
│    • models.py (SQLAlchemy ORM models)                                 │
│    • schemas.py (Pydantic validation schemas)                          │
│    • database.py (DB connection setup)                                 │
│    • auth.py (JWT token generation/validation)                         │
│    • routes/ (API endpoints)                                           │
│    • utils/ (helpers and utilities)                                    │
│                                                                        │
│  STEP 4: TESTER AGENT (Quality Assurance)                              │
│  ─────────────────────────────────────────                             │
│  Input: Programmer's code                                              │
│  Output:                                                               │
│    • test_main.py (main functionality tests)                           │
│    • test_auth.py (authentication tests)                               │
│    • test_models.py (ORM model tests)                                  │
│    • test_api.py (endpoint tests with fixtures)                        │
│    • Test execution results (pass/fail)                                │
│    • Coverage report (what % of code is tested)                        │
│                                                                        │
│  STEP 5: REVIEWER AGENT (Code Quality Inspection)                      │
│  ──────────────────────────────────────────────                        │
│  Input: Code, tests, architecture                                      │
│  Output:                                                               │
│    • Code style review (PEP 8 compliance)                              │
│    • Security analysis (SQL injection, auth flaws, etc.)               │
│    • Performance review (N+1 queries, inefficient loops)               │
│    • Maintainability analysis (technical debt, complexity)             │
│    • Final approval or required fixes                                  │
│                                                                        │
│  Process Flow:                                                         │
│    CEO → CTO → PROGRAMMER → TESTER → REVIEWER                          │
│    │      │      │           │         │                              │
│    └──────┴──────┴───────────┴─────────┘ (Each provides feedback)      │
│                                                                        │
│  Iterative: If TESTER finds bugs → PROGRAMMER fixes → RE-TEST         │
└────────────────┬───────────────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│          PROJECT GENERATED & SAVED TO WAREHOUSE                        │
│     C:\\Users\\keath\\NuSyQ\\ChatDev\\WareHouse\\RestAPI_20260216_120000  │
│                                                                        │
│  Generated Project Structure:                                          │
│  ───────────────────────────                                           │
│  RestAPI_20260216_120000/                                              │
│  ├── .env.example                    (Environment template)            │
│  ├── .gitignore                      (Git ignore patterns)             │
│  ├── requirements.txt                (Python dependencies)             │
│  ├── README.md                       (Complete documentation)          │
│  ├── main.py                         (FastAPI application)             │
│  ├── models.py                       (SQLAlchemy models)               │
│  ├── schemas.py                      (Pydantic schemas)                │
│  ├── database.py                     (DB configuration)                │
│  ├── auth.py                         (JWT authentication)              │
│  ├── config/                         (Configuration files)             │
│  │   └── config.py                                                    │
│  ├── routes/                         (API endpoints)                   │
│  │   ├── __init__.py                                                 │
│  │   ├── users.py                    (User endpoints)                 │
│  │   ├── posts.py                    (Post endpoints)                 │
│  │   └── auth.py                     (Auth endpoints)                 │
│  ├── utils/                          (Helper functions)                │
│  │   ├── __init__.py                                                 │
│  │   └── helpers.py                                                  │
│  ├── tests/                          (Test suite)                      │
│  │   ├── __init__.py                                                 │
│  │   ├── conftest.py                 (Pytest fixtures)                │
│  │   ├── test_main.py                (Main tests)                     │
│  │   ├── test_auth.py                (Auth tests)                     │
│  │   ├── test_models.py              (Model tests)                    │
│  │   └── test_api.py                 (Endpoint tests)                 │
│  └── docs/                           (Generated documentation)         │
│      └── API.md                      (API specification)              │
│                                                                        │
│  Key Features:                                                         │
│  ✅ Complete, runnable, production-ready code                         │
│  ✅ Comprehensive test suite (pytest)                                  │
│  ✅ Type hints throughout (for IDE autocomplete)                       │
│  ✅ Error handling (try/except, validation)                            │
│  ✅ Database migrations (if SQL used)                                  │
│  ✅ API documentation (docstrings)                                     │
│  ✅ Requirements.txt with pinned versions                              │
│  ✅ README with setup instructions                                     │
│  ✅ .env.example for configuration                                     │
│  ✅ .gitignore for safety                                              │
│                                                                        │
│  Can immediately run:                                                  │
│  $ cd RestAPI_20260216_120000                                          │
│  $ pip install -r requirements.txt                                     │
│  $ python main.py                    # Start server                    │
│  $ pytest                            # Run tests                       │
└────────────────┬───────────────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│           RESULT RETURNED TO USER                                      │
│                                                                        │
│  {                                                                      │
│    "status": "success",                                                │
│    "system": "chatdev",                                                │
│    "output": {                                                        │
│      "pid": 12345,                                                    │
│      "project_name": "RestAPI",                                       │
│      "model": "qwen2.5-coder:7b",                                     │
│      "organization": "KiloFoolish",                                   │
│      "config": "Default",                                             │
│      "api_key_configured": true,                                      │
│      "chatdev_path": "C:\\Users\\keath\\NuSyQ\\ChatDev"               │
│    },                                                                  │
│    "note": "ChatDev process launched; monitor logs for completion.",  │
│    "task_id": "agent_20260216_120000"                                 │
│  }                                                                     │
│                                                                        │
│  Next Steps:                                                           │
│  1. Monitor ChatDev process (PID 12345)                                │
│  2. Check WareHouse for generated project                              │
│  3. Run tests: cd WareHouse/RestAPI_* && pytest                        │
│  4. Start server: python main.py                                       │
│  5. Access API: http://localhost:8000                                  │
│  6. View docs: http://localhost:8000/docs                              │
└────────────────────────────────────────────────────────────────────────┘
```

---

## ChatDev in System Context: Where It Fits

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     COMPLETE ECOSYSTEM                                  │
└─────────────────────────────────────────────────────────────────────────┘

                        UNIFIED AI ORCHESTRATOR
                        ═══════════════════════

                ┌───────────────────────────────────────┐
                │    AGENT TASK ROUTER                  │
                │  (Natural Language Interface)         │
                │                                       │
                │  • Parses: "Generate", "Analyze",    │
                │    "Review", "Debug", "Plan"          │
                │                                       │
                │  • Routes to optimal system:           │
                │    ├─ "Generate" → ChatDev (5-agent) │
                │    ├─ "Analyze" → Ollama (fast)      │
                │    ├─ "Debug" → Quantum (healing)    │
                │    ├─ "Plan" → Ollama + Consciousness│
                │    └─ "Review" → Ollama (code review)│
                └───────────────┬───────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
   ┌─────────┐             ┌──────────┐         ┌────────────┐
   │ChatDev  │             │ Ollama   │         │ Quantum    │
   │ 5-Agent │             │10 Models │         │Resolver    │
   │  Team   │             │          │         │ (Healing)  │
   ├─────────┤             ├──────────┤         ├────────────┤
   │ Generate│             │Analyze   │         │Fix errors  │
   │Complete │             │Review    │         │Heal system │
   │Projects │             │Debug     │         │Optimize    │
   │         │             │Plan      │         │            │
   │         │             │Document  │         │            │
   │CEO      │             │          │         │            │
   │CTO      │             │qwen2.5   │         │Import fix  │
   │Program  │             │llama3.1  │         │Path repair │
   │Tester   │             │starcoder │         │            │
   │Reviewer │             │deepseek  │         │            │
   └─────────┘             └──────────┘         └────────────┘
        │                       │                       │
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                                ▼
                    ┌───────────────────────────┐
                    │ CONSCIOUSNESS BRIDGE      │
                    │ (Memory & Context)        │
                    │                           │
                    │ • Memory Palace           │
                    │ • Context Synthesis       │
                    │ • Lessons Learned         │
                    │ • Decision History        │
                    └───────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────────┐
                    │ QUEST LOG                 │
                    │ (Persistent Memory)       │
                    │                           │
                    │ • All tasks logged        │
                    │ • Results persisted       │
                    │ • Patterns captured       │
                    │ • Lessons stored          │
                    └───────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────────┐
                    │ AUTONOMOUS LOOP           │
                    │ (Continuous Improvement)  │
                    │                           │
                    │ • Analyze                 │
                    │ • Diagnose                │
                    │ • Plan                    │
                    │ • Execute                 │
                    │ • Validate                │
                    │ • Queue next steps        │
                    └───────────────────────────┘
```

---

## ChatDev Request Flow: Complete Sequence

```
TIME    COMPONENT                  ACTION
────────────────────────────────────────────────────────────────────

 0ms    User/Agent                 "Generate a REST API with FastAPI"
        ↓
 10ms   AgentTaskRouter            Parse request
        ↓                          Create OrchestrationTask
        ↓                          task_type="generate"
        ↓                          target_system="chatdev"
        ↓
 20ms   UnifiedAIOrchestrator      Route decision
        ↓                          Task → _route_to_chatdev()
        ↓
 30ms   ChatDev Handler            Extract parameters
        ↓                          Validate: task_type == "generate"
        ↓                          Load ChatDevLauncher
        ↓
 40ms   ChatDevLauncher            Find ChatDev installation
        ↓                          Load KILO secrets
        ↓                          Resolve API keys
        ↓                          Set environment
        ↓
 50ms   Subprocess Spawn           Launch: python run_ollama.py ...
        ↓                          Model: qwen2.5-coder:7b
        ↓                          Task: "Create REST API"
        ↓                          PID: 12345
        ↓
        ┌────────────────────────────────────────────────────────┐
        │   CHATDEV MULTI-AGENT EXECUTION (in parallel with UI)  │
        └────────────────────────────────────────────────────────┘
        
 100ms  CEO Agent                  Read task
        ↓                          Analyze requirements
        ↓                          Generate PRD
        ↓
 200ms  CTO Agent                  Read CEO output
        ↓                          Design architecture
        ↓                          Select technology stack
        ↓                          Create file structure
        ↓
 400ms  Programmer Agent           Read CTO design
        ↓                          Write all code files
        ↓                          Type hints, validation
        ↓                          Error handling
        ↓
 800ms  Tester Agent               Run pytest
        ↓                          Generate test files
        ↓                          Validate coverage
        ↓                          Report failures
        ↓
1000ms  Reviewer Agent             Code quality check
        ↓                          Security audit
        ↓                          Performance review
        ↓                          Final signoff
        ↓
 
1200ms  File System                Save to WareHouse
        ↓                          Create timestamp folder
        ↓                          Write all files
        ↓                          tests/, routes/, etc.
        │
        ↓ (Back to main execution)
        
1210ms  Return to Router           Process finished
        ↓                          Get results
        ↓                          Return success response
        ↓
1220ms  Return to User             {"status": "success", ...}
        ↓
        Show: Project ready at WareHouse/RestAPI_20260216_120000/
        Show: All agents completed
        Show: Tests passed
        Show: Ready to run/test/deploy
```

---

## Parameter Mapping: User Request → ChatDev Call

```
User Request:
  "Generate a Python async web scraper with error handling"
  
         │
         ▼
         
AgentTaskRouter.route_task(
    task_type="generate",
    description="Python async web scraper with error handling",
    context={
        "project_name": "WebScraper",
        "chatdev_model": "qwen2.5-coder:7b",
        "organization": "NuSyQ"
    },
    target_system="auto"  # Auto-detects ChatDev
)

         │
         ▼
         
_route_to_chatdev() extracts:
    • project_name = "WebScraper"
    • model = "qwen2.5-coder:7b"
    • organization = "NuSyQ"
    • config = "Default"
    • task = "Python async web scraper with error handling"

         │
         ▼
         
ChatDevLauncher.launch_chatdev(
    task="Python async web scraper with error handling",
    name="WebScraper",
    model="qwen2.5-coder:7b",
    organization="NuSyQ",
    config="Default"
)

         │
         ▼
         
Actual Command Spawned:
    python run_ollama.py \
      --task "Python async web scraper with error handling" \
      --name "WebScraper" \
      --model "qwen2.5-coder:7b" \
      --organization "NuSyQ" \
      --config "Default"

         │
         ▼
         
ChatDev 5-Agent Pipeline Executes
    CEO → CTO → Programmer → Tester → Reviewer

         │
         ▼
         
Output Saved:
    WareHouse/WebScraper_20260216_120000/
    ├── main.py (async scraper logic)
    ├── models.py (data models)
    ├── utils.py (error handling utilities)
    ├── requirements.txt (aiohttp, beautifulsoup4, etc)
    ├── tests/
    │   ├── test_scraper.py
    │   ├── test_error_handling.py
    │   └── test_models.py
    └── README.md (usage instructions)
```

---

## Error & Fallback Handling in ChatDev Routing

```
_route_to_chatdev(task) 
  │
  ├─────────────────────────────────────────────────────┐
  │ Validation Check                                    │
  │ if task.task_type != "generate":                    │
  │     ↓ Return ERROR                                  │
  │     "ChatDev only supports 'generate' task type"    │
  └─────────────────────────────────────────────────────┘
  │
  ├─────────────────────────────────────────────────────┐
  │ Try: Import ChatDevLauncher                         │
  │ except ImportError:                                 │
  │     ↓ Fall back to FACTORY FALLBACK                 │
  │     Try ProjectFactory instead                      │
  └─────────────────────────────────────────────────────┘
  │
  ├─────────────────────────────────────────────────────┐
  │ Try: launcher.launch_chatdev()                      │
  │ except FileNotFoundError:                           │
  │     ↓ Fall back to FACTORY FALLBACK                 │
  │     ChatDev path not found, try ProjectFactory      │
  └─────────────────────────────────────────────────────┘
  │
  ├─────────────────────────────────────────────────────┐
  │ Try: launcher.launch_chatdev()                      │
  │ except RuntimeError as e:                           │
  │     ↓ Fall back to FACTORY FALLBACK                 │
  │     ChatDev launch failed: {e}                      │
  └─────────────────────────────────────────────────────┘
  │
  ├─────────────────────────────────────────────────────┐
  │ Try: launcher.launch_chatdev()                      │
  │ except (ValueError, TypeError) as e:                │
  │     ↓ Fall back to FACTORY FALLBACK                 │
  │     ChatDev parameter error: {e}                    │
  └─────────────────────────────────────────────────────┘
  │
  └─→ Success!
      {
          "status": "success",
          "system": "chatdev",
          "output": {
              "pid": 12345,
              "project_name": "WebScraper",
              ...
          }
      }

Fallback to Factory if all ChatDev attempts fail:
    ProjectFactory.create_project(
        task,
        intelligent_provider_selection=True
        # Factory chooses: ChatDev > Ollama > Claude > OpenAI
        # Based on: complexity, offline needs, budget
    )
```

---

## Real Example: ChatDev Generation Output

### Request:
```bash
python scripts/start_nusyq.py generate "Create a FastAPI todo list API with user authentication and database"
```

### Generated Project Structure (5-20 minutes):

```
WareHouse/TodoAPI_20260216_102300/
│
├── .env.example
│   # OLLAMA_API_BASE=http://localhost:11434
│   # DATABASE_URL=sqlite:///todos.db
│   # SECRET_KEY=your-secret-key
│
├── requirements.txt
│   # FastAPI==0.109.0
│   # SQLAlchemy==2.0.25
│   # Pydantic==2.5.1
│   # pytest==7.4.3
│   # aiohttp==3.9.1
│
├── main.py (FastAPI application)
│   # def main():
│   #     app = FastAPI(title="Todo API")
│   #     ...setup routes...
│   #     uvicorn.run(app, host="127.0.0.1", port=8000)
│
├── models.py (SQLAlchemy ORM)
│   # class User(Base):
│   #     id = Column(Integer, primary_key=True)
│   #     email = Column(String, unique=True)
│   #     hashed_password = Column(String)
│   #     todos = relationship("Todo", back_populates="owner")
│   #
│   # class Todo(Base):
│   #     id = Column(Integer, primary_key=True)
│   #     title = Column(String)
│   #     completed = Column(Boolean, default=False)
│
├── schemas.py (Pydantic validation)
│   # class UserCreate(BaseModel):
│   #     email: str
│   #     password: str
│   #
│   # class TodoCreate(BaseModel):
│   #     title: str
│   #     description: Optional[str] = None
│
├── auth.py (JWT authentication)
│   # def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
│   #     to_encode = data.copy()
│   #     expire = datetime.utcnow() + expires_delta
│   #     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
│   #     return encoded_jwt
│
├── database.py
│   # DATABASE_URL = "sqlite:///./test.db"
│   # engine = create_engine(DATABASE_URL, connect_args=...)
│   # SessionLocal = sessionmaker(bind=engine)
│
├── routes/
│   ├── users.py
│   │   # @router.post("/register")
│   │   # def register(user: UserCreate):
│   │   #     # Hash password, create user in DB
│   │   #     return {"message": "User created"}
│   │   #
│   │   # @router.post("/login")
│   │   # def login(user: UserCreate):
│   │   #     # Verify credentials, create JWT token
│   │   #     return {"access_token": token}
│   │
│   └── todos.py
│       # @router.get("/todos")
│       # def get_todos(current_user = Depends(get_current_user)):
│       #     return db.query(Todo).filter(Todo.owner_id == current_user.id).all()
│       #
│       # @router.post("/todos")
│       # def create_todo(todo: TodoCreate, current_user = Depends(get_current_user)):
│       #     db_todo = Todo(title=todo.title, owner_id=current_user.id)
│       #     db.add(db_todo)
│       #     db.commit()
│       #     return db_todo
│
├── tests/
│   ├── conftest.py
│   │   # @pytest.fixture
│   │   # def client():
│   │   #     app.dependency_overrides[get_db] = override_get_db
│   │   #     return TestClient(app)
│   │
│   ├── test_auth.py
│   │   # def test_register(client):
│   │   #     response = client.post("/users/register", json={...})
│   │   #     assert response.status_code == 201
│   │   #
│   │   # def test_login(client):
│   │   #     response = client.post("/users/login", json={...})
│   │   #     assert "access_token" in response.json()
│   │
│   ├── test_todos.py
│   │   # def test_create_todo(client, auth_headers):
│   │   #     response = client.post("/todos", headers=auth_headers, json={...})
│   │   #     assert response.status_code == 201
│   │   #
│   │   # def test_get_todos(client, auth_headers):
│   │   #     response = client.get("/todos", headers=auth_headers)
│   │   #     assert response.status_code == 200
│   │   #     assert isinstance(response.json(), list)
│   │
│   └── test_models.py
│       # def test_user_creation():
│       #     user = User(email="test@test.com", hashed_password="...")
│       #     assert user.email == "test@test.com"
│
├── README.md
│   # # Todo API
│   # 
│   # A FastAPI-based REST API for managing todos with user authentication.
│   #
│   # ## Setup
│   # ```bash
│   # pip install -r requirements.txt
│   # python main.py
│   # ```
│   #
│   # ## API Endpoints
│   # POST /users/register     - Create new user
│   # POST /users/login        - Get JWT token
│   # POST /todos              - Create todo
│   # GET /todos               - List user's todos
│   # PUT /todos/{id}          - Update todo
│   # DELETE /todos/{id}       - Delete todo
│   #
│   # ## Testing
│   # ```bash
│   # pytest
│   # ```
│
└── docs/
    └── API.md (Auto-generated API documentation)
```

### Ready to use immediately:
```bash
cd WareHouse/TodoAPI_20260216_102300/

# 1. Install dependencies
pip install -r requirements.txt

# 2. Run tests
pytest

# 3. Start server
python main.py
# Server running at http://localhost:8000

# 4. View interactive API docs
# Open: http://localhost:8000/docs
```

---

This is what ChatDev integration provides: **complete, tested, production-ready projects generated by a 5-agent team in minutes**.

