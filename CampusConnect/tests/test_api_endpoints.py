#!/usr/bin/env python3
"""
Campus Connect API Testing Suite
Comprehensive tests for all microservice endpoints
"""

import pytest
import requests
import json
from datetime import datetime, timedelta
import time

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER = {
    "email": f"test_{int(time.time())}@campus.com",
    "password": "testpassword123",
    "full_name": "Test User API",
    "phone": "+1234567890"
}

class TestCampusConnectAPI:
    """Comprehensive API testing suite"""

    def setup_method(self):
        """Setup for each test method"""
        self.session = requests.Session()
        self.token = None
        self.user_id = None
        self.test_data = {}

    def teardown_method(self):
        """Cleanup after each test method"""
        if self.session:
            self.session.close()

    def authenticate_user(self):
        """Authenticate and get JWT token"""
        # First try to register
        register_response = self.session.post(
            f"{BASE_URL}/auth/register",
            json=TEST_USER,
            timeout=10
        )

        if register_response.status_code == 200:
            data = register_response.json()
            self.token = data.get("access_token")
            self.user_id = data.get("user", {}).get("id")
        else:
            # Try login if registration fails (user might already exist)
            login_response = self.session.post(
                f"{BASE_URL}/auth/login",
                json={
                    "email": "admin@campus.com",
                    "password": "admin123"
                },
                timeout=10
            )
            if login_response.status_code == 200:
                data = login_response.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user", {}).get("id")

        if self.token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}"
            })

        return self.token is not None

    def test_health_check(self):
        """Test API Gateway health check"""
        response = self.session.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_cors_headers(self):
        """Test CORS headers are properly set"""
        response = self.session.options(f"{BASE_URL}/auth/health", timeout=5)
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers

    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        # Make multiple requests quickly
        responses = []
        for i in range(110):  # Exceed rate limit
            response = self.session.get(f"{BASE_URL}/health", timeout=5)
            responses.append(response.status_code)
            time.sleep(0.01)  # Small delay to avoid overwhelming

        # Should have some 429 (Too Many Requests) responses
        rate_limited_responses = [r for r in responses if r == 429]
        assert len(rate_limited_responses) > 0, "Rate limiting should be active"

    def test_auth_service_health(self):
        """Test auth service health"""
        response = self.session.get(f"{BASE_URL}/auth/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "auth"

    def test_user_registration(self):
        """Test user registration"""
        user_data = {
            "email": f"pytest_{int(time.time())}@test.com",
            "password": "testpassword123",
            "full_name": "Pytest User",
            "phone": "+1234567890"
        }

        response = self.session.post(
            f"{BASE_URL}/auth/register",
            json=user_data,
            timeout=10
        )

        # Should succeed or fail with conflict (user exists)
        assert response.status_code in [200, 400]

        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert "user" in data
            assert data["user"]["email"] == user_data["email"]

    def test_user_login(self):
        """Test user login"""
        login_data = {
            "email": "admin@campus.com",
            "password": "admin123"
        }

        response = self.session.post(
            f"{BASE_URL}/auth/login",
            json=login_data,
            timeout=10
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] == "admin"

    def test_protected_route_without_auth(self):
        """Test accessing protected route without authentication"""
        # Clear any existing auth
        temp_session = requests.Session()

        response = temp_session.get(f"{BASE_URL}/auth/profile", timeout=5)
        assert response.status_code == 401

    def test_meetups_service(self):
        """Test meetups service functionality"""
        # Authenticate first
        assert self.authenticate_user(), "Authentication failed"

        # Test getting meetups
        response = self.session.get(f"{BASE_URL}/meetups", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Test creating a meetup
        meetup_data = {
            "title": "API Test Meetup",
            "description": "Testing meetup creation via API",
            "host_name": "API Tester",
            "social_handle": "@api_tester",
            "location": "Test Location",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "event_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "max_participants": 50
        }

        response = self.session.post(
            f"{BASE_URL}/meetups",
            json=meetup_data,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert data["title"] == meetup_data["title"]
            self.test_data["meetup_id"] = data["id"]

    def test_marketplace_service(self):
        """Test marketplace service functionality"""
        # Authenticate first
        assert self.authenticate_user(), "Authentication failed"

        # Test getting marketplace items
        response = self.session.get(f"{BASE_URL}/marketplace", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Test creating a marketplace item
        item_data = {
            "title": "API Test Laptop",
            "description": "Testing marketplace item creation",
            "price": 999.99,
            "category": "electronics",
            "condition_status": "new",
            "contact_info": "test@campus.com"
        }

        response = self.session.post(
            f"{BASE_URL}/marketplace",
            json=item_data,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert data["title"] == item_data["title"]
            self.test_data["item_id"] = data["id"]

    def test_stolen_found_service(self):
        """Test stolen & found service functionality"""
        # Authenticate first
        assert self.authenticate_user(), "Authentication failed"

        # Test getting reports
        response = self.session.get(f"{BASE_URL}/stolen-found", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Test creating a report
        report_data = {
            "item_name": "API Test Wallet",
            "description": "Testing lost item report creation",
            "category": "accessories",
            "report_type": "lost",
            "location": "Library",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "contact_info": "test@campus.com"
        }

        response = self.session.post(
            f"{BASE_URL}/stolen-found",
            json=report_data,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert data["item_name"] == report_data["item_name"]
            self.test_data["report_id"] = data["id"]

    def test_rooms_service(self):
        """Test rooms service functionality"""
        # Authenticate first
        assert self.authenticate_user(), "Authentication failed"

        # Test getting rooms
        response = self.session.get(f"{BASE_URL}/rooms", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Test creating a room listing
        room_data = {
            "title": "API Test Room",
            "description": "Testing room listing creation",
            "location": "Test Building",
            "rent_amount": 800.00,
            "deposit_amount": 1600.00,
            "room_type": "single",
            "gender_preference": "any",
            "amenities": ["wifi", "laundry"],
            "contact_info": "test@campus.com"
        }

        response = self.session.post(
            f"{BASE_URL}/rooms",
            json=room_data,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert data["title"] == room_data["title"]
            self.test_data["room_id"] = data["id"]

    def test_jobs_service(self):
        """Test jobs service functionality"""
        # Authenticate first
        assert self.authenticate_user(), "Authentication failed"

        # Test getting jobs
        response = self.session.get(f"{BASE_URL}/jobs", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Test creating a job posting
        job_data = {
            "title": "API Test Developer",
            "company_name": "Test Company",
            "description": "Testing job posting creation",
            "requirements": "JavaScript, React, Node.js",
            "job_type": "internship",
            "location": "Remote",
            "salary_range": "$20-30/hour"
        }

        response = self.session.post(
            f"{BASE_URL}/jobs",
            json=job_data,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert data["title"] == job_data["title"]
            self.test_data["job_id"] = data["id"]

    def test_food_service(self):
        """Test food service functionality"""
        # Authenticate first
        assert self.authenticate_user(), "Authentication failed"

        # Test getting food outlets
        response = self.session.get(f"{BASE_URL}/food/outlets", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_admin_endpoints(self):
        """Test admin-only endpoints"""
        # Login as admin
        admin_login = {
            "email": "admin@campus.com",
            "password": "admin123"
        }

        response = self.session.post(
            f"{BASE_URL}/auth/login",
            json=admin_login,
            timeout=10
        )

        assert response.status_code == 200
        data = response.json()
        admin_token = data.get("access_token")

        # Test admin endpoints with admin token
        admin_session = requests.Session()
        admin_session.headers.update({
            "Authorization": f"Bearer {admin_token}"
        })

        # Test getting all users (admin only)
        response = admin_session.get(f"{BASE_URL}/auth/users", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_error_handling(self):
        """Test error handling for invalid requests"""
        # Test invalid JSON
        response = self.session.post(
            f"{BASE_URL}/auth/login",
            data="invalid json",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        assert response.status_code in [400, 422]

        # Test non-existent endpoint
        response = self.session.get(f"{BASE_URL}/non-existent-endpoint", timeout=5)
        assert response.status_code == 404

    def test_response_format(self):
        """Test API response formats"""
        response = self.session.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200

        # Check content type
        assert "application/json" in response.headers.get("content-type", "")

        # Check JSON structure
        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data

    def test_request_validation(self):
        """Test request validation"""
        # Test missing required fields
        response = self.session.post(
            f"{BASE_URL}/auth/login",
            json={},
            timeout=10
        )
        assert response.status_code == 422  # Validation error

        # Test invalid email format
        response = self.session.post(
            f"{BASE_URL}/auth/login",
            json={"email": "invalid-email", "password": "password"},
            timeout=10
        )
        assert response.status_code == 422

if __name__ == "__main__":
    # Run basic health check if called directly
    session = requests.Session()
    try:
        response = session.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API Gateway is healthy")
        else:
            print(f"❌ API Gateway returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Could not connect to API Gateway: {e}")