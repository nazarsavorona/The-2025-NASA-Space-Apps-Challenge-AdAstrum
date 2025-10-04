import csv
import json
import os

from fastapi import HTTPException
from starlette import status


def read_json(file: str) -> dict:
    try:
        with open(file, "r") as f:
            return json.load(f)
    except Exception as exs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file {file}: {exs}"
        )

def write_json(file: str, data: dict):
    try:
        with open(file, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as exs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to write JSON file {file}: {exs}"
        )

def read_csv(file: str):
    try:
        with open(file, "r", newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as exs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read CSV file {file}: {exs}"
        )


def write_csv(file: str, data: list, fieldnames: list):
    try:
        with open(file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    except Exception as exs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to write CSV file {file}: {exs}"
        )

def clear_dynamic_folder():
    """
        Clears the /dynamic/ folder by removing all files and subdirectories.
        """
    dynamic_dir = "/dynamic"
    if not os.path.exists(dynamic_dir):
        return {"status": "ok", "message": f"{dynamic_dir} does not exist."}

    try:
        for filename in os.listdir(dynamic_dir):
            file_path = os.path.join(dynamic_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.remove(file_path)
            except Exception as e:
                return {"status": "error", "message": str(e)}

        return {"status": "ok", "message": f"Cleared {dynamic_dir}/"}
    except Exception as e:
        return {"status": "error", "message": str(e)}