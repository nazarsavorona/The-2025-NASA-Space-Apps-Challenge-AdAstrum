import csv
import json

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