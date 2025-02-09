from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import torch
import numpy as np
from .ai_models.lstm import load_lstm_model
from .ai_models.finbert import load_finbert_model
from .ai_models.random_forest import load_random_forest
from .ai_models.reinforcement_learning import load_reinforcement_model


# Load models at runtime
lstm_model = load_lstm_model()
finbert_pipeline = load_finbert_model()
random_forest_model = load_random_forest()
reinforcement_model = load_reinforcement_model()

class PredictLSTM(APIView):
    """Handles LSTM model predictions."""
    def post(self, request):
        data = request.data.get("input_data")
        if not data:
            return Response({"error": "No input data provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Convert input to a 3D tensor (batch_size=1, sequence_length, features=1)
            tensor_data = torch.tensor(np.array(data, dtype=np.float32)).unsqueeze(0).unsqueeze(-1)
            
            output = lstm_model(tensor_data)  # Forward pass
            return Response({"prediction": output.tolist()}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PredictFinBERT(APIView):
    """Handles FinBERT sentiment analysis predictions."""
    def post(self, request):
        text = request.data.get("text")
        if not text:
            return Response({"error": "No text provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = finbert_pipeline(text)
            return Response({"prediction": result}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PredictRandomForest(APIView):
    """Handles predictions using a Random Forest model."""
    def post(self, request):
        features = request.data.get("features")
        if not features:
            return Response({"error": "No features provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            prediction = random_forest_model.predict([features])
            return Response({"prediction": prediction.tolist()}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from .ai_models.reinforcement_learning import load_reinforcement_model, discretize_state  # Import function
import numpy as np

# Load Reinforcement Learning model
reinforcement_model = load_reinforcement_model()

# Define bins for discretization (must match training)
state_bins = [np.linspace(-1, 1, 10) for _ in range(len(reinforcement_model.shape) - 1)]  # Use same binning as training

class PredictReinforcementLearning(APIView):
    """Handles predictions using a Reinforcement Learning model."""
    def post(self, request):
        state = request.data.get("state")
        if not state:
            return Response({"error": "No state provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Convert state to discrete index
            state = np.array(state, dtype=np.float32)
            state = discretize_state(state, state_bins)  # Ensure state is in valid range
            
            # Choose action using Q-table
            action = np.argmax(reinforcement_model[state])  # Select best action

            return Response({"action": int(action)}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
