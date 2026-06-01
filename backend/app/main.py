from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import endpoints
from app.db.migrate import migrate_tinydb_to_sqlite

app = FastAPI(title="EcoSaur API", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    print("FastAPI Startup: Running database initialization and migration...")
    migrate_tinydb_to_sqlite()

# Allow Next.js frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router, prefix="/api/v1")

@app.get("/")
def read_root():
    # Trigger uvicorn reload
    return {"message": "Welcome to EcoSaur API"}
