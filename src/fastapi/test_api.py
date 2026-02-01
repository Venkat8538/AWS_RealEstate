#!/usr/bin/env python3
"""
Quick test script for FastAPI endpoints
Usage: python test_api.py
"""
import requests
import json

API_URL = "http://localhost:8000"

def test_health():
    print("Testing /health endpoint...")
    response = requests.get(f"{API_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")

def test_predict():
    print("Testing /predict endpoint...")
    payload = {
        "sqft": 2000,
        "bedrooms": 3,
        "bathrooms": 2.5,
        "location": "Urban",
        "year_built": 2010,
        "condition": "Good"
    }
    response = requests.post(f"{API_URL}/predict", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")

def test_batch():
    print("Testing /batch-predict endpoint...")
    payload = [
        {"sqft": 1500, "bedrooms": 2, "bathrooms": 1.5, "location": "Suburb", "year_built": 2000, "condition": "Fair"},
        {"sqft": 2500, "bedrooms": 4, "bathrooms": 3.0, "location": "Downtown", "year_built": 2015, "condition": "Excellent"}
    ]
    response = requests.post(f"{API_URL}/batch-predict", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")

if __name__ == "__main__":
    try:
        test_health()
        test_predict()
        test_batch()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to API. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")
