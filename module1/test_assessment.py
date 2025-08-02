#!/usr/bin/env python3
"""
Test script for adaptive assessment functionality
"""

import requests
import json

def test_assessment_routes():
    """Test the adaptive assessment routes"""
    base_url = "http://127.0.0.1:5000"
    
    print("Testing Adaptive Assessment Routes...")
    print("=" * 50)
    
    # Test 1: Check if dashboard route exists
    try:
        response = requests.get(f"{base_url}/adaptive/dashboard", allow_redirects=False)
        print(f"Dashboard route status: {response.status_code}")
        if response.status_code == 302:
            print("✓ Dashboard route exists (redirects to login as expected)")
        else:
            print(f"Dashboard response: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to server. Make sure the app is running.")
        return
    except Exception as e:
        print(f"✗ Error testing dashboard: {e}")
    
    # Test 2: Check if take assessment route exists
    try:
        response = requests.get(f"{base_url}/adaptive/take-assessment", allow_redirects=False)
        print(f"Take assessment route status: {response.status_code}")
        if response.status_code == 302:
            print("✓ Take assessment route exists (redirects to login as expected)")
        else:
            print(f"Take assessment response: {response.status_code}")
    except Exception as e:
        print(f"✗ Error testing take assessment: {e}")
    
    # Test 3: Check if API routes exist
    try:
        response = requests.get(f"{base_url}/adaptive/questions", allow_redirects=False)
        print(f"Questions API route status: {response.status_code}")
        if response.status_code == 302:
            print("✓ Questions API route exists (redirects to login as expected)")
        else:
            print(f"Questions API response: {response.status_code}")
    except Exception as e:
        print(f"✗ Error testing questions API: {e}")
    
    # Test 4: Check if analytics route exists
    try:
        response = requests.get(f"{base_url}/adaptive/analytics", allow_redirects=False)
        print(f"Analytics route status: {response.status_code}")
        if response.status_code == 302:
            print("✓ Analytics route exists (redirects to login as expected)")
        else:
            print(f"Analytics response: {response.status_code}")
    except Exception as e:
        print(f"✗ Error testing analytics: {e}")
    
    print("\n" + "=" * 50)
    print("Assessment routes test completed!")
    print("\nTo test the full functionality:")
    print("1. Start the app: python app.py")
    print("2. Open http://127.0.0.1:5000 in your browser")
    print("3. Login with admin credentials: admin@example.com / Admin123!")
    print("4. Navigate to the adaptive assessment dashboard")

if __name__ == "__main__":
    test_assessment_routes() 