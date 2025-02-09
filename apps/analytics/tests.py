import pytest
import requests

BASE_URL = "http://127.0.0.1:8000/analytics/"

@pytest.mark.parametrize("endpoint, payload", [
    ("lstm/", {"input_data": [0.1, 0.2, 0.3]}),
    ("finbert/", {"text": "The stock market is performing well."}),
    ("random_forest/", {"features": [1, 0, 3, 2]}),
    ("reinforcement/", {"state": [0.5, 1.2, 0.3]})
])
def test_api_endpoints(endpoint, payload):
    response = requests.post(BASE_URL + endpoint, json=payload)
    assert response.status_code == 200, f"Failed {endpoint}: {response.text}"
