import joblib
import os
from django.conf import settings
from transformers import pipeline

MODEL_PATH = os.path.join(settings.BASE_DIR, "models", "finbert_pipeline.pkl")

def load_finbert_model():
    if not os.path.exists(MODEL_PATH):
        # Auto-download FinBERT if missing
        finbert_pipeline = pipeline("sentiment-analysis", model="ProsusAI/finbert")
        joblib.dump(finbert_pipeline, MODEL_PATH)
        return finbert_pipeline
    return joblib.load(MODEL_PATH)
