import pandas
import requests

async def call_model(data_format: str, df: pandas.DataFrame, hyperparams: str):
    url = "localhost:5000/predict"
    payload = {
        "format": data_format,
        "content": df.to_json(orient="records"),
        "hyperparams": hyperparams
    }
    response = requests.post(url, json=payload)
    try:
        return response.json()
    except ValueError:
        return response.text