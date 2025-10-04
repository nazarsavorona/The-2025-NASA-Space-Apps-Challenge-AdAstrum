import logging
from io import BytesIO
from typing import Dict

import aiofiles
import pandas as pd
from fastapi import APIRouter, FastAPI, UploadFile, HTTPException, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from model_api_mock import call_model
from preprocess import get_dataframe_format
import uuid

from utils import write_json, read_json, clear_dynamic_folder

def exoplanets_file(session_name: str):
    return f"dynamic/{session_name}-exoplanets.csv"

def hyperparams_file(session_name: str):
    return f"dynamic/{session_name}-hyperparams.json"
app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.delete("/clear-dynamic")
async def clear_dynamic():
    clear_dynamic_folder()

@app.middleware("http")
async def add_session_id(request: Request, call_next):
    session_id = request.cookies.get("session_id")
    print(session_id)
    if not session_id:
        session_id = str(uuid.uuid4())

    request.state.session_id = session_id

    response: Response = await call_next(request)

    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=True
    )
    return response
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "http://localhost:63343",
    "http://127.0.0.1:63343",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def read_root():
    return {"message": "Hello, AdAstrum!"}


@app.post("/upload/")
async def upload(request: Request, file: UploadFile | None):
    session_id = request.state.session_id
    print(session_id)
    print(request)
    filepath = Path(exoplanets_file(session_id))
    if file:
        try:
            async with aiofiles.open(filepath, "wb") as out_file:
                while chunk := await file.read(1024 * 1024):  # 1 MB chunks
                    await out_file.write(chunk)
            logger.info("Session file saved successfully: %s", filepath)
            return {"message": "File uploaded successfully"}, status.HTTP_201_CREATED
        except Exception as exc:
            logger.error("Failed to save session file: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save session file"
            ) from exc

    else:
        try:
            if filepath.exists():
                filepath.unlink()
                logger.info("Session file removed: %s", filepath)
            else:
                logger.info("No session file found to remove")
            return status.HTTP_204_NO_CONTENT
        except Exception as exc:
            logger.error("Failed to remove session file: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove session file"
            ) from exc

@app.post("/hyperparams/")
async def set_hyperparams(request: Request, hyperparams: Dict):
    session_id = request.state.session_id
    hyperparams_f = hyperparams_file(session_id)
    write_json(hyperparams_f, hyperparams)
    return status.HTTP_201_CREATED

@app.post("/predict/")
async def get_result_for_file(request: Request):
    session_id = request.state.session_id
    planet_file = exoplanets_file(session_id)
    hyperparams_f = hyperparams_file(session_id)
    try:
        df = pd.read_csv(planet_file)
        hyperparams = read_json(hyperparams_f)
    except Exception as exs:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=exs
        )
    try:
        data_format = get_dataframe_format(df)
    except Exception as exs:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exs
        )
    return call_model(data_format, df, hyperparams)

@app.post("/test-endpoint/")
async def test_endpoint(file: UploadFile | None, hyperparams: dict | None=None):

    if hyperparams is None:
        hyperparams = {
            "candidate_threshold": 0.2,
            "confirmed_threshold": 0.5,
        }

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    try:
        contents = await file.read()
        df = pd.read_csv(BytesIO(contents))
        data_format = get_dataframe_format(df)
    except Exception as exs:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exs
        )
    return call_model(data_format, df, hyperparams)
