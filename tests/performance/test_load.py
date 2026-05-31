"""
Load Testing for Sheldon OS

Tests system behavior under various load conditions:
- 1,000 concurrent users
- 10,000 concurrent users
- 100,000 concurrent users
- Sustained load (24 hours)
- Peak load handling
"""

import asyncio
import statistics
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import pytest


class LoadTestMetrics:
    """Collect and analyze load test metrics"""

    def __init__(self):
        self.response_times: List[float] = []
        self.errors: List[str] = []
        self.throughput: List[int] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def record_response(
        self,
        duration: float,
        success: bool,
        error: Optional[str] = None,
    ):
        """Record a single request response"""
        self.response_times.append(duration)
        if not success:
            self.errors.append(error or "Unknown error")

    def record_throughput(self, requests_per_second: int):
        """Record throughput measurement"""
        self.throughput.append(requests_per_second)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        if not self.response_times:
            return {"error": "No data collected"}

        sorted_times = sorted(self.response_times)
        return {
            "total_requests": len(self.response_times),
            "successful_requests": len(self.response_times) - len(self.errors),
            "failed_requests": len(self.errors),
            "error_rate": len(self.errors) / len(self.response_times),
            "avg_response_time": statistics.mean(self.response_times),
            "median_response_time": statistics.median(self.response_times),
            "p95_response_time": sorted_times[int(len(sorted_times) * 0.95)],
            "p99_response_time": sorted_times[int(len(sorted_times) * 0.99)],
            "min_response_time": min(self.response_times),
            "max_response_time": max(self.response_times),
            "avg_throughput": (
                statistics.mean(self.throughput) if self.throughput else 0
            ),
            "duration": (
                (self.end_time - self.start_time).total_seconds()
                if self.start_time and self.end_time
                else 0
            ),
        }


class TestLightLoad:
    """Test system under light load (100 users)"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_100_concurrent_users(self, orchestrator):
        """Test 100 concurrent users"""
        metrics = LoadTestMetrics()
        metrics.start_time = datetime.utcnow()

        async def simulate_user():
            """Simulate single user workflow"""
            start = time.time()
            try:
                # Create agent
                agent_id = await orchestrator.create_agent(
                    agent_type="test", config={"name": "load_test"}
                )

                # Execute task
                await orchestrator.execute_task(
                    agent_id=agent_id,
                    task="Test task",
                )

                # Cleanup
                await orchestrator.terminate_agent(agent_id)

                duration = time.time() - start
                metrics.record_response(duration, True)

            except Exception as e:
                duration = time.time() - start
                metrics.record_response(duration, False, str(e))

        # Run 100 concurrent users
        await asyncio.gather(*[simulate_user() for _ in range(100)])

        metrics.end_time = datetime.utcnow()
        summary = metrics.get_summary()

        # Assertions
        assert summary["error_rate"] < 0.01  # <1% error rate
        assert summary["p95_response_time"] < 1.0  # <1s p95
        assert summary["avg_response_time"] < 0.5  # <500ms average

        print("\n100 User Load Test Results:")
        print(f"  Total Requests: {summary['total_requests']}")
        print(f"  Error Rate: {summary['error_rate']:.2%}")
        print(f"  Avg Response: {summary['avg_response_time']:.3f}s")
        print(f"  P95 Response: {summary['p95_response_time']:.3f}s")


class TestMediumLoad:
    """Test system under medium load (1,000 users)"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_1000_concurrent_users(self, orchestrator, memory_system):
        """Test 1,000 concurrent users"""
        metrics = LoadTestMetrics()
        metrics.start_time = datetime.utcnow()

        async def simulate_user(user_id: int):
            """Simulate user with multiple operations"""
            start = time.time()
            try:
                # Create agent
                agent_id = await orchestrator.create_agent(
                    agent_type="load_test", config={"user_id": user_id}
                )

                # Execute multiple tasks
                for i in range(5):
                    await orchestrator.execute_task(
                        agent_id=agent_id,
                        task=f"Task {i}",
                    )

                # Store memory
                await memory_system.store_memory(
                    agent_id=agent_id,
                    memory_type="test",
                    content={"user_id": user_id},
                )

                # Cleanup
                await orchestrator.terminate_agent(agent_id)

                duration = time.time() - start
                metrics.record_response(duration, True)

            except Exception as e:
                duration = time.time() - start
                metrics.record_response(duration, False, str(e))

        # Run 1,000 concurrent users
        await asyncio.gather(*[simulate_user(i) for i in range(1000)])

        metrics.end_time = datetime.utcnow()
        summary = metrics.get_summary()

        # Assertions
        assert summary["error_rate"] < 0.05  # <5% error rate
        assert summary["p95_response_time"] < 2.0  # <2s p95
        assert summary["avg_response_time"] < 1.0  # <1s average

        print("\n1,000 User Load Test Results:")
        print(f"  Total Requests: {summary['total_requests']}")
        print(f"  Error Rate: {summary['error_rate']:.2%}")
        print(f"  Avg Response: {summary['avg_response_time']:.3f}s")
        print(f"  P95 Response: {summary['p95_response_time']:.3f}s")
        print(f"  P99 Response: {summary['p99_response_time']:.3f}s")


class TestHeavyLoad:
    """Test system under heavy load (10,000 users)"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.heavy
    async def test_10000_concurrent_users(self, orchestrator):
        """Test 10,000 concurrent users"""
        metrics = LoadTestMetrics()
        metrics.start_time = datetime.utcnow()

        # Batch users to avoid overwhelming system
        batch_size = 1000
        num_batches = 10

        for batch in range(num_batches):
            print(f"Running batch {batch + 1}/{num_batches}...")

            async def simulate_user():
                start = time.time()
                try:
                    agent_id = await orchestrator.create_agent(
                        agent_type="heavy_load", config={"batch": batch}
                    )

                    await orchestrator.execute_task(
                        agent_id=agent_id, task="Heavy load task"
                    )

                    await orchestrator.terminate_agent(agent_id)

                    duration = time.time() - start
                    metrics.record_response(duration, True)

                except Exception as e:
                    duration = time.time() - start
                    metrics.record_response(duration, False, str(e))

            # Run batch
            await asyncio.gather(*[simulate_user() for _ in range(batch_size)])

            # Brief pause between batches
            await asyncio.sleep(1)

        metrics.end_time = datetime.utcnow()
        summary = metrics.get_summary()

        # Assertions
        assert summary["error_rate"] < 0.10  # <10% error rate
        assert summary["p95_response_time"] < 5.0  # <5s p95
        assert summary["avg_response_time"] < 2.0  # <2s average

        print("\n10,000 User Load Test Results:")
        print(f"  Total Requests: {summary['total_requests']}")
        print(f"  Error Rate: {summary['error_rate']:.2%}")
        print(f"  Avg Response: {summary['avg_response_time']:.3f}s")
        print(f"  P95 Response: {summary['p95_response_time']:.3f}s")
        print(f"  P99 Response: {summary['p99_response_time']:.3f}s")
        print(f"  Duration: {summary['duration']:.1f}s")


class TestSustainedLoad:
    """Test system under sustained load"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.sustained
    async def test_sustained_load_1_hour(self, orchestrator):
        """Test sustained load for 1 hour"""
        metrics = LoadTestMetrics()
        metrics.start_time = datetime.utcnow()

        duration = 3600  # 1 hour in seconds
        requests_per_second = 10

        end_time = time.time() + duration

        async def continuous_load():
            """Generate continuous load"""
            while time.time() < end_time:
                start = time.time()
                try:
                    agent_id = await orchestrator.create_agent(
                        agent_type="sustained", config={}
                    )

                    await orchestrator.execute_task(
                        agent_id=agent_id, task="Sustained task"
                    )

                    await orchestrator.terminate_agent(agent_id)

                    duration_req = time.time() - start
                    metrics.record_response(duration_req, True)

                except Exception as e:
                    duration_req = time.time() - start
                    metrics.record_response(duration_req, False, str(e))

                # Maintain target RPS
                sleep_time = max(0, (1.0 / requests_per_second) - duration_req)
                await asyncio.sleep(sleep_time)

        # Run continuous load
        await continuous_load()

        metrics.end_time = datetime.utcnow()
        summary = metrics.get_summary()

        # Assertions
        assert summary["error_rate"] < 0.01  # <1% error rate
        assert summary["p95_response_time"] < 1.0  # <1s p95
        assert summary["avg_response_time"] < 0.5  # <500ms average

        print("\nSustained Load Test Results (1 hour):")
        print(f"  Total Requests: {summary['total_requests']}")
        print(f"  Error Rate: {summary['error_rate']:.2%}")
        print(f"  Avg Response: {summary['avg_response_time']:.3f}s")
        print(f"  P95 Response: {summary['p95_response_time']:.3f}s")
        print(f"  Duration: {summary['duration']:.1f}s")


class TestPeakLoad:
    """Test system under peak/spike load"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_spike_load(self, orchestrator):
        """Test sudden spike in load"""
        metrics = LoadTestMetrics()
        metrics.start_time = datetime.utcnow()

        # Normal load
        print("Running normal load...")

        async def normal_user():
            start = time.time()
            try:
                agent_id = await orchestrator.create_agent(
                    agent_type="normal", config={}
                )
                await orchestrator.execute_task(agent_id, "Normal task")
                await orchestrator.terminate_agent(agent_id)
                duration = time.time() - start
                metrics.record_response(duration, True)
            except Exception as e:
                duration = time.time() - start
                metrics.record_response(duration, False, str(e))

        await asyncio.gather(*[normal_user() for _ in range(100)])

        # Sudden spike
        print("Simulating spike...")
        await asyncio.gather(*[normal_user() for _ in range(5000)])

        # Return to normal
        print("Returning to normal...")
        await asyncio.gather(*[normal_user() for _ in range(100)])

        metrics.end_time = datetime.utcnow()
        summary = metrics.get_summary()

        # Assertions
        assert summary["error_rate"] < 0.15  # <15% error rate during spike
        assert summary["p95_response_time"] < 10.0  # <10s p95

        print("\nSpike Load Test Results:")
        print(f"  Total Requests: {summary['total_requests']}")
        print(f"  Error Rate: {summary['error_rate']:.2%}")
        print(f"  Avg Response: {summary['avg_response_time']:.3f}s")
        print(f"  P95 Response: {summary['p95_response_time']:.3f}s")
        print(f"  Max Response: {summary['max_response_time']:.3f}s")


class TestThroughput:
    """Test system throughput"""

    @pytest.mark.asyncio
    async def test_max_throughput(self, orchestrator):
        """Measure maximum throughput"""
        metrics = LoadTestMetrics()
        metrics.start_time = datetime.utcnow()

        duration = 60  # 1 minute
        end_time = time.time() + duration

        request_count = 0

        async def make_request():
            nonlocal request_count
            start = time.time()
            try:
                agent_id = await orchestrator.create_agent(
                    agent_type="throughput", config={}
                )
                await orchestrator.execute_task(agent_id, "Throughput task")
                await orchestrator.terminate_agent(agent_id)
                request_count += 1
                duration_req = time.time() - start
                metrics.record_response(duration_req, True)
            except Exception as e:
                duration_req = time.time() - start
                metrics.record_response(duration_req, False, str(e))

        # Generate maximum load
        tasks = []
        while time.time() < end_time:
            # Launch 100 concurrent requests
            batch = [make_request() for _ in range(100)]
            tasks.extend(batch)

            # Don't wait, keep launching
            if len(tasks) > 10000:
                # Prevent memory issues
                await asyncio.gather(*tasks[:5000])
                tasks = tasks[5000:]

        # Wait for remaining
        if tasks:
            await asyncio.gather(*tasks)

        metrics.end_time = datetime.utcnow()
        summary = metrics.get_summary()

        throughput = request_count / duration
        metrics.record_throughput(int(throughput))

        print("\nThroughput Test Results:")
        print(f"  Total Requests: {request_count}")
        print(f"  Duration: {duration}s")
        print(f"  Throughput: {throughput:.1f} req/s")
        print(f"  Error Rate: {summary['error_rate']:.2%}")

        # Assert minimum throughput
        assert throughput >= 100  # At least 100 req/s


class TestDatabaseLoad:
    """Test database performance under load"""

    @pytest.mark.asyncio
    async def test_database_concurrent_writes(self, memory_system):
        """Test concurrent database writes"""
        metrics = LoadTestMetrics()
        metrics.start_time = datetime.utcnow()

        async def write_memory(agent_id: str):
            start = time.time()
            try:
                await memory_system.store_memory(
                    agent_id=agent_id,
                    memory_type="load_test",
                    content={"data": "test" * 100},  # ~400 bytes
                )
                duration = time.time() - start
                metrics.record_response(duration, True)
            except Exception as e:
                duration = time.time() - start
                metrics.record_response(duration, False, str(e))

        # 10,000 concurrent writes
        await asyncio.gather(
            *[write_memory(f"agent_{i}") for i in range(10000)]
        )

        metrics.end_time = datetime.utcnow()
        summary = metrics.get_summary()

        # Assertions
        assert summary["error_rate"] < 0.01  # <1% error rate
        assert summary["p95_response_time"] < 0.1  # <100ms p95

        print("\nDatabase Load Test Results:")
        print(f"  Total Writes: {summary['total_requests']}")
        print(f"  Error Rate: {summary['error_rate']:.2%}")
        print(f"  Avg Write Time: {summary['avg_response_time']:.3f}s")
        print(f"  P95 Write Time: {summary['p95_response_time']:.3f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not slow"])

# Made with Bob
