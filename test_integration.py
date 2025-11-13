#!/usr/bin/env python3
"""
Integration Test Suite for Serverless-SDK_API Microservices

Tests the complete microservices architecture including:
- Service startup and health checks
- API endpoint functionality
- Inter-service communication
- Database operations
- Cache operations
- Monitoring and metrics
- Security features
"""

import requests
import json
import time
import subprocess
import sys
import os
from typing import Dict, List, Optional
import yaml

class MicroservicesTester:
    def __init__(self):
        self.base_urls = {
            'mesh-gateway': 'http://localhost:8080',
            'ai-core': 'http://localhost:8081',
            'storage': 'http://localhost:8082',
            'grafana': 'http://localhost:3000',
            'prometheus': 'http://localhost:9090'
        }
        self.test_results = []
        self.docker_compose_process = None

    def log_test(self, test_name: str, status: str, message: str = ""):
        """Log test results"""
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'timestamp': time.time()
        }
        self.test_results.append(result)
        print(f"[{status.upper()}] {test_name}: {message}")

    def start_services(self):
        """Start all services using docker-compose"""
        try:
            print("Starting microservices with docker-compose...")
            self.docker_compose_process = subprocess.Popen(
                ['docker-compose', 'up', '-d'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            time.sleep(30)  # Wait for services to start
            return True
        except Exception as e:
            self.log_test("Service Startup", "FAILED", f"Failed to start services: {str(e)}")
            return False

    def stop_services(self):
        """Stop all services"""
        try:
            if self.docker_compose_process:
                self.docker_compose_process.terminate()
                self.docker_compose_process.wait()

            subprocess.run(['docker-compose', 'down'], cwd=os.getcwd(), capture_output=True)
            print("Services stopped successfully")
        except Exception as e:
            print(f"Error stopping services: {e}")

    def test_service_health(self, service_name: str, url: str) -> bool:
        """Test service health endpoint"""
        try:
            response = requests.get(f"{url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    self.log_test(f"{service_name} Health", "PASSED", "Service is healthy")
                    return True
            self.log_test(f"{service_name} Health", "FAILED", f"Health check failed: {response.status_code}")
            return False
        except Exception as e:
            self.log_test(f"{service_name} Health", "FAILED", f"Health check error: {str(e)}")
            return False

    def test_mesh_gateway_endpoints(self) -> bool:
        """Test Mesh Gateway service endpoints"""
        base_url = self.base_urls['mesh-gateway']
        tests_passed = 0
        total_tests = 0

        # Test mesh status
        total_tests += 1
        try:
            response = requests.get(f"{base_url}/mesh/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'device_count' in data and 'active_routes' in data:
                    tests_passed += 1
                    self.log_test("Mesh Gateway Status", "PASSED", "Status endpoint working")
                else:
                    self.log_test("Mesh Gateway Status", "FAILED", "Invalid response format")
            else:
                self.log_test("Mesh Gateway Status", "FAILED", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Mesh Gateway Status", "FAILED", str(e))

        # Test device discovery
        total_tests += 1
        try:
            response = requests.get(f"{base_url}/devices", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    tests_passed += 1
                    self.log_test("Device Discovery", "PASSED", f"Found {len(data)} devices")
                else:
                    self.log_test("Device Discovery", "FAILED", "Invalid response format")
            else:
                self.log_test("Device Discovery", "FAILED", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Device Discovery", "FAILED", str(e))

        # Test route calculation
        total_tests += 1
        try:
            payload = {
                "source": "device_001",
                "destination": "device_002",
                "constraints": {"max_hops": 5}
            }
            response = requests.post(f"{base_url}/routes/calculate", json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'route' in data and 'cost' in data:
                    tests_passed += 1
                    self.log_test("Route Calculation", "PASSED", "Route calculated successfully")
                else:
                    self.log_test("Route Calculation", "FAILED", "Invalid response format")
            else:
                self.log_test("Route Calculation", "FAILED", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Route Calculation", "FAILED", str(e))

        return tests_passed == total_tests

    def test_ai_core_endpoints(self) -> bool:
        """Test AI Core service endpoints"""
        base_url = self.base_urls['ai-core']
        tests_passed = 0
        total_tests = 0

        # Test model listing
        total_tests += 1
        try:
            response = requests.get(f"{base_url}/models", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    tests_passed += 1
                    self.log_test("AI Models List", "PASSED", f"Found {len(data)} models")
                else:
                    self.log_test("AI Models List", "FAILED", "Invalid response format")
            else:
                self.log_test("AI Models List", "FAILED", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("AI Models List", "FAILED", str(e))

        # Test inference
        total_tests += 1
        try:
            payload = {
                "model": "quantum",
                "input": [0.1, 0.2, 0.3, 0.4],
                "parameters": {"temperature": 0.7}
            }
            response = requests.post(f"{base_url}/inference", json=payload, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if 'result' in data and 'confidence' in data:
                    tests_passed += 1
                    self.log_test("AI Inference", "PASSED", f"Inference completed with confidence {data.get('confidence', 'N/A')}")
                else:
                    self.log_test("AI Inference", "FAILED", "Invalid response format")
            else:
                self.log_test("AI Inference", "FAILED", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("AI Inference", "FAILED", str(e))

        # Test quantum circuit execution
        total_tests += 1
        try:
            payload = {
                "circuit": "H(0); CNOT(0,1); MEASURE",
                "shots": 1024
            }
            response = requests.post(f"{base_url}/quantum/execute", json=payload, timeout=20)
            if response.status_code == 200:
                data = response.json()
                if 'results' in data:
                    tests_passed += 1
                    self.log_test("Quantum Execution", "PASSED", "Quantum circuit executed successfully")
                else:
                    self.log_test("Quantum Execution", "FAILED", "Invalid response format")
            else:
                self.log_test("Quantum Execution", "FAILED", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Quantum Execution", "FAILED", str(e))

        return tests_passed == total_tests

    def test_storage_endpoints(self) -> bool:
        """Test Storage service endpoints"""
        base_url = self.base_urls['storage']
        tests_passed = 0
        total_tests = 0

        # Test database record operations
        total_tests += 1
        try:
            # Insert record
            record = {
                "table": "mesh_devices",
                "data": {
                    "device_id": "test_device_001",
                    "device_type": "sensor",
                    "location": {"lat": 37.7749, "lon": -122.4194},
                    "status": "active"
                }
            }
            response = requests.post(f"{base_url}/records", json=record, timeout=10)
            if response.status_code == 201:
                data = response.json()
                record_id = data.get('id')
                tests_passed += 1
                self.log_test("Database Insert", "PASSED", f"Record inserted with ID: {record_id}")
            else:
                self.log_test("Database Insert", "FAILED", f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Database Insert", "FAILED", str(e))
            return False

        # Test cache operations
        total_tests += 1
        try:
            # Set cache value
            cache_data = {
                "key": "test_key",
                "value": {"session_id": "abc123", "user_id": "user001"},
                "ttl": 300
            }
            response = requests.post(f"{base_url}/cache", json=cache_data, timeout=10)
            if response.status_code == 200:
                tests_passed += 1
                self.log_test("Cache Set", "PASSED", "Cache value set successfully")
            else:
                self.log_test("Cache Set", "FAILED", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Cache Set", "FAILED", str(e))

        # Test file storage
        total_tests += 1
        try:
            # Store file
            file_data = {
                "key": "test_file.txt",
                "content": "This is a test file content",
                "metadata": {"type": "text", "size": 30}
            }
            response = requests.post(f"{base_url}/objects", json=file_data, timeout=10)
            if response.status_code == 201:
                data = response.json()
                object_key = data.get('key')
                tests_passed += 1
                self.log_test("File Storage", "PASSED", f"File stored with key: {object_key}")
            else:
                self.log_test("File Storage", "FAILED", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("File Storage", "FAILED", str(e))

        return tests_passed == total_tests

    def test_monitoring_setup(self) -> bool:
        """Test monitoring and metrics setup"""
        tests_passed = 0
        total_tests = 0

        # Test Prometheus metrics
        total_tests += 1
        try:
            response = requests.get(f"{self.base_urls['prometheus']}/api/v1/targets", timeout=10)
            if response.status_code == 200:
                data = response.json()
                active_targets = len([t for t in data.get('data', {}).get('activeTargets', []) if t.get('health') == 'up'])
                if active_targets > 0:
                    tests_passed += 1
                    self.log_test("Prometheus Targets", "PASSED", f"{active_targets} targets are healthy")
                else:
                    self.log_test("Prometheus Targets", "FAILED", "No healthy targets found")
            else:
                self.log_test("Prometheus Targets", "FAILED", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Prometheus Targets", "FAILED", str(e))

        # Test Grafana accessibility
        total_tests += 1
        try:
            response = requests.get(f"{self.base_urls['grafana']}/api/health", timeout=10)
            if response.status_code == 200:
                tests_passed += 1
                self.log_test("Grafana Health", "PASSED", "Grafana is accessible")
            else:
                self.log_test("Grafana Health", "FAILED", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Grafana Health", "FAILED", str(e))

        return tests_passed == total_tests

    def test_inter_service_communication(self) -> bool:
        """Test communication between services"""
        tests_passed = 0
        total_tests = 0

        # Test mesh gateway -> storage communication (device registration)
        total_tests += 1
        try:
            # Simulate device registration through mesh gateway
            device_data = {
                "device_id": "comm_test_device",
                "device_type": "test_sensor",
                "capabilities": ["temperature", "humidity"]
            }
            response = requests.post(
                f"{self.base_urls['mesh-gateway']}/devices/register",
                json=device_data,
                timeout=15
            )
            if response.status_code == 200:
                tests_passed += 1
                self.log_test("Inter-service Communication", "PASSED", "Device registration successful")
            else:
                self.log_test("Inter-service Communication", "FAILED", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Inter-service Communication", "FAILED", str(e))

        return tests_passed == total_tests

    def run_performance_tests(self) -> bool:
        """Run basic performance tests"""
        tests_passed = 0
        total_tests = 0

        # Test API response times
        endpoints = [
            (f"{self.base_urls['mesh-gateway']}/health", "Mesh Gateway Health"),
            (f"{self.base_urls['ai-core']}/health", "AI Core Health"),
            (f"{self.base_urls['storage']}/health", "Storage Health")
        ]

        for url, name in endpoints:
            total_tests += 1
            try:
                start_time = time.time()
                response = requests.get(url, timeout=5)
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds

                if response.status_code == 200 and response_time < 1000:  # Less than 1 second
                    tests_passed += 1
                    self.log_test(f"{name} Performance", "PASSED", f"Response time: {response_time:.2f}ms")
                else:
                    self.log_test(f"{name} Performance", "FAILED", f"Response time: {response_time:.2f}ms")
            except Exception as e:
                self.log_test(f"{name} Performance", "FAILED", str(e))

        return tests_passed == total_tests

    def run_all_tests(self):
        """Run the complete test suite"""
        print("=" * 60)
        print("Serverless-SDK_API Microservices Integration Test Suite")
        print("=" * 60)

        # Start services
        if not self.start_services():
            print("Failed to start services. Aborting tests.")
            return False

        try:
            # Wait for services to be ready
            print("Waiting for services to be ready...")
            time.sleep(10)

            # Run all test categories
            test_categories = [
                ("Service Health Checks", self.test_all_service_health),
                ("Mesh Gateway Functionality", self.test_mesh_gateway_endpoints),
                ("AI Core Functionality", self.test_ai_core_endpoints),
                ("Storage Functionality", self.test_storage_endpoints),
                ("Monitoring Setup", self.test_monitoring_setup),
                ("Inter-service Communication", self.test_inter_service_communication),
                ("Performance Tests", self.run_performance_tests)
            ]

            all_passed = True
            for category_name, test_func in test_categories:
                print(f"\n--- {category_name} ---")
                if not test_func():
                    all_passed = False

            # Generate test report
            self.generate_test_report()

            return all_passed

        finally:
            # Stop services
            self.stop_services()

    def test_all_service_health(self) -> bool:
        """Test health of all services"""
        services_healthy = 0
        total_services = len(self.base_urls) - 2  # Exclude grafana and prometheus from health checks

        for service_name, url in self.base_urls.items():
            if service_name in ['grafana', 'prometheus']:
                continue
            if self.test_service_health(service_name, url):
                services_healthy += 1

        return services_healthy == total_services

    def generate_test_report(self):
        """Generate a comprehensive test report"""
        print("\n" + "=" * 60)
        print("TEST REPORT SUMMARY")
        print("=" * 60)

        passed = len([r for r in self.test_results if r['status'] == 'PASSED'])
        failed = len([r for r in self.test_results if r['status'] == 'FAILED'])
        total = len(self.test_results)

        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(".1f")

        if failed > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if result['status'] == 'FAILED':
                    print(f"  - {result['test']}: {result['message']}")

        # Save detailed report
        report_file = "test_report.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\nDetailed report saved to {report_file}")

def main():
    """Main test execution"""
    tester = MicroservicesTester()

    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        tester.stop_services()
        sys.exit(1)
    except Exception as e:
        print(f"Test suite failed with error: {e}")
        tester.stop_services()
        sys.exit(1)

if __name__ == "__main__":
    main()
