import logging
import aiofiles
from fastapi import APIRouter, FastAPI, UploadFile, HTTPException, status
from pathlib import Path

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@app.get("/")
def read_root():
    return {"message": "Hello, AdAstrum!"}

@app.post("/start-session/")
async def start_session(file: UploadFile | None):
    filename = "dynamic/user-data.csv"
    filepath = Path(filename)
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
