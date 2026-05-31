"""
Core Integration Tests

Tests integration between core components:
- Orchestrator + Memory System
- Orchestrator + Context Manager
- Memory System + Context Manager
- Agent System + Orchestrator
- All core components together
"""

import asyncio
from datetime import datetime

import pytest

from src.core.orchestrator import Orchestrator


class TestOrchestratorMemoryIntegration:
    """Test Orchestrator + Memory System integration"""

    @pytest.mark.asyncio
    async def test_orchestrator_stores_agent_memory(
        self, orchestrator, memory_system
    ):
        """Test orchestrator stores agent interactions in memory."""
        # Create agent through orchestrator
        agent_id = await orchestrator.create_agent(
            agent_type="research", config={"name": "test_agent"}
        )

        # Execute task
        result = await orchestrator.execute_task(
            agent_id=agent_id, task="Research AI trends"
        )

        # Verify memory was stored
        memories = await memory_system.retrieve_memories(
            agent_id=agent_id, memory_type="task_execution"
        )

        assert len(memories) > 0
        assert memories[0]["task"] == "Research AI trends"
        assert memories[0]["result"] == result

    @pytest.mark.asyncio
    async def test_orchestrator_retrieves_agent_context(
        self, orchestrator, memory_system
    ):
        """Test that orchestrator retrieves relevant context from memory"""
        agent_id = "test_agent_123"

        # Store some memories
        await memory_system.store_memory(
            agent_id=agent_id,
            memory_type="conversation",
            content={"message": "Previous interaction"},
            metadata={"timestamp": datetime.utcnow().isoformat()},
        )

        # Orchestrator should retrieve this context
        context = await orchestrator.get_agent_context(agent_id)

        assert "conversation" in context
        assert len(context["conversation"]) > 0

    @pytest.mark.asyncio
    async def test_memory_persistence_across_orchestrator_restarts(
        self, orchestrator, memory_system
    ):
        """Test that memory persists when orchestrator restarts"""
        agent_id = "persistent_agent"

        # Store memory
        await memory_system.store_memory(
            agent_id=agent_id,
            memory_type="long_term",
            content={"knowledge": "Important fact"},
            metadata={"importance": 0.9},
        )

        # Simulate orchestrator restart
        new_orchestrator = Orchestrator(memory_system=memory_system)

        # Retrieve memory through new orchestrator
        context = await new_orchestrator.get_agent_context(agent_id)

        assert "long_term" in context
        assert context["long_term"][0]["knowledge"] == "Important fact"


class TestOrchestratorContextIntegration:
    """Test Orchestrator + Context Manager integration"""

    @pytest.mark.asyncio
    async def test_orchestrator_creates_context_snapshots(
        self, orchestrator, context_manager
    ):
        """Test that orchestrator creates context snapshots at key points"""
        agent_id = await orchestrator.create_agent(
            agent_type="business", config={"name": "business_agent"}
        )

        # Execute multiple tasks
        for i in range(3):
            await orchestrator.execute_task(
                agent_id=agent_id,
                task=f"Task {i}",
            )

        # Verify snapshots were created
        snapshots = await context_manager.get_snapshots(agent_id)

        assert len(snapshots) >= 3
        assert all("task" in s for s in snapshots)

    @pytest.mark.asyncio
    async def test_orchestrator_restores_from_snapshot(
        self, orchestrator, context_manager
    ):
        """Test that orchestrator can restore agent state from snapshot"""
        agent_id = "snapshot_agent"

        # Create snapshot
        snapshot_id = await context_manager.create_snapshot(
            agent_id=agent_id,
            context={
                "state": "active",
                "progress": 0.5,
                "data": {"key": "value"},
            },
        )

        # Restore through orchestrator
        restored_context = await orchestrator.restore_agent_state(
            agent_id=agent_id, snapshot_id=snapshot_id
        )

        assert restored_context["state"] == "active"
        assert restored_context["progress"] == 0.5
        assert restored_context["data"]["key"] == "value"

    @pytest.mark.asyncio
    async def test_context_handoff_between_agents(
        self, orchestrator, context_manager
    ):
        """Test context handoff when orchestrator delegates between agents"""
        # Create two agents
        agent1_id = await orchestrator.create_agent(
            agent_type="research", config={"name": "researcher"}
        )
        agent2_id = await orchestrator.create_agent(
            agent_type="analysis", config={"name": "analyzer"}
        )

        # Agent 1 completes task
        result1 = await orchestrator.execute_task(
            agent_id=agent1_id, task="Research topic"
        )

        # Create handoff snapshot
        snapshot_id = await context_manager.create_handoff_snapshot(
            from_agent=agent1_id,
            to_agent=agent2_id,
            context={"research_results": result1},
        )

        # Agent 2 receives context
        context = await orchestrator.get_handoff_context(
            agent_id=agent2_id, snapshot_id=snapshot_id
        )

        assert "research_results" in context
        assert context["research_results"] == result1


class TestMemoryContextIntegration:
    """Test Memory System + Context Manager integration"""

    @pytest.mark.asyncio
    async def test_context_snapshots_include_memory_state(
        self, memory_system, context_manager
    ):
        """Test that context snapshots include relevant memory state"""
        agent_id = "memory_context_agent"

        # Store memories
        await memory_system.store_memory(
            agent_id=agent_id,
            memory_type="working",
            content={"current_task": "Analysis"},
        )

        # Create snapshot
        snapshot_id = await context_manager.create_snapshot(
            agent_id=agent_id,
            context={"state": "processing"},
            include_memory=True,
        )

        # Retrieve snapshot
        snapshot = await context_manager.get_snapshot(snapshot_id)

        assert "memory_state" in snapshot
        assert "working" in snapshot["memory_state"]

    @pytest.mark.asyncio
    async def test_memory_consolidation_triggers_snapshot(
        self, memory_system, context_manager
    ):
        """Test that memory consolidation triggers context snapshot"""
        agent_id = "consolidation_agent"

        # Store multiple memories
        for i in range(10):
            await memory_system.store_memory(
                agent_id=agent_id,
                memory_type="short_term",
                content={"item": i},
            )

        # Trigger consolidation
        await memory_system.consolidate_memories(agent_id)

        # Verify snapshot was created
        snapshots = await context_manager.get_snapshots(
            agent_id=agent_id, snapshot_type="consolidation"
        )

        assert len(snapshots) > 0
        assert snapshots[-1]["trigger"] == "memory_consolidation"


class TestAgentSystemIntegration:
    """Test Agent System + Orchestrator integration"""

    @pytest.mark.asyncio
    async def test_agent_lifecycle_through_orchestrator(
        self, orchestrator, lifecycle_manager
    ):
        """Test complete agent lifecycle managed by orchestrator"""
        # Create agent
        agent_id = await orchestrator.create_agent(
            agent_type="business", config={"name": "lifecycle_test"}
        )

        # Verify agent is active
        status = await lifecycle_manager.get_agent_status(agent_id)
        assert status == "active"

        # Pause agent
        await orchestrator.pause_agent(agent_id)
        status = await lifecycle_manager.get_agent_status(agent_id)
        assert status == "paused"

        # Resume agent
        await orchestrator.resume_agent(agent_id)
        status = await lifecycle_manager.get_agent_status(agent_id)
        assert status == "active"

        # Terminate agent
        await orchestrator.terminate_agent(agent_id)
        status = await lifecycle_manager.get_agent_status(agent_id)
        assert status == "terminated"

    @pytest.mark.asyncio
    async def test_multi_agent_coordination(self, orchestrator):
        """Test orchestrator coordinating multiple agents"""
        # Create multiple agents
        agent_ids = []
        for i in range(3):
            agent_id = await orchestrator.create_agent(
                agent_type="worker", config={"name": f"worker_{i}"}
            )
            agent_ids.append(agent_id)

        # Execute parallel tasks
        tasks = [
            orchestrator.execute_task(agent_id, f"Task {i}")
            for i, agent_id in enumerate(agent_ids)
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        assert all(r is not None for r in results)

    @pytest.mark.asyncio
    async def test_agent_failure_recovery(
        self, orchestrator, lifecycle_manager
    ):
        """Test orchestrator handles agent failures gracefully"""
        agent_id = await orchestrator.create_agent(
            agent_type="unstable", config={"name": "failure_test"}
        )

        # Simulate agent failure
        await lifecycle_manager.mark_agent_failed(
            agent_id=agent_id, error="Simulated failure"
        )

        # Orchestrator should detect and recover
        await orchestrator.check_agent_health(agent_id)

        # Verify recovery attempt
        status = await lifecycle_manager.get_agent_status(agent_id)
        assert status in ["recovering", "active"]


class TestFullCoreIntegration:
    """Test all core components working together"""

    @pytest.mark.asyncio
    async def test_complete_task_execution_flow(
        self, orchestrator, memory_system, context_manager, lifecycle_manager
    ):
        """Test complete flow: create agent -> execute task -> store results"""
        # Create agent
        agent_id = await orchestrator.create_agent(
            agent_type="research", config={"name": "integration_test"}
        )

        # Execute task
        task = "Analyze market trends"
        result = await orchestrator.execute_task(agent_id, task)

        # Verify all systems updated
        # 1. Memory system has task record
        memories = await memory_system.retrieve_memories(
            agent_id=agent_id, memory_type="task_execution"
        )
        assert len(memories) > 0

        # 2. Context manager has snapshot
        snapshots = await context_manager.get_snapshots(agent_id)
        assert len(snapshots) > 0

        # 3. Lifecycle manager tracks agent
        status = await lifecycle_manager.get_agent_status(agent_id)
        assert status == "active"

        # 4. Result is valid
        assert result is not None

    @pytest.mark.asyncio
    async def test_long_running_agent_with_checkpoints(
        self, orchestrator, memory_system, context_manager
    ):
        """Test long-running agent with periodic checkpoints"""
        agent_id = await orchestrator.create_agent(
            agent_type="long_running",
            config={"name": "checkpoint_test", "checkpoint_interval": 5},
        )

        # Simulate long-running task
        await orchestrator.start_long_task(
            agent_id=agent_id, task="Long analysis"
        )

        # Wait for checkpoints
        await asyncio.sleep(15)

        # Verify checkpoints created
        snapshots = await context_manager.get_snapshots(
            agent_id=agent_id, snapshot_type="checkpoint"
        )

        assert len(snapshots) >= 2  # At least 2 checkpoints in 15 seconds

        # Verify memory updated
        memories = await memory_system.retrieve_memories(
            agent_id=agent_id, memory_type="progress"
        )
        assert len(memories) > 0

    @pytest.mark.asyncio
    async def test_system_recovery_from_crash(
        self, orchestrator, memory_system, context_manager, lifecycle_manager
    ):
        """Test system can recover from crash using stored state"""
        agent_id = "crash_recovery_agent"

        # Create agent and execute task
        agent_id = await orchestrator.create_agent(
            agent_type="resilient", config={"name": "crash_test"}
        )

        # Start task
        task_id = await orchestrator.start_long_task(
            agent_id=agent_id, task="Critical task"
        )

        # Create checkpoint
        snapshot_id = await context_manager.create_snapshot(
            agent_id=agent_id, context={"task_id": task_id, "progress": 0.5}
        )

        # Simulate crash - create new orchestrator
        new_orchestrator = Orchestrator(
            memory_system=memory_system,
            context_manager=context_manager,
            lifecycle_manager=lifecycle_manager,
        )

        # Recover agent state
        recovered = await new_orchestrator.recover_agent(
            agent_id=agent_id, snapshot_id=snapshot_id
        )

        assert recovered is True

        # Verify agent can continue
        status = await lifecycle_manager.get_agent_status(agent_id)
        assert status in ["active", "recovering"]

    @pytest.mark.asyncio
    async def test_concurrent_agent_operations(
        self, orchestrator, memory_system, context_manager
    ):
        """Test system handles concurrent operations correctly"""
        # Create multiple agents
        agent_ids = []
        for i in range(5):
            agent_id = await orchestrator.create_agent(
                agent_type="concurrent", config={"name": f"concurrent_{i}"}
            )
            agent_ids.append(agent_id)

        # Execute concurrent operations
        async def agent_workflow(agent_id):
            # Execute task
            result = await orchestrator.execute_task(
                agent_id=agent_id, task="Concurrent task"
            )

            # Store memory
            await memory_system.store_memory(
                agent_id=agent_id,
                memory_type="result",
                content={"result": result},
            )

            # Create snapshot
            await context_manager.create_snapshot(
                agent_id=agent_id, context={"completed": True}
            )

            return result

        # Run all workflows concurrently
        results = await asyncio.gather(
            *[agent_workflow(aid) for aid in agent_ids]
        )

        # Verify all completed successfully
        assert len(results) == 5
        assert all(r is not None for r in results)

        # Verify no data corruption
        for agent_id in agent_ids:
            memories = await memory_system.retrieve_memories(
                agent_id=agent_id, memory_type="result"
            )
            assert len(memories) == 1

            snapshots = await context_manager.get_snapshots(agent_id)
            assert len(snapshots) >= 1


class TestErrorHandlingIntegration:
    """Test error handling across components"""

    @pytest.mark.asyncio
    async def test_memory_failure_doesnt_crash_orchestrator(
        self, orchestrator, memory_system
    ):
        """Test orchestrator continues if memory system fails"""
        agent_id = await orchestrator.create_agent(
            agent_type="resilient", config={"name": "memory_failure_test"}
        )

        # Simulate memory system failure
        memory_system._simulate_failure = True

        # Orchestrator should handle gracefully
        result = await orchestrator.execute_task(
            agent_id=agent_id,
            task="Test task",
            fallback_on_memory_failure=True,
        )

        assert result is not None
        memory_system._simulate_failure = False

    @pytest.mark.asyncio
    async def test_context_snapshot_failure_recovery(
        self, orchestrator, context_manager
    ):
        """Test system recovers from snapshot failures"""
        agent_id = await orchestrator.create_agent(
            agent_type="snapshot_test", config={"name": "snapshot_failure"}
        )

        # Simulate snapshot failure
        context_manager._simulate_failure = True

        # Execute task (should succeed despite snapshot failure)
        result = await orchestrator.execute_task(
            agent_id=agent_id,
            task="Test task",
        )

        assert result is not None
        context_manager._simulate_failure = False

    @pytest.mark.asyncio
    async def test_cascading_failure_prevention(
        self, orchestrator, memory_system, context_manager, lifecycle_manager
    ):
        """Test system prevents cascading failures"""
        # Create multiple agents
        agent_ids = []
        for i in range(3):
            agent_id = await orchestrator.create_agent(
                agent_type="dependent", config={"name": f"dependent_{i}"}
            )
            agent_ids.append(agent_id)

        # Fail one agent
        await lifecycle_manager.mark_agent_failed(
            agent_id=agent_ids[0], error="Simulated failure"
        )

        # Other agents should continue
        for agent_id in agent_ids[1:]:
            status = await lifecycle_manager.get_agent_status(agent_id)
            assert status == "active"

        # System should isolate failure
        health = await orchestrator.get_system_health()
        assert health["failed_agents"] == 1
        assert health["active_agents"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
