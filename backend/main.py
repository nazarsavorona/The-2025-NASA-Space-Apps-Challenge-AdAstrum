import logging
from io import BytesIO
from typing import Dict, Any

import aiofiles
import pandas as pd
from fastapi import APIRouter, FastAPI, UploadFile, HTTPException, status
from pathlib import Path

from model_api_mock import call_model
from preprocess import get_dataframe_format

app = FastAPI()

USER_FILE = "dynamic/user-data.csv"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@app.get("/")
def read_root():
    return {"message": "Hello, AdAstrum!"}


@app.post("/upload/")
async def upload(file: UploadFile | None):

    filepath = Path(USER_FILE)
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

@app.post("/predict/")
async def get_result_for_file(hyperparams: str | None=None):
    try:
        df = pd.read_csv(USER_FILE)
        data_format = get_dataframe_format(df)
    except Exception as exs:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exs
        )
    return call_model(data_format, df, hyperparams)

@app.post("/run-for-csv/")
async def get_result_for_file(file: UploadFile | None, hyperparams: str | None=None):
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
