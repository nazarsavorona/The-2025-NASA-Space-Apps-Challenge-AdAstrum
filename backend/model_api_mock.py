from typing import Dict, Any

import numpy as np
import pandas
import json

async def call_model(data_format: str, df: pandas.DataFrame, hyperparams: str):
    predicted_confidence = np.random.rand(len(df))
    predicted_class = [
        0 if c < 0.2 else (1 if c < 0.8 else 2)
        for c in predicted_confidence
    ]

    df_with_predictions = df.copy()
    df_with_predictions["predicted_confidence"] = predicted_confidence
    df_with_predictions["predicted_class"] = predicted_class

    response = {
        "format": data_format,
        "content": json.loads(df_with_predictions.to_json(orient="records"))
    }

    return response