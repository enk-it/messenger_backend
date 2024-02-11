from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from fastapi import FastAPI
from pyfiles.routes import router

app = FastAPI()

origins = [
    "http://localhost",

    "http://localhost:8080",
    "http://localhost:3000",

    "http://192.168.0.12:8000",
    "http://192.168.0.12:3000",

    "http://192.168.0.17:8000",
    "http://192.168.0.17:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    # uvicorn.run(app, host="127.0.0.1", port=8000)
    uvicorn.run(app, host="192.168.0.12", port=8000, ws_ping_interval=1000, ws_ping_timeout=500) # debug
    # uvicorn.run(app, host="192.168.0.17", port=8000, ws_ping_interval=1000, ws_ping_timeout=500) # production
#