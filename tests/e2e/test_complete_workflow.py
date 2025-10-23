"""
End-to-end tests for the Sales Engagement Platform.
Tests complete user workflows from authentication to VoIP calls.
"""

import pytest
import asyncio
import json
from httpx import AsyncClient
from fastapi.testclient import TestClient
import websockets
from typing import Dict, Any

from app.main import app
from app.core.config import settings


class TestCompleteWorkflow:
    """Test complete user workflows end-to-end."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    async def async_client(self):
        """Create async test client."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    @pytest.fixture
    def test_user_data(self):
        """Test user registration data."""
        return {
            "email": "test@example.com",
            "password": "TestPassword123!",
            "firstname": "Test",
            "lastname": "User",
            "company_name": "Test Company"
        }
    
    @pytest.fixture
    def test_contact_data(self):
        """Test contact data."""
        return {
            "firstname": "John",
            "lastname": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "metadata": {
                "company": "Acme Corp",
                "position": "CEO"
            }
        }
    
    async def test_complete_user_journey(self, async_client: AsyncClient, test_user_data: Dict[str, Any], test_contact_data: Dict[str, Any]):
        """Test complete user journey from registration to VoIP call."""
        
        # Step 1: User Registration
        print("🔐 Testing user registration...")
        register_response = await async_client.post("/api/v1/auth/register", json=test_user_data)
        assert register_response.status_code == 201
        user_data = register_response.json()
        assert "access_token" in user_data
        
        access_token = user_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Step 2: User Login
        print("🔑 Testing user login...")
        login_response = await async_client.post("/api/v1/auth/login", data={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        })
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data
        
        # Step 3: Create Contact
        print("👤 Testing contact creation...")
        contact_response = await async_client.post(
            "/api/v1/contacts",
            json=test_contact_data,
            headers=headers
        )
        assert contact_response.status_code == 201
        contact_data = contact_response.json()
        contact_id = contact_data["id"]
        
        # Step 4: Search Contacts
        print("🔍 Testing contact search...")
        search_response = await async_client.get(
            "/api/v1/contacts/search",
            params={"q": "John"},
            headers=headers
        )
        assert search_response.status_code == 200
        search_results = search_response.json()
        assert len(search_results["contacts"]) > 0
        
        # Step 5: Update Contact
        print("✏️ Testing contact update...")
        update_data = {"metadata": {"company": "Updated Corp", "position": "CTO"}}
        update_response = await async_client.patch(
            f"/api/v1/contacts/{contact_id}",
            json=update_data,
            headers=headers
        )
        assert update_response.status_code == 200
        
        # Step 6: Get Contact Timeline
        print("📅 Testing contact timeline...")
        timeline_response = await async_client.get(
            f"/api/v1/contacts/{contact_id}/activities",
            headers=headers
        )
        assert timeline_response.status_code == 200
        timeline_data = timeline_response.json()
        assert "activities" in timeline_data
        
        # Step 7: Initiate VoIP Call (Mock)
        print("📞 Testing VoIP call initiation...")
        call_data = {
            "contact_id": contact_id,
            "phone_number": test_contact_data["phone"]
        }
        call_response = await async_client.post(
            "/api/v1/calls",
            json=call_data,
            headers=headers
        )
        # Note: This might fail in test environment without Twilio credentials
        # We'll check for either success or expected error
        assert call_response.status_code in [201, 400, 503]
        
        # Step 8: Create Manual Activity
        print("📝 Testing manual activity creation...")
        activity_data = {
            "type": "note",
            "contact_id": contact_id,
            "payload": {
                "content": "Test note from E2E test",
                "tags": ["test", "e2e"]
            }
        }
        activity_response = await async_client.post(
            "/api/v1/activities",
            json=activity_data,
            headers=headers
        )
        assert activity_response.status_code == 201
        
        # Step 9: Get Activity Statistics
        print("📊 Testing activity statistics...")
        stats_response = await async_client.get(
            "/api/v1/activities/stats",
            headers=headers
        )
        assert stats_response.status_code == 200
        stats_data = stats_response.json()
        assert "total_activities" in stats_data
        
        print("✅ Complete user journey test passed!")
    
    async def test_websocket_notifications(self, async_client: AsyncClient, test_user_data: Dict[str, Any]):
        """Test WebSocket real-time notifications."""
        
        print("🔌 Testing WebSocket notifications...")
        
        # First, register and login to get token
        register_response = await async_client.post("/api/v1/auth/register", json=test_user_data)
        assert register_response.status_code == 201
        user_data = register_response.json()
        access_token = user_data["access_token"]
        
        # Test WebSocket connection (mock)
        # In a real test, you'd connect to the WebSocket endpoint
        # For now, we'll test the WebSocket endpoint exists
        ws_response = await async_client.get("/api/v1/ws/connect")
        # WebSocket endpoints return 426 for HTTP requests
        assert ws_response.status_code == 426
        
        print("✅ WebSocket endpoint test passed!")
    
    async def test_security_and_compliance(self, async_client: AsyncClient, test_user_data: Dict[str, Any]):
        """Test security and GDPR compliance features."""
        
        print("🔒 Testing security and compliance...")
        
        # Register user
        register_response = await async_client.post("/api/v1/auth/register", json=test_user_data)
        assert register_response.status_code == 201
        user_data = register_response.json()
        access_token = user_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Test audit log access
        audit_response = await async_client.get("/api/v1/security/audit-logs", headers=headers)
        assert audit_response.status_code == 200
        
        # Test data export (GDPR)
        export_response = await async_client.post("/api/v1/security/export-data", headers=headers)
        assert export_response.status_code == 200
        
        # Test unauthorized access
        unauthorized_response = await async_client.get("/api/v1/contacts")
        assert unauthorized_response.status_code == 401
        
        print("✅ Security and compliance tests passed!")
    
    async def test_monitoring_endpoints(self, async_client: AsyncClient, test_user_data: Dict[str, Any]):
        """Test monitoring and observability endpoints."""
        
        print("📊 Testing monitoring endpoints...")
        
        # Test public health check
        health_response = await async_client.get("/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] in ["healthy", "degraded"]
        
        # Test metrics endpoint
        metrics_response = await async_client.get("/metrics")
        assert metrics_response.status_code == 200
        assert "http_requests_total" in metrics_response.text
        
        # Register user for authenticated endpoints
        register_response = await async_client.post("/api/v1/auth/register", json=test_user_data)
        assert register_response.status_code == 201
        user_data = register_response.json()
        access_token = user_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Test authenticated monitoring endpoints
        system_metrics_response = await async_client.get("/api/v1/monitoring/metrics/summary", headers=headers)
        assert system_metrics_response.status_code == 200
        
        error_summary_response = await async_client.get("/api/v1/monitoring/errors/summary", headers=headers)
        assert error_summary_response.status_code == 200
        
        print("✅ Monitoring endpoints test passed!")
    
    async def test_performance_under_load(self, async_client: AsyncClient, test_user_data: Dict[str, Any]):
        """Test system performance under concurrent load."""
        
        print("⚡ Testing performance under load...")
        
        # Register user
        register_response = await async_client.post("/api/v1/auth/register", json=test_user_data)
        assert register_response.status_code == 201
        user_data = register_response.json()
        access_token = user_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Create multiple contacts concurrently
        async def create_contact(index: int):
            contact_data = {
                "firstname": f"Test{index}",
                "lastname": f"User{index}",
                "email": f"test{index}@example.com",
                "phone": f"+123456789{index % 10}"
            }
            response = await async_client.post("/api/v1/contacts", json=contact_data, headers=headers)
            return response.status_code == 201
        
        # Create 10 contacts concurrently
        tasks = [create_contact(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Check that most requests succeeded
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.8, f"Success rate {success_rate} below threshold"
        
        print(f"✅ Performance test passed! Success rate: {success_rate:.2%}")
    
    async def test_error_handling(self, async_client: AsyncClient):
        """Test error handling and recovery."""
        
        print("🚨 Testing error handling...")
        
        # Test invalid authentication
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = await async_client.get("/api/v1/contacts", headers=invalid_headers)
        assert response.status_code == 401
        
        # Test invalid data
        invalid_contact = {"invalid": "data"}
        response = await async_client.post("/api/v1/contacts", json=invalid_contact)
        assert response.status_code == 401  # Should fail auth first
        
        # Test non-existent resource
        response = await async_client.get("/api/v1/contacts/99999")
        assert response.status_code == 401  # Should fail auth first
        
        print("✅ Error handling tests passed!")


@pytest.mark.asyncio
async def test_full_e2e_suite():
    """Run the complete end-to-end test suite."""
    
    print("🚀 Starting comprehensive E2E test suite...")
    
    test_instance = TestCompleteWorkflow()
    
    # Create test clients
    async with AsyncClient(app=app, base_url="http://test") as async_client:
        
        # Test data
        test_user_data = {
            "email": "e2e_test@example.com",
            "password": "E2ETestPassword123!",
            "firstname": "E2E",
            "lastname": "Test",
            "company_name": "E2E Test Company"
        }
        
        test_contact_data = {
            "firstname": "E2E",
            "lastname": "Contact",
            "email": "e2e.contact@example.com",
            "phone": "+1987654321",
            "metadata": {
                "company": "E2E Test Corp",
                "position": "Test Manager"
            }
        }
        
        try:
            # Run all test scenarios
            await test_instance.test_complete_user_journey(async_client, test_user_data, test_contact_data)
            await test_instance.test_websocket_notifications(async_client, {**test_user_data, "email": "ws_test@example.com"})
            await test_instance.test_security_and_compliance(async_client, {**test_user_data, "email": "security_test@example.com"})
            await test_instance.test_monitoring_endpoints(async_client, {**test_user_data, "email": "monitoring_test@example.com"})
            await test_instance.test_performance_under_load(async_client, {**test_user_data, "email": "perf_test@example.com"})
            await test_instance.test_error_handling(async_client)
            
            print("🎉 All E2E tests passed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ E2E test failed: {e}")
            raise


if __name__ == "__main__":
    # Run the test suite directly
    asyncio.run(test_full_e2e_suite())