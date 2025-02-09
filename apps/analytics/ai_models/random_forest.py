import os
import joblib
from django.conf import settings
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor  # Use Regressor
from sklearn.model_selection import train_test_split

# Define Model Path
MODEL_DIR = os.path.join(settings.BASE_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "random_forest.pkl")

def create_random_forest_model():
    """
    Creates and trains a Random Forest Regressor model.
    """
    # Ensure models directory exists
    models_dir = os.path.join(os.getcwd(), "models")
    os.makedirs(models_dir, exist_ok=True)

    # Generate Fake Data if No Dataset Exists
    data_path = f"{settings.BASE_DIR}/apps/analytics/ai_models/datasets/random_forest_data.csv"
    if not os.path.exists(data_path):
        print("⚠️ Dataset not found, generating random regression data...")
        df = pd.DataFrame(np.random.rand(500, 5), columns=["f1", "f2", "f3", "f4", "target"])
        df.to_csv(data_path, index=False)

    # Load Dataset
    df = pd.read_csv(data_path)
    X = df.iloc[:, :-1].values  # Features
    y = df.iloc[:, -1].values   # Target (continuous values)

    # Split Data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train Model (Using RandomForestRegressor)
    print("🚀 Training Random Forest Regression model...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Save Model
    model_path = os.path.join(models_dir, "random_forest.pkl")
    joblib.dump(model, model_path)

    print(f"✅ Model saved at {model_path}")


def load_random_forest():
    """
    Loads the trained Random Forest Regressor model.
    """
    if not os.path.exists(MODEL_PATH):
        create_random_forest_model()

    print(f"✅ Loading Random Forest model from {MODEL_PATH}")
    return joblib.load(MODEL_PATH)
