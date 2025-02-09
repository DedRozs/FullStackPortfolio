import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Ensure models directory exists
models_dir = os.path.join(os.getcwd(), "models")
os.makedirs(models_dir, exist_ok=True)

# Generate Fake Data if No Dataset Exists
data_path = "datasets/random_forest_data.csv"
if not os.path.exists(data_path):
    print("⚠️ Dataset not found, generating random data...")
    df = pd.DataFrame(np.random.rand(500, 5), columns=["f1", "f2", "f3", "f4", "target"])
    df.to_csv(data_path, index=False)

# Load Dataset
df = pd.read_csv(data_path)
X = df.iloc[:, :-1].values  # Features
y = df.iloc[:, -1].values   # Target

# Split Data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train Model
print("🚀 Training Random Forest model...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Save Model
model_path = os.path.join(models_dir, "random_forest.pkl")
joblib.dump(model, model_path)

print(f"✅ Model saved at {model_path}")
