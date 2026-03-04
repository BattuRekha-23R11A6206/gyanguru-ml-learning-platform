#!/usr/bin/env python3
"""Test script for enhanced quiz functionality"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def register_user():
    """Register a test user"""
    data = {
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "testpass123"
    }

    response = requests.post(f"{BASE_URL}/api/register", json=data)
    print(f"Registration status: {response.status_code}")
    if response.status_code == 201:
        print("✅ User registered successfully")
        return True
    else:
        print(f"❌ Registration failed: {response.text}")
        return False

def login_user():
    """Login and get JWT token"""
    data = {
        "username": "testuser2",
        "password": "testpass123"
    }

    response = requests.post(f"{BASE_URL}/api/login", json=data)
    print(f"Login status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            token = result.get('token')
            print("✅ Login successful, got token")
            return token
        else:
            print(f"❌ Login failed: {result.get('error')}")
            return None
    else:
        print(f"❌ Login request failed: {response.text}")
        return None

def test_quiz_generation(token):
    """Test real-time quiz generation"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "topic": "machine learning",
        "difficulty": "intermediate",
        "num_questions": 3
    }

    print("\n🧠 Testing real-time quiz generation...")
    response = requests.post(f"{BASE_URL}/api/quiz/generate", json=data, headers=headers)
    print(f"Quiz generation status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"Response: {result}")  # Debug output
        if result.get('success'):
            print("✅ Quiz generated successfully")
            quiz = result.get('quiz', {})
            if quiz:
                print(f"📚 Topic: {quiz.get('topic')}")
                print(f"❓ Questions: {len(quiz.get('questions', []))}")
                return True
            else:
                print("❌ Quiz object is empty")
                return False
        else:
            print(f"❌ Quiz generation failed: {result.get('error')}")
            return False
    else:
        print(f"❌ Quiz generation request failed: {response.text}")
        return False

def test_adaptive_quiz(token):
    """Test adaptive quiz generation"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {"topic": "neural networks"}

    print("\n🎯 Testing adaptive quiz generation...")
    response = requests.post(f"{BASE_URL}/api/quiz/adaptive", json=data, headers=headers)
    print(f"Adaptive quiz status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("✅ Adaptive quiz generated successfully")
            return True
        else:
            print(f"❌ Adaptive quiz failed: {result.get('error')}")
            return False
    else:
        print(f"❌ Adaptive quiz request failed: {response.text}")
        return False

def test_quiz_analytics(token):
    """Test quiz performance analytics"""
    headers = {"Authorization": f"Bearer {token}"}

    print("\n📊 Testing quiz analytics...")
    response = requests.post(f"{BASE_URL}/api/quiz/analytics", headers=headers)
    print(f"Analytics status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("✅ Analytics retrieved successfully")
            return True
        else:
            print(f"❌ Analytics failed: {result.get('error')}")
            return False
    else:
        print(f"❌ Analytics request failed: {response.text}")
        return False

def main():
    print("🚀 Starting enhanced quiz functionality test...")

    # Test health endpoint first
    print("\n🏥 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/api/health")
    if response.status_code == 200:
        print("✅ Health check passed")
    else:
        print(f"❌ Health check failed: {response.status_code}")
        sys.exit(1)

    # Register and login
    if not register_user():
        sys.exit(1)

    token = login_user()
    if not token:
        sys.exit(1)

    # Test quiz functionality
    quiz_gen_success = test_quiz_generation(token)
    adaptive_success = test_adaptive_quiz(token)
    analytics_success = test_quiz_analytics(token)

    print("\n🎉 Test Summary:")
    print(f"Real-time Quiz Generation: {'✅ PASS' if quiz_gen_success else '❌ FAIL'}")
    print(f"Adaptive Quiz Generation: {'✅ PASS' if adaptive_success else '❌ FAIL'}")
    print(f"Quiz Analytics: {'✅ PASS' if analytics_success else '❌ FAIL'}")

    if quiz_gen_success and adaptive_success and analytics_success:
        print("\n🎊 All enhanced quiz features are working correctly!")
    else:
        print("\n⚠️  Some quiz features need attention.")

if __name__ == "__main__":
    main()
