import pytest
import requests
import uuid
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


class TestResponseTimes:

    def test_user_creation_response_time(self, base_url, api_headers):
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "email": f"perf_{unique_id}@example.com",
            "password": "PerfTest123!",
            "first_name": "Perf",
            "last_name": "Test"
        }

        start_time = time.time()
        response = requests.post(
            f"{base_url}/v1/user/",
            json=user_data,
            headers=api_headers
        )
        elapsed = time.time() - start_time

        assert response.status_code == 201
        assert elapsed < 2.0, f"User creation took {elapsed:.2f}s, expected < 2.0s"

    def test_product_creation_response_time(self, base_url, api_headers, basic_auth):
        unique_id = str(uuid.uuid4())[:8]
        product_data = {
            "name": f"Perf Product {unique_id}",
            "description": "Performance test",
            "sku": f"PERF-{unique_id}",
            "manufacturer": "Test Mfg",
            "quantity": 100
        }

        start_time = time.time()
        response = requests.post(
            f"{base_url}/v1/product/",
            json=product_data,
            headers=api_headers,
            auth=basic_auth
        )
        elapsed = time.time() - start_time

        assert response.status_code == 201
        assert elapsed < 2.0, f"Product creation took {elapsed:.2f}s, expected < 2.0s"


class TestConcurrentRequests:

    def test_concurrent_user_creation(self, base_url, api_headers):
        def create_user(index):
            unique_id = str(uuid.uuid4())[:8]
            user_data = {
                "email": f"concurrent_{index}_{unique_id}@example.com",
                "password": "Concurrent123!",
                "first_name": f"User{index}",
                "last_name": "Concurrent"
            }
            response = requests.post(
                f"{base_url}/v1/user/",
                json=user_data,
                headers=api_headers
            )
            return response.status_code, index

        # Create 10 users concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_user, i) for i in range(10)]
            results = [future.result() for future in as_completed(futures)]
        success_count = sum(1 for status, _ in results if status == 201)
        assert success_count == 10, f"Only {success_count}/10 concurrent user creations succeeded"

    def test_concurrent_product_creation(self, base_url, api_headers, basic_auth):
        def create_product(index):
            unique_id = str(uuid.uuid4())[:8]
            product_data = {
                "name": f"Concurrent Product {index}_{unique_id}",
                "description": "Concurrent test",
                "sku": f"CONC-{index}-{unique_id}",
                "manufacturer": "Test Mfg",
                "quantity": min(index * 5, 100)
            }
            response = requests.post(
                f"{base_url}/v1/product/",
                json=product_data,
                headers=api_headers,
                auth=basic_auth
            )
            return response.status_code, index

        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(create_product, i) for i in range(15)]
            results = [future.result() for future in as_completed(futures)]
        success_count = sum(1 for status, _ in results if status == 201)
        assert success_count == 15, f"Only {success_count}/15 concurrent product creations succeeded"

class TestLargeDatasets:

    def test_create_20_products(self, base_url, api_headers, basic_auth):
        start_time = time.time()
        created_count = 0

        for i in range(20):
            unique_id = str(uuid.uuid4())[:8]
            product_data = {
                "name": f"Bulk Product {i}_{unique_id}",
                "description": f"Bulk test product number {i}",
                "sku": f"BULK-{i}-{unique_id}",
                "manufacturer": "Bulk Mfg",
                "quantity": min(i * 3, 100) 
            }

            response = requests.post(
                f"{base_url}/v1/product/",
                json=product_data,
                headers=api_headers,
                auth=basic_auth
            )

            if response.status_code == 201:
                created_count += 1

        elapsed = time.time() - start_time

        assert created_count == 20, f"Only created {created_count}/20 products"
        assert elapsed < 15.0, f"Creating 20 products took {elapsed:.2f}s, expected < 15s"

        avg_time = elapsed / 20
        assert avg_time < 0.75, f"Average time per product: {avg_time:.2f}s, expected < 0.75s"

    def test_create_30_users(self, base_url, api_headers):
        start_time = time.time()
        created_count = 0

        for i in range(30):
            unique_id = str(uuid.uuid4())[:8]
            user_data = {
                "email": f"bulk_user_{i}_{unique_id}@example.com",
                "password": "BulkTest123!",
                "first_name": f"BulkUser{i}",
                "last_name": "Test"
            }

            response = requests.post(
                f"{base_url}/v1/user/",
                json=user_data,
                headers=api_headers
            )

            if response.status_code == 201:
                created_count += 1

        elapsed = time.time() - start_time

        assert created_count == 30, f"Only created {created_count}/30 users"
        assert elapsed < 20.0, f"Creating 30 users took {elapsed:.2f}s, expected < 20s"