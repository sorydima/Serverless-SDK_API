#!/usr/bin/env python3
"""
Performance Benchmarking Suite for Serverless-SDK_API Microservices

Tests performance characteristics including:
- API response times
- Throughput and concurrency
- Resource utilization
- Scalability metrics
- Database and cache performance
"""

import requests
import time
import threading
import statistics
import json
import concurrent.futures
from typing import List, Dict, Any
import psutil
import os

class PerformanceTester:
    def __init__(self):
        self.base_urls = {
            'mesh-gateway': 'http://localhost:8080',
            'ai-core': 'http://localhost:8081',
            'storage': 'http://localhost:8082'
        }
        self.results = {}
        self.system_metrics = []

    def measure_response_time(self, url: str, method: str = 'GET', data: Dict = None, headers: Dict = None) -> float:
        """Measure response time for a single request"""
        start_time = time.time()
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            end_time = time.time()
            return (end_time - start_time) * 1000  # Convert to milliseconds
        except Exception as e:
            print(f"Request failed: {e}")
            return float('inf')

    def benchmark_endpoint(self, url: str, method: str = 'GET', data: Dict = None,
                          num_requests: int = 100, concurrent_users: int = 10) -> Dict[str, Any]:
        """Benchmark an endpoint with multiple concurrent requests"""

        def single_request():
            return self.measure_response_time(url, method, data)

        print(f"Benchmarking {url} with {num_requests} requests, {concurrent_users} concurrent users...")

        response_times = []

        # Run requests in batches to simulate concurrent users
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(single_request) for _ in range(num_requests)]
            for future in concurrent.futures.as_completed(futures):
                response_time = future.result()
                if response_time != float('inf'):
                    response_times.append(response_time)

        if not response_times:
            return {
                'error': 'All requests failed',
                'total_requests': num_requests,
                'successful_requests': 0
            }

        return {
            'total_requests': num_requests,
            'successful_requests': len(response_times),
            'success_rate': len(response_times) / num_requests * 100,
            'avg_response_time': statistics.mean(response_times),
            'median_response_time': statistics.median(response_times),
            'min_response_time': min(response_times),
            'max_response_time': max(response_times),
            '95th_percentile': statistics.quantiles(response_times, n=20)[18],  # 95th percentile
            '99th_percentile': statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else max(response_times)
        }

    def monitor_system_resources(self, duration_seconds: int = 60):
        """Monitor system resource usage during testing"""
        print(f"Monitoring system resources for {duration_seconds} seconds...")

        start_time = time.time()
        metrics = []

        while time.time() - start_time < duration_seconds:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            metrics.append({
                'timestamp': time.time(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_gb': memory.used / (1024**3),
                'disk_percent': disk.percent
            })

        return metrics

    def test_mesh_gateway_performance(self) -> Dict[str, Any]:
        """Test Mesh Gateway performance"""
        print("\n=== Testing Mesh Gateway Performance ===")

        results = {}

        # Health check performance
        health_url = f"{self.base_urls['mesh-gateway']}/health"
        results['health_check'] = self.benchmark_endpoint(health_url, num_requests=500, concurrent_users=20)

        # Device discovery performance
        devices_url = f"{self.base_urls['mesh-gateway']}/devices"
        results['device_discovery'] = self.benchmark_endpoint(devices_url, num_requests=200, concurrent_users=10)

        # Route calculation performance
        route_url = f"{self.base_urls['mesh-gateway']}/routes/calculate"
        route_data = {
            "source": "device_001",
            "destination": "device_002",
            "constraints": {"max_hops": 5}
        }
        results['route_calculation'] = self.benchmark_endpoint(
            route_url, method='POST', data=route_data, num_requests=100, concurrent_users=5
        )

        return results

    def test_ai_core_performance(self) -> Dict[str, Any]:
        """Test AI Core performance"""
        print("\n=== Testing AI Core Performance ===")

        results = {}

        # Health check performance
        health_url = f"{self.base_urls['ai-core']}/health"
        results['health_check'] = self.benchmark_endpoint(health_url, num_requests=500, concurrent_users=20)

        # Model listing performance
        models_url = f"{self.base_urls['ai-core']}/models"
        results['model_listing'] = self.benchmark_endpoint(models_url, num_requests=200, concurrent_users=10)

        # Inference performance (lightweight test)
        inference_url = f"{self.base_urls['ai-core']}/inference"
        inference_data = {
            "model": "quantum",
            "input": [0.1, 0.2, 0.3, 0.4],
            "parameters": {"temperature": 0.7}
        }
        results['inference'] = self.benchmark_endpoint(
            inference_url, method='POST', data=inference_data, num_requests=50, concurrent_users=5
        )

        return results

    def test_storage_performance(self) -> Dict[str, Any]:
        """Test Storage service performance"""
        print("\n=== Testing Storage Performance ===")

        results = {}

        # Health check performance
        health_url = f"{self.base_urls['storage']}/health"
        results['health_check'] = self.benchmark_endpoint(health_url, num_requests=500, concurrent_users=20)

        # Cache operations performance
        cache_url = f"{self.base_urls['storage']}/cache"
        cache_data = {
            "key": "perf_test_key",
            "value": {"data": "test_value", "timestamp": time.time()},
            "ttl": 300
        }
        results['cache_set'] = self.benchmark_endpoint(
            cache_url, method='POST', data=cache_data, num_requests=200, concurrent_users=10
        )

        # File storage performance (small files)
        objects_url = f"{self.base_urls['storage']}/objects"
        file_data = {
            "key": "perf_test_file.txt",
            "content": "This is a performance test file content",
            "metadata": {"type": "text", "size": 40}
        }
        results['file_storage'] = self.benchmark_endpoint(
            objects_url, method='POST', data=file_data, num_requests=50, concurrent_users=5
        )

        return results

    def test_concurrent_load(self) -> Dict[str, Any]:
        """Test system under concurrent load from all services"""
        print("\n=== Testing Concurrent Load ===")

        def mixed_workload():
            """Simulate mixed workload across all services"""
            results = []

            # Mesh Gateway requests
            try:
                start = time.time()
                response = requests.get(f"{self.base_urls['mesh-gateway']}/health", timeout=10)
                results.append(('mesh-health', (time.time() - start) * 1000))
            except:
                results.append(('mesh-health', float('inf')))

            # AI Core requests
            try:
                start = time.time()
                response = requests.get(f"{self.base_urls['ai-core']}/models", timeout=10)
                results.append(('ai-models', (time.time() - start) * 1000))
            except:
                results.append(('ai-models', float('inf')))

            # Storage requests
            try:
                start = time.time()
                cache_data = {"key": "load_test", "value": "test", "ttl": 60}
                response = requests.post(f"{self.base_urls['storage']}/cache", json=cache_data, timeout=10)
                results.append(('storage-cache', (time.time() - start) * 1000))
            except:
                results.append(('storage-cache', float('inf')))

            return results

        # Run concurrent mixed workload
        num_threads = 20
        num_iterations = 10

        all_response_times = []

        print(f"Running mixed workload with {num_threads} concurrent threads, {num_iterations} iterations each...")

        for iteration in range(num_iterations):
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(mixed_workload) for _ in range(num_threads)]
                for future in concurrent.futures.as_completed(futures):
                    results = future.result()
                    all_response_times.extend([rt for _, rt in results if rt != float('inf')])

        if not all_response_times:
            return {'error': 'All concurrent requests failed'}

        return {
            'total_requests': len(all_response_times),
            'avg_response_time': statistics.mean(all_response_times),
            'median_response_time': statistics.median(all_response_times),
            '95th_percentile': statistics.quantiles(all_response_times, n=20)[18] if len(all_response_times) >= 20 else max(all_response_times),
            'max_response_time': max(all_response_times),
            'min_response_time': min(all_response_times)
        }

    def generate_performance_report(self):
        """Generate comprehensive performance report"""
        print("\n" + "=" * 80)
        print("PERFORMANCE TEST REPORT")
        print("=" * 80)

        # Overall system performance
        print("\n📊 OVERALL SYSTEM PERFORMANCE")
        print("-" * 40)

        if 'concurrent_load' in self.results:
            concurrent = self.results['concurrent_load']
            print(".2f"
            print(".2f"
            print(".2f"

        # Service-specific performance
        services = ['mesh_gateway', 'ai_core', 'storage']
        for service in services:
            if service in self.results:
                print(f"\n🔧 {service.upper().replace('_', ' ')} PERFORMANCE")
                print("-" * 40)

                for endpoint, metrics in self.results[service].items():
                    if 'error' in metrics:
                        print(f"❌ {endpoint}: {metrics['error']}")
                        continue

                    success_rate = metrics.get('success_rate', 0)
                    avg_time = metrics.get('avg_response_time', 0)
                    p95_time = metrics.get('95th_percentile', 0)

                    status = "✅" if success_rate >= 95 and avg_time < 1000 else "⚠️" if success_rate >= 90 else "❌"
                    print(f"{status} {endpoint}:")
                    print(".1f"                    print(".2f"                    print(".2f"
        # System resource usage
        if self.system_metrics:
            print("\n💻 SYSTEM RESOURCE USAGE")
            print("-" * 40)

            cpu_usage = [m['cpu_percent'] for m in self.system_metrics]
            memory_usage = [m['memory_percent'] for m in self.system_metrics]

            print(".1f"            print(".1f"            print(".1f"            print(".1f"
        # Performance assessment
        print("\n🎯 PERFORMANCE ASSESSMENT")
        print("-" * 40)

        all_avg_times = []
        all_success_rates = []

        for service_results in self.results.values():
            if isinstance(service_results, dict):
                for endpoint_metrics in service_results.values():
                    if isinstance(endpoint_metrics, dict) and 'avg_response_time' in endpoint_metrics:
                        all_avg_times.append(endpoint_metrics['avg_response_time'])
                        if 'success_rate' in endpoint_metrics:
                            all_success_rates.append(endpoint_metrics['success_rate'])

        if all_avg_times:
            overall_avg_time = statistics.mean(all_avg_times)
            overall_success_rate = statistics.mean(all_success_rates) if all_success_rates else 100

            if overall_success_rate >= 95 and overall_avg_time < 500:
                assessment = "EXCELLENT - System performing within target parameters"
            elif overall_success_rate >= 90 and overall_avg_time < 1000:
                assessment = "GOOD - System performing adequately with minor optimizations needed"
            elif overall_success_rate >= 80:
                assessment = "FAIR - System needs performance optimizations"
            else:
                assessment = "POOR - System requires immediate attention"

            print(f"Assessment: {assessment}")
            print(".2f"            print(".1f"
        # Save detailed results
        report_file = "performance_report.json"
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': time.time(),
                'results': self.results,
                'system_metrics': self.system_metrics
            }, f, indent=2)
        print(f"\n📄 Detailed report saved to {report_file}")

    def run_performance_tests(self):
        """Run the complete performance test suite"""
        print("🚀 Starting Serverless-SDK_API Performance Test Suite")
        print("=" * 60)

        try:
            # Start system monitoring in background
            monitor_thread = threading.Thread(
                target=lambda: self.system_metrics.extend(self.monitor_system_resources(300))
            )
            monitor_thread.daemon = True
            monitor_thread.start()

            # Run individual service tests
            self.results['mesh_gateway'] = self.test_mesh_gateway_performance()
            self.results['ai_core'] = self.test_ai_core_performance()
            self.results['storage'] = self.test_storage_performance()

            # Run concurrent load test
            self.results['concurrent_load'] = self.test_concurrent_load()

            # Generate report
            self.generate_performance_report()

            return True

        except Exception as e:
            print(f"❌ Performance testing failed: {e}")
            return False

def main():
    """Main performance testing execution"""
    tester = PerformanceTester()

    try:
        success = tester.run_performance_tests()
        exit_code = 0 if success else 1
        print(f"\n🏁 Performance testing completed with exit code: {exit_code}")
        return exit_code
    except KeyboardInterrupt:
        print("\n⏹️  Performance testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Performance testing failed with error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
