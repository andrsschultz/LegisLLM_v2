#!/usr/bin/env python3
"""
Test script for Gesetzesentwurf generation workflow
"""
import requests
import json
import os

# Configuration
BACKEND_URL = "http://localhost:8000"
API_KEY = "test-key"  # You'll need to use a real API key
MODEL = "gpt-3.5-turbo"

def test_aenderungsbefehle_generation():
    """Test Änderungsbefehle generation endpoint"""
    print("\n=== Testing Änderungsbefehle Generation ===")
    
    # Sample final amendment data
    test_data = {
        "task_description": "Einführung einer Freigrenze für Einnahmen aus Vermietung und Verpachtung von 520 Euro jährlich",
        "final_amendments": [
            {
                "originalNorm": {
                    "jurabk": "EStG",
                    "enbez": "§ 21",
                    "P": "1",
                    "wording": "Zu den Einkünften aus Vermietung und Verpachtung gehören..."
                },
                "amendedNorm": {
                    "jurabk": "EStG",
                    "enbez": "§ 21",
                    "P": "1",
                    "wording": "Zu den Einkünften aus Vermietung und Verpachtung gehören... Eine Freigrenze von 520 Euro jährlich wird gewährt.",
                    "amendmentDescription": "Ergänzung um Freigrenze von 520 Euro jährlich"
                }
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/generate_aenderungsbefehle",
            params={"model": MODEL},
            headers={"Content-Type": "application/json", "X-API-Key": API_KEY},
            json=test_data
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Änderungsbefehle generated successfully!")
            print(f"Response length: {len(result.get('response', ''))} characters")
            return result.get('response', '')
        else:
            print(f"❌ Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return None

def test_gesetzesentwurf_generation(aenderungsbefehle):
    """Test Gesetzesentwurf generation endpoint"""
    print("\n=== Testing Gesetzesentwurf Generation ===")
    
    if not aenderungsbefehle:
        print("❌ No Änderungsbefehle provided, skipping test")
        return
    
    # Sample data for Gesetzesentwurf generation
    test_data = {
        "task_description": "Einführung einer Freigrenze für Einnahmen aus Vermietung und Verpachtung von 520 Euro jährlich",
        "aenderungsbefehle": aenderungsbefehle,
        "final_amendments": [
            {
                "originalNorm": {
                    "jurabk": "EStG",
                    "enbez": "§ 21",
                    "P": "1",
                    "wording": "Zu den Einkünften aus Vermietung und Verpachtung gehören..."
                },
                "amendedNorm": {
                    "jurabk": "EStG",
                    "enbez": "§ 21",
                    "P": "1",
                    "wording": "Zu den Einkünften aus Vermietung und Verpachtung gehören... Eine Freigrenze von 520 Euro jährlich wird gewährt.",
                    "amendmentDescription": "Ergänzung um Freigrenze von 520 Euro jährlich"
                }
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/generate_entwurf",
            params={"model": MODEL},
            headers={"Content-Type": "application/json", "X-API-Key": API_KEY},
            json=test_data
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Gesetzesentwurf generated successfully!")
            print(f"Response length: {len(result.get('response', ''))} characters")
            print("\n--- Generated Gesetzesentwurf Preview ---")
            preview = result.get('response', '')[:500] + "..." if len(result.get('response', '')) > 500 else result.get('response', '')
            print(preview)
            return result.get('response', '')
        else:
            print(f"❌ Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return None

def main():
    print("🧪 Testing Gesetzesentwurf Generation Workflow")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Model: {MODEL}")
    
    # Test health endpoint first
    try:
        health_response = requests.get(f"{BACKEND_URL}/health")
        if health_response.status_code == 200:
            print("✅ Backend is healthy")
        else:
            print("❌ Backend health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to backend: {str(e)}")
        return
    
    # Step 1: Generate Änderungsbefehle
    aenderungsbefehle = test_aenderungsbefehle_generation()
    
    # Step 2: Generate Gesetzesentwurf (only if step 1 succeeded)
    if aenderungsbefehle:
        test_gesetzesentwurf_generation(aenderungsbefehle)
    
    print("\n🏁 Test workflow completed!")

if __name__ == "__main__":
    main()