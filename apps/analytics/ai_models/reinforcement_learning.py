import os
import joblib
import numpy as np
import gym
from django.conf import settings

# Define Model Path
MODEL_DIR = os.path.join(settings.BASE_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "reinforcement_learning.pkl")

def discretize_state(state, bins):
    """
    Converts a continuous state into a discrete index for the Q-table.
    - Uses np.digitize to assign state values into bins.
    - Subtracts 1 so the indices start from 0 instead of 1.
    - Clamps indices to be within the valid range of Q-table indices.
    """
    discretized = [min(len(bins[i]) - 1, max(0, np.digitize(state[i], bins[i]) - 1)) for i in range(len(state))]
    return tuple(discretized)  # Convert to tuple for indexing

def create_reinforcement_learning_model():
    """
    Creates and trains a simple Q-learning Reinforcement Learning model.
    """
    # Ensure models directory exists
    os.makedirs(MODEL_DIR, exist_ok=True)

    # Initialize OpenAI Gym Environment
    env = gym.make("CartPole-v1")

    # Q-learning Parameters
    state_size = env.observation_space.shape[0]
    action_size = env.action_space.n

    # Create binning for each state feature (10 bins per feature)
    state_bins = [np.linspace(-1, 1, 10) for _ in range(state_size)]
    
    # Create Q-table with discretized states
    q_table = np.zeros((10,) * state_size + (action_size,), dtype=np.float32)

    # Hyperparameters
    alpha = 0.1  # Learning rate
    gamma = 0.95  # Discount factor
    epsilon = 1.0  # Exploration rate
    epsilon_decay = 0.99
    min_epsilon = 0.01
    episodes = 1000

    # Training Loop
    for episode in range(episodes):
        state, _ = env.reset()
        state = discretize_state(state, state_bins)  # Convert state to discrete index
        done = False

        while not done:
            action = np.argmax(q_table[state]) if np.random.rand() > epsilon else env.action_space.sample()
            next_state, reward, done, _, _ = env.step(action)
            next_state = discretize_state(next_state, state_bins)  # Convert to discrete index

            # Q-learning update rule (ensuring indices remain valid)
            q_table[state][action] = (1 - alpha) * q_table[state][action] + alpha * (
                reward + gamma * np.max(q_table[next_state])
            )

            state = next_state

        # Reduce exploration rate
        epsilon = max(min_epsilon, epsilon * epsilon_decay)

        if episode % 100 == 0:
            print(f"Episode {episode}/{episodes} - Epsilon: {epsilon:.2f}")

    # Save Model
    joblib.dump(q_table, MODEL_PATH)
    print(f"✅ Reinforcement Learning Model saved at {MODEL_PATH}")

def load_reinforcement_model():
    """
    Loads the trained Reinforcement Learning model.
    """
    if not os.path.exists(MODEL_PATH):
        create_reinforcement_learning_model()

    print(f"✅ Loading Reinforcement Learning model from {MODEL_PATH}")
    return joblib.load(MODEL_PATH)
