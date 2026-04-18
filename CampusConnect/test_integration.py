#!/usr/bin/env python3
"""
Campus Connect Integration Test Script
Tests the end-to-end functionality of the microservices
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
WEBSOCKET_URL = "ws://localhost:8080"

class CampusConnectTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_id = None

    def log(self, message: str, status: str = "INFO"):
        """Log messages with status"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {status}: {message}")

    def test_health_checks(self) -> bool:
        """Test health checks for all services"""
        self.log("Testing health checks...")

        services = [
            ("API Gateway", f"{API_BASE_URL}/health"),
            ("Auth Service", f"{API_BASE_URL}/auth/health"),
            ("Meetups Service", f"{API_BASE_URL}/meetups/health"),
            ("Marketplace Service", f"{API_BASE_URL}/marketplace/health"),
            ("Stolen & Found Service", f"{API_BASE_URL}/stolen-found/health"),
            ("Rooms Service", f"{API_BASE_URL}/rooms/health"),
            ("Rental Service", f"{API_BASE_URL}/rental/health"),
            ("Clubs Service", f"{API_BASE_URL}/clubs/health"),
            ("Jobs Service", f"{API_BASE_URL}/jobs/health"),
            ("Notes Service", f"{API_BASE_URL}/notes/health"),
            ("Food Service", f"{API_BASE_URL}/food/health"),
        ]

        all_healthy = True
        for service_name, url in services:
            try:
                response = self.session.get(url, timeout=5)
                if response.status_code == 200:
                    self.log(f"✓ {service_name} is healthy", "SUCCESS")
                else:
                    self.log(f"✗ {service_name} returned status {response.status_code}", "ERROR")
                    all_healthy = False
            except requests.exceptions.RequestException as e:
                self.log(f"✗ {service_name} is unreachable: {e}", "ERROR")
                all_healthy = False

        return all_healthy

    def test_user_registration(self) -> bool:
        """Test user registration"""
        self.log("Testing user registration...")

        user_data = {
            "email": f"test_{int(time.time())}@campus.com",
            "password": "testpassword123",
            "full_name": "Test User",
            "phone": "+1234567890"
        }

        try:
            response = self.session.post(
                f"{API_BASE_URL}/auth/register",
                json=user_data,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user", {}).get("id")

                if self.token:
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.token}"
                    })
                    self.log("✓ User registration successful", "SUCCESS")
                    return True
                else:
                    self.log("✗ Registration response missing token", "ERROR")
                    return False
            else:
                self.log(f"✗ Registration failed: {response.status_code} - {response.text}", "ERROR")
                return False

        except requests.exceptions.RequestException as e:
            self.log(f"✗ Registration request failed: {e}", "ERROR")
            return False

    def test_user_login(self) -> bool:
        """Test user login"""
        self.log("Testing user login...")

        login_data = {
            "email": "test@example.com",  # Use a test user that should exist
            "password": "password123"
        }

        try:
            response = self.session.post(
                f"{API_BASE_URL}/auth/login",
                json=login_data,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")

                if token:
                    self.token = token
                    self.session.headers.update({
                        "Authorization": f"Bearer {token}"
                    })
                    self.log("✓ User login successful", "SUCCESS")
                    return True
                else:
                    self.log("✗ Login response missing token", "ERROR")
                    return False
            else:
                self.log(f"✗ Login failed: {response.status_code} - {response.text}", "ERROR")
                return False

        except requests.exceptions.RequestException as e:
            self.log(f"✗ Login request failed: {e}", "ERROR")
            return False

    def test_meetups_service(self) -> bool:
        """Test meetups service functionality"""
        self.log("Testing meetups service...")

        try:
            # Test getting meetups
            response = self.session.get(f"{API_BASE_URL}/meetups", timeout=10)
            if response.status_code == 200:
                self.log("✓ Meetups listing works", "SUCCESS")
                return True
            else:
                self.log(f"✗ Meetups listing failed: {response.status_code}", "ERROR")
                return False

        except requests.exceptions.RequestException as e:
            self.log(f"✗ Meetups service test failed: {e}", "ERROR")
            return False

    def test_marketplace_service(self) -> bool:
        """Test marketplace service functionality"""
        self.log("Testing marketplace service...")

        try:
            # Test getting marketplace items
            response = self.session.get(f"{API_BASE_URL}/marketplace", timeout=10)
            if response.status_code == 200:
                self.log("✓ Marketplace listing works", "SUCCESS")
                return True
            else:
                self.log(f"✗ Marketplace listing failed: {response.status_code}", "ERROR")
                return False

        except requests.exceptions.RequestException as e:
            self.log(f"✗ Marketplace service test failed: {e}", "ERROR")
            return False

    def test_stolen_found_service(self) -> bool:
        """Test stolen & found service functionality"""
        self.log("Testing stolen & found service...")

        try:
            # Test getting reports
            response = self.session.get(f"{API_BASE_URL}/stolen-found", timeout=10)
            if response.status_code == 200:
                self.log("✓ Stolen & found listing works", "SUCCESS")
                return True
            else:
                self.log(f"✗ Stolen & found listing failed: {response.status_code}", "ERROR")
                return False

        except requests.exceptions.RequestException as e:
            self.log(f"✗ Stolen & found service test failed: {e}", "ERROR")
            return False

    def test_rooms_service(self) -> bool:
        """Test rooms service functionality"""
        self.log("Testing rooms service...")

        try:
            # Test getting rooms
            response = self.session.get(f"{API_BASE_URL}/rooms", timeout=10)
            if response.status_code == 200:
                self.log("✓ Rooms listing works", "SUCCESS")
                return True
            else:
                self.log(f"✗ Rooms listing failed: {response.status_code}", "ERROR")
                return False

        except requests.exceptions.RequestException as e:
            self.log(f"✗ Rooms service test failed: {e}", "ERROR")
            return False

    def test_jobs_service(self) -> bool:
        """Test jobs service functionality"""
        self.log("Testing jobs service...")

        try:
            # Test getting jobs
            response = self.session.get(f"{API_BASE_URL}/jobs", timeout=10)
            if response.status_code == 200:
                self.log("✓ Jobs listing works", "SUCCESS")
                return True
            else:
                self.log(f"✗ Jobs listing failed: {response.status_code}", "ERROR")
                return False

        except requests.exceptions.RequestException as e:
            self.log(f"✗ Jobs service test failed: {e}", "ERROR")
            return False

    def test_food_service(self) -> bool:
        """Test food service functionality"""
        self.log("Testing food service...")

        try:
            # Test getting food outlets
            response = self.session.get(f"{API_BASE_URL}/food/outlets", timeout=10)
            if response.status_code == 200:
                self.log("✓ Food outlets listing works", "SUCCESS")
                return True
            else:
                self.log(f"✗ Food outlets listing failed: {response.status_code}", "ERROR")
                return False

        except requests.exceptions.RequestException as e:
            self.log(f"✗ Food service test failed: {e}", "ERROR")
            return False

    def run_all_tests(self) -> bool:
        """Run all integration tests"""
        self.log("🚀 Starting Campus Connect Integration Tests", "START")

        tests = [
            ("Health Checks", self.test_health_checks),
            ("User Login", self.test_user_login),
            ("Meetups Service", self.test_meetups_service),
            ("Marketplace Service", self.test_marketplace_service),
            ("Stolen & Found Service", self.test_stolen_found_service),
            ("Rooms Service", self.test_rooms_service),
            ("Jobs Service", self.test_jobs_service),
            ("Food Service", self.test_food_service),
        ]

        results = []
        for test_name, test_func in tests:
            self.log(f"Running {test_name}...")
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                self.log(f"✗ {test_name} crashed: {e}", "ERROR")
                results.append((test_name, False))

        # Summary
        self.log("\n" + "="*50, "SUMMARY")
        self.log("TEST RESULTS:", "SUMMARY")

        passed = 0
        total = len(results)

        for test_name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            color = "SUCCESS" if result else "ERROR"
            self.log(f"{test_name}: {status}", color)
            if result:
                passed += 1

        self.log(f"\nPassed: {passed}/{total} tests", "SUMMARY")

        if passed == total:
            self.log("🎉 All tests passed! Campus Connect is working correctly.", "SUCCESS")
            return True
        else:
            self.log(f"⚠️  {total - passed} tests failed. Please check the services.", "WARNING")
            return False

def main():
    """Main test runner"""
    print("Campus Connect Integration Test Suite")
    print("=" * 50)

    tester = CampusConnectTester()

    # Wait a bit for services to be ready
    print("Waiting for services to be ready...")
    time.sleep(5)

    success = tester.run_all_tests()

    if success:
        print("\n✅ Integration tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()