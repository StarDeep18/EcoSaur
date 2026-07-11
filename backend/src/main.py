from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes import analyze, history, auth
from src.config.migrate import init_db

app = FastAPI(title="EcoSaur Upgraded API", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    print("FastAPI Startup: Running database initialization and seeding...")
    init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "*"  # Allow mobile devices to connect
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include refactored routes
app.include_router(analyze.router, prefix="/api/v1")
app.include_router(history.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to the production-ready EcoSaur API"}
