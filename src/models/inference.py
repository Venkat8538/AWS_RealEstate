import xgboost as xgb
import json
import os

def model_fn(model_dir):
    """Load the XGBoost model from the model directory."""
    model_file = os.path.join(model_dir, "xgboost-model")
    booster = xgb.Booster()
    booster.load_model(model_file)
    return booster

def input_fn(request_body, content_type='text/csv'):
    """Parse input data."""
    if content_type == 'text/csv':
        import io
        import pandas as pd
        df = pd.read_csv(io.StringIO(request_body), header=None)
        return xgb.DMatrix(df.values)
    else:
        raise ValueError(f"Unsupported content type: {content_type}")

def predict_fn(input_data, model):
    """Make predictions."""
    return model.predict(input_data)

def output_fn(prediction, accept='text/csv'):
    """Format the prediction output."""
    if accept == 'text/csv':
        return ','.join(str(x) for x in prediction)
    elif accept == 'application/json':
        return json.dumps(prediction.tolist())
    else:
        raise ValueError(f"Unsupported accept type: {accept}")
