#!/usr/bin/env python3
"""
Local deployment test script for Sales Engagement Platform
"""
import asyncio
import aiohttp
import json
import time
import sys
from typing import Dict, Any

class LocalTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.auth_token = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def wait_for_service(self, max_attempts: int = 30) -> bool:
        """Wait for the API service to be ready"""
        print("🔄 Waiting for API service to be ready...")
        
        for attempt in range(max_attempts):
            try:
                async with self.session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        print("✅ API service is ready!")
                        return True
            except Exception:
                pass
            
            print(f"⏳ Attempt {attempt + 1}/{max_attempts} - waiting...")
            await asyncio.sleep(2)
        
        print("❌ API service failed to start")
        return False
    
    async def test_health_endpoint(self) -> bool:
        """Test the health endpoint"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check passed: {data}")
                    return True
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    async def test_api_docs(self) -> bool:
        """Test API documentation endpoint"""
        try:
            async with self.session.get(f"{self.base_url}/docs") as response:
                if response.status == 200:
                    print("✅ API documentation is accessible")
                    return True
                else:
                    print(f"❌ API docs failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ API docs error: {e}")
            return False
    
    async def test_user_registration(self) -> bool:
        """Test user registration"""
        try:
            registration_data = {
                "email": "test@example.com",
                "password": "TestPass123!",
                "company_name": "Test Company"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/auth/register",
                json=registration_data
            ) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    print(f"✅ User registration successful: {data.get('message', 'Success')}")
                    return True
                elif response.status == 400:
                    # User might already exist
                    error_data = await response.json()
                    if "already exists" in str(error_data):
                        print("✅ User registration (user already exists)")
                        return True
                    else:
                        print(f"❌ Registration failed: {error_data}")
                        return False
                else:
                    print(f"❌ Registration failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False
    
    async def test_user_login(self) -> bool:
        """Test user login and store auth token"""
        try:
            login_data = {
                "email": "test@example.com",
                "password": "TestPass123!"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get("access_token")
                    print(f"✅ User login successful")
                    return True
                else:
                    error_data = await response.json()
                    print(f"❌ Login failed: {error_data}")
                    return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    async def test_authenticated_endpoint(self) -> bool:
        """Test an authenticated endpoint"""
        if not self.auth_token:
            print("❌ No auth token available for authenticated test")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with self.session.get(
                f"{self.base_url}/api/v1/auth/me",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Authenticated endpoint test passed: {data.get('email')}")
                    return True
                else:
                    print(f"❌ Authenticated endpoint failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Authenticated endpoint error: {e}")
            return False
    
    async def test_contact_creation(self) -> bool:
        """Test contact creation"""
        if not self.auth_token:
            print("❌ No auth token available for contact test")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            contact_data = {
                "firstname": "John",
                "lastname": "Doe",
                "email": "john.doe@example.com",
                "phone": "+1234567890"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/contacts",
                json=contact_data,
                headers=headers
            ) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    print(f"✅ Contact creation successful: {data.get('firstname')} {data.get('lastname')}")
                    return True
                else:
                    error_data = await response.json()
                    print(f"❌ Contact creation failed: {error_data}")
                    return False
        except Exception as e:
            print(f"❌ Contact creation error: {e}")
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all tests"""
        print("=" * 60)
        print("🧪 SALES ENGAGEMENT PLATFORM - LOCAL DEPLOYMENT TEST")
        print("=" * 60)
        
        # Wait for service to be ready
        if not await self.wait_for_service():
            return False
        
        tests = [
            ("Health Endpoint", self.test_health_endpoint),
            ("API Documentation", self.test_api_docs),
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("Authenticated Endpoint", self.test_authenticated_endpoint),
            ("Contact Creation", self.test_contact_creation),
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n🔍 Testing: {test_name}")
            try:
                result = await test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results.append((test_name, False))
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = 0
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
            if result:
                passed += 1
        
        total = len(results)
        print(f"\n📈 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All tests passed! The Sales Engagement Platform is working correctly.")
            print(f"🌐 API URL: {self.base_url}")
            print(f"📚 Documentation: {self.base_url}/docs")
            return True
        else:
            print("⚠️  Some tests failed. Check the logs above for details.")
            return False

async def main():
    """Main test function"""
    async with LocalTester() as tester:
        success = await tester.run_all_tests()
        return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test runner error: {e}")
        sys.exit(1)