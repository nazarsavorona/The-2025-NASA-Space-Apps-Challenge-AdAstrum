"""
Example of using the model_service.predict() method directly.

This demonstrates how to use the predict function without going through the API.
"""

import pandas as pd
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.model_service import get_model_service


def example_kepler_prediction():
    """Example using Kepler format data."""
    print("\n=== Kepler Format Example ===")
    
    # Create sample data
    df = pd.DataFrame([
        {
            "koi_period": 3.52,
            "koi_duration": 2.8,
            "koi_depth": 1200.0,
            "koi_impact": 0.5,
            "koi_eccen": 0.1,
            "koi_incl": 89.5,
            "koi_prad": 1.5,
            "koi_teq": 350.0,
            "koi_insol": 1.2,
            "koi_steff": 5700.0,
            "koi_slogg": 4.5,
            "koi_srad": 1.0,
            "koi_smass": 1.0,
            "koi_smet": 0.0,
        },
        {
            "koi_period": 10.5,
            "koi_duration": 3.2,
            "koi_depth": 800.0,
            "koi_impact": 0.3,
            "koi_eccen": 0.05,
            "koi_incl": 88.0,
            "koi_prad": 2.1,
            "koi_teq": 280.0,
            "koi_insol": 0.8,
            "koi_steff": 6100.0,
            "koi_slogg": 4.3,
            "koi_srad": 1.2,
            "koi_smass": 1.1,
            "koi_smet": 0.1,
        }
    ])
    
    # Set hyperparameters
    hyperparams = {
        "candidate_threshold": 0.4,
        "confirmed_threshold": 0.7
    }
    
    # Get model service and make predictions
    model_service = get_model_service()
    result_df = model_service.predict(df, "kepler", hyperparams)
    
    # Display results
    print(f"\nInput rows: {len(df)}")
    print(f"\nPredictions:")
    for idx, row in result_df.iterrows():
        print(f"\n  Row {idx + 1}:")
        print(f"    Orbital Period: {row['koi_period']:.2f} days")
        print(f"    Planet Radius: {row['koi_prad']:.2f} Earth radii")
        print(f"    Predicted Class: {row['predicted_class']} ", end="")
        if row['predicted_class'] == 0:
            print("(False Positive)")
        elif row['predicted_class'] == 1:
            print("(Candidate)")
        else:
            print("(Confirmed)")
        print(f"    Confidence: {row['predicted_confidence']:.3f}")


def example_k2_prediction():
    """Example using K2 format data."""
    print("\n=== K2 Format Example ===")
    
    # Create sample data
    df = pd.DataFrame([
        {
            "pl_orbper": 4.5,
            "pl_trandur": 2.5,
            "pl_trandep": 1000.0,
            "pl_imppar": 0.4,
            "pl_orbeccen": 0.08,
            "pl_orbincl": 89.0,
            "pl_rade": 1.6,
            "pl_eqt": 320.0,
            "pl_insol": 1.0,
            "st_teff": 5800.0,
            "st_logg": 4.45,
            "st_rad": 1.0,
            "st_mass": 1.0,
            "st_met": 0.05,
        }
    ])
    
    # Set hyperparameters
    hyperparams = {
        "candidate_threshold": 0.3,
        "confirmed_threshold": 0.6
    }
    
    # Get model service and make predictions
    model_service = get_model_service()
    result_df = model_service.predict(df, "k2", hyperparams)
    
    # Display results
    print(f"\nInput rows: {len(df)}")
    print(f"\nPrediction:")
    row = result_df.iloc[0]
    print(f"  Orbital Period: {row['pl_orbper']:.2f} days")
    print(f"  Planet Radius: {row['pl_rade']:.2f} Earth radii")
    print(f"  Predicted Class: {row['predicted_class']} ", end="")
    if row['predicted_class'] == 0:
        print("(False Positive)")
    elif row['predicted_class'] == 1:
        print("(Candidate)")
    else:
        print("(Confirmed)")
    print(f"  Confidence: {row['predicted_confidence']:.3f}")


def example_with_missing_values():
    """Example with missing values (NaN)."""
    print("\n=== Example with Missing Values ===")
    
    # Create sample data with missing values
    df = pd.DataFrame([
        {
            "koi_period": 3.52,
            "koi_prad": 1.5,
            "koi_steff": 5700.0,
            "koi_slogg": 4.5,
            # Other values will be NaN
        }
    ])
    
    # Set hyperparameters
    hyperparams = {
        "candidate_threshold": 0.4,
        "confirmed_threshold": 0.7
    }
    
    print("\nNote: Missing values are automatically handled by the imputer")
    print("Input data has only 4 features filled, rest are NaN")
    
    # Get model service and make predictions
    model_service = get_model_service()
    result_df = model_service.predict(df, "kepler", hyperparams)
    
    # Display results
    print(f"\nPrediction:")
    row = result_df.iloc[0]
    print(f"  Predicted Class: {row['predicted_class']}")
    print(f"  Confidence: {row['predicted_confidence']:.3f}")


def example_batch_prediction():
    """Example with batch prediction from CSV file."""
    print("\n=== Batch Prediction from CSV ===")
    
    # Check if test data exists
    csv_file = "data/kepler.csv"
    if not os.path.exists(csv_file):
        print(f"File {csv_file} not found. Skipping this example.")
        return
    
    # Read CSV (first 5 rows)
    df = pd.read_csv(csv_file, nrows=5, comment='#')
    
    # Set hyperparameters
    hyperparams = {
        "candidate_threshold": 0.4,
        "confirmed_threshold": 0.7
    }
    
    # Get model service and make predictions
    model_service = get_model_service()
    result_df = model_service.predict(df, "kepler", hyperparams)
    
    # Display summary
    print(f"\nProcessed {len(result_df)} rows from CSV")
    print("\nSummary:")
    print(f"  Confirmed (class=2): {(result_df['predicted_class'] == 2).sum()}")
    print(f"  Candidate (class=1): {(result_df['predicted_class'] == 1).sum()}")
    print(f"  False Positive (class=0): {(result_df['predicted_class'] == 0).sum()}")
    
    # Show high-confidence predictions
    high_conf = result_df[result_df['predicted_confidence'] >= 0.8]
    if len(high_conf) > 0:
        print(f"\nHigh confidence predictions (>= 0.8): {len(high_conf)}")


def main():
    """Run all examples."""
    print("=" * 60)
    print("Model Service predict() Method Examples")
    print("=" * 60)
    
    try:
        # Run examples
        example_kepler_prediction()
        example_k2_prediction()
        example_with_missing_values()
        example_batch_prediction()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have trained the models first:")
        print("  python v1.py")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
