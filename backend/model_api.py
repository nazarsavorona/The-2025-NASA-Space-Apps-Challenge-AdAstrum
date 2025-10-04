"""
Model API for making predictions using the trained exoplanet classification models.
"""
import pandas as pd
from fastapi import HTTPException, status

from model_service import get_model_service


async def call_model(data_format: str, df: pd.DataFrame, hyperparams: dict) -> dict:
    """
    Call the model service to make predictions.
    
    Args:
        data_format: Format of the input data ("kepler", "k2", or "toi")
        df: Input dataframe with raw mission data
        hyperparams: Dictionary with prediction thresholds:
            - candidate_threshold: float
            - confirmed_threshold: float
            
    Returns:
        Dictionary with prediction results
    """
    try:
        # Get the model service
        model_service = get_model_service()
        
        # Normalize format name
        format_name = data_format.lower()
        if "kepler" in format_name:
            format_name = "kepler"
        elif "k2" in format_name or "tess" in format_name:
            format_name = "k2"
        
        # Make predictions
        result_df = model_service.predict(df, format_name, hyperparams)
        
        # Convert result to JSON-serializable format
        return {
            "status": "success",
            "predictions": result_df.to_dict(orient="records"),
            "summary": {
                "total": len(result_df),
                "confirmed": int((result_df["predicted_class"] == 2).sum()),
                "candidate": int((result_df["predicted_class"] == 1).sum()),
                "false_positive": int((result_df["predicted_class"] == 0).sum()),
            }
        }
        
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model not available: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )