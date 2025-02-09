import os
import torch
from django.conf import settings
import torch.nn as nn
import torch.optim as optim
import numpy as np

MODEL_PATH = os.path.join(settings.BASE_DIR, "models", "lstm_model.pth")


def generate_new_model():
    # Generate Dummy Data for Training
    X_train = np.random.rand(100, 10, 1)  # 100 samples, 10 time-steps each
    y_train = np.random.rand(100, 1)

    # Convert to tensors
    X_train_tensor = torch.tensor(X_train, dtype=torch.float32)
    y_train_tensor = torch.tensor(y_train, dtype=torch.float32)

    # Initialize model, loss, and optimizer
    model = LSTMModel()
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # Train the model
    epochs = 100
    for epoch in range(epochs):
        optimizer.zero_grad()
        output = model(X_train_tensor)
        loss = criterion(output, y_train_tensor)
        loss.backward()
        optimizer.step()

    # Ensure models directory exists
    models_dir = os.path.join(os.getcwd(), "models")
    os.makedirs(models_dir, exist_ok=True)

    # Save the model
    model_path = os.path.join(models_dir, "lstm_model.pth")
    torch.save(model.state_dict(), model_path)
    print(f"LSTM Model saved at {model_path}")


# Define LSTM Model
class LSTMModel(torch.nn.Module):
    def __init__(self, input_size=1, hidden_size=50, output_size=1, num_layers=2):
        super(LSTMModel, self).__init__()
        self.lstm = torch.nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = torch.nn.Linear(hidden_size, output_size)

    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        return self.fc(lstm_out[:, -1, :])

# Model Path (Always Load Latest Version)
def get_latest_model():
    model_dir = os.path.join(settings.BASE_DIR, "models")
    model_files = [f for f in os.listdir(model_dir) if f.startswith("lstm_model")]
    if not model_files:
        generate_new_model()
    
    latest_model = sorted(model_files)[-1]  # Get latest version
    return os.path.join(model_dir, latest_model)

def load_lstm_model():
    model_path = get_latest_model()
    model = LSTMModel()
    model.load_state_dict(torch.load(model_path, map_location=torch.device("cpu")))
    model.eval()
    return model
