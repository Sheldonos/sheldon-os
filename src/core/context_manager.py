"""
Sheldon OS Context Management System

Manages context handoffs across different time intervals:
- Hourly: Immediate operational context
- Daily: Day-to-day progress and decisions
- Weekly: Strategic progress and adjustments
- Monthly: Performance reviews and planning
- Semi-annually: Major milestones and pivots
- Annually: Long-term vision and achievements

Ensures continuous progression and knowledge preservation across
agent lifecycles.
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class ContextInterval(Enum):
    """Context handoff intervals"""

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    SEMI_ANNUALLY = "semi_annually"
    ANNUALLY = "annually"


class ContextPriority(Enum):
    """Context priority levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass  # pylint: disable=too-many-instance-attributes
class ContextSnapshot:
    """A snapshot of system context at a point in time"""

    id: str
    interval: ContextInterval
    timestamp: datetime
    priority: ContextPriority

    # Core context data
    system_state: Dict[str, Any]
    active_agents: List[Dict[str, Any]]
    completed_tasks: List[Dict[str, Any]]
    pending_tasks: List[Dict[str, Any]]
    decisions_made: List[Dict[str, Any]]

    # Performance metrics
    metrics: Dict[str, Any]

    # Insights and learnings
    insights: List[str]
    patterns_identified: List[str]
    recommendations: List[str]

    # Issues and blockers
    issues: List[Dict[str, Any]]
    blockers: List[Dict[str, Any]]

    # Goals and progress
    goals: List[Dict[str, Any]]
    progress: Dict[str, float]

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "interval": self.interval.value,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.value,
            "system_state": self.system_state,
            "active_agents": self.active_agents,
            "completed_tasks": self.completed_tasks,
            "pending_tasks": self.pending_tasks,
            "decisions_made": self.decisions_made,
            "metrics": self.metrics,
            "insights": self.insights,
            "patterns_identified": self.patterns_identified,
            "recommendations": self.recommendations,
            "issues": self.issues,
            "blockers": self.blockers,
            "goals": self.goals,
            "progress": self.progress,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextSnapshot":
        """Create from dictionary"""
        return cls(
            id=data["id"],
            interval=ContextInterval(data["interval"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            priority=ContextPriority(data["priority"]),
            system_state=data["system_state"],
            active_agents=data["active_agents"],
            completed_tasks=data["completed_tasks"],
            pending_tasks=data["pending_tasks"],
            decisions_made=data["decisions_made"],
            metrics=data["metrics"],
            insights=data["insights"],
            patterns_identified=data["patterns_identified"],
            recommendations=data["recommendations"],
            issues=data["issues"],
            blockers=data["blockers"],
            goals=data["goals"],
            progress=data["progress"],
            metadata=data.get("metadata", {}),
        )


@dataclass  # pylint: disable=too-many-instance-attributes
class ContextHandoff:
    """Context handoff between agents or time periods"""

    id: str
    from_agent: Optional[str]
    to_agent: Optional[str]
    timestamp: datetime
    context: Dict[str, Any]
    instructions: List[str]
    priority: ContextPriority
    acknowledged: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "instructions": self.instructions,
            "priority": self.priority.value,
            "acknowledged": self.acknowledged,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextHandoff":
        """Create from dictionary"""
        return cls(
            id=data["id"],
            from_agent=data.get("from_agent"),
            to_agent=data.get("to_agent"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            context=data["context"],
            instructions=data["instructions"],
            priority=ContextPriority(data["priority"]),
            acknowledged=data.get("acknowledged", False),
        )


class ContextManager:  # pylint: disable=too-many-instance-attributes
    """Manages system context and handoffs

    Responsibilities:
    - Create periodic context snapshots
    - Manage context handoffs between agents
    - Preserve state across system restarts
    - Generate context summaries for different intervals
    - Track progress and decisions over time
    """

    def __init__(
        self,
        storage_path: Optional[Path] = None,
        enable_auto_snapshots: bool = True,
        config: Optional[Any] = None,
    ):
        """Initialize context manager

        Args:
            storage_path: Path to store context snapshots
            enable_auto_snapshots: Enable automatic periodic snapshots
        """
        self.config = config
        self.storage_path = storage_path or Path("data/context")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.enable_auto_snapshots = enable_auto_snapshots

        # Context stores
        self.snapshots: Dict[str, ContextSnapshot] = {}
        self.handoffs: Dict[str, ContextHandoff] = {}

        # Current context
        self.current_context: Dict[str, Any] = {
            "system_state": {},
            "active_agents": [],
            "tasks": [],
            "decisions": [],
            "metrics": {},
        }

        # Snapshot schedules
        self.last_snapshots: Dict[ContextInterval, datetime] = {}

        # Callbacks for context updates
        self.update_callbacks: List[Callable] = []

        # Background tasks
        self._snapshot_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Start context manager"""
        self._running = True

        # Load existing snapshots
        await self._load_snapshots()

        # Start automatic snapshot task
        if self.enable_auto_snapshots:
            self._snapshot_task = asyncio.create_task(self._snapshot_loop())

    async def stop(self):
        """Stop context manager"""
        self._running = False

        # Save current state
        await self.create_snapshot(
            ContextInterval.HOURLY,
            ContextPriority.HIGH,
        )

        # Cancel background tasks
        if self._snapshot_task:
            self._snapshot_task.cancel()
            try:
                await self._snapshot_task
            except asyncio.CancelledError:
                pass

    async def update_context(
        self,
        key: str,
        value: Any,
        notify: bool = True,
    ):
        """Update current context

        Args:
            key: Context key
            value: Context value
            notify: Whether to notify callbacks
        """
        self.current_context[key] = value

        if notify:
            await self._notify_callbacks(key, value)

    async def get_context(self, key: Optional[str] = None) -> Any:
        """Get current context

        Args:
            key: Specific context key (None for all)

        Returns:
            Context value or full context
        """
        if key is None:
            return self.current_context
        return self.current_context.get(key)

    async def create_snapshot(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
        self,
        interval: Optional[ContextInterval] = None,
        priority: ContextPriority = ContextPriority.MEDIUM,
        force: bool = False,
        agent_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        snapshot_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        include_memory: bool = False,
    ) -> Any:
        """Create a context snapshot.

        Supports both the native interval-based API and the integration-test
        compatibility API that passes agent_id/context/snapshot_type.
        """
        if (
            agent_id is not None
            or context is not None
            or snapshot_type is not None
        ):
            snapshot_interval = interval or ContextInterval.HOURLY
            snapshot_id = (
                f"{snapshot_type or 'snapshot'}_"
                f"{datetime.utcnow().isoformat()}"
            )
            snapshot_metadata = dict(metadata or {})
            snapshot_metadata["agent_id"] = agent_id
            snapshot_metadata["snapshot_type"] = snapshot_type or "manual"

            if include_memory:
                memory_state = {}
                if context and isinstance(context, dict):
                    memory_state["working"] = [context]
                snapshot_metadata["memory_state"] = memory_state

            snapshot_context = context or {}
            snapshot = ContextSnapshot(
                id=snapshot_id,
                interval=snapshot_interval,
                timestamp=datetime.utcnow(),
                priority=priority,
                system_state=snapshot_context,
                active_agents=[],
                completed_tasks=[],
                pending_tasks=[],
                decisions_made=[],
                metrics={},
                insights=[],
                patterns_identified=[],
                recommendations=[],
                issues=[],
                blockers=[],
                goals=[],
                progress={},
                metadata=snapshot_metadata,
            )

            self.snapshots[snapshot_id] = snapshot
            self.last_snapshots[snapshot_interval] = datetime.utcnow()
            await self._save_snapshot(snapshot)
            return snapshot_id

        if interval is None:
            interval = ContextInterval.HOURLY

        # Check if snapshot is due
        if not force:
            last_snapshot = self.last_snapshots.get(interval)
            if last_snapshot:
                time_since = datetime.utcnow() - last_snapshot
                if not self._is_snapshot_due(interval, time_since):
                    return None

        # Generate snapshot ID
        snapshot_id = f"{interval.value}_{datetime.utcnow().isoformat()}"

        # Collect context data
        snapshot = ContextSnapshot(
            id=snapshot_id,
            interval=interval,
            timestamp=datetime.utcnow(),
            priority=priority,
            system_state=self.current_context.get("system_state", {}),
            active_agents=self.current_context.get("active_agents", []),
            completed_tasks=self._get_completed_tasks(interval),
            pending_tasks=self._get_pending_tasks(),
            decisions_made=self._get_decisions(interval),
            metrics=self.current_context.get("metrics", {}),
            insights=self._generate_insights(interval),
            patterns_identified=self._identify_patterns(interval),
            recommendations=self._generate_recommendations(interval),
            issues=self._get_issues(),
            blockers=self._get_blockers(),
            goals=self._get_goals(),
            progress=self._calculate_progress(),
        )

        # Store snapshot
        self.snapshots[snapshot_id] = snapshot
        self.last_snapshots[interval] = datetime.utcnow()

        # Persist to disk
        await self._save_snapshot(snapshot)

        return snapshot

    async def create_handoff(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        from_agent: Optional[str],
        to_agent: Optional[str],
        context: Dict[str, Any],
        instructions: List[str],
        priority: ContextPriority = ContextPriority.MEDIUM,
    ) -> str:
        """Create a context handoff

        Args:
            from_agent: Source agent ID
            to_agent: Target agent ID
            context: Context to hand off
            instructions: Instructions for recipient
            priority: Handoff priority

        Returns:
            Handoff ID
        """
        handoff_id = f"handoff_{datetime.utcnow().isoformat()}"

        handoff = ContextHandoff(
            id=handoff_id,
            from_agent=from_agent,
            to_agent=to_agent,
            timestamp=datetime.utcnow(),
            context=context,
            instructions=instructions,
            priority=priority,
        )

        self.handoffs[handoff_id] = handoff

        # Persist to disk
        await self._save_handoff(handoff)

        return handoff_id

    async def acknowledge_handoff(self, handoff_id: str) -> bool:
        """Acknowledge receipt of a handoff

        Args:
            handoff_id: Handoff ID

        Returns:
            True if acknowledged, False if not found
        """
        handoff = self.handoffs.get(handoff_id)
        if handoff:
            handoff.acknowledged = True
            await self._save_handoff(handoff)
            return True
        return False

    async def get_handoffs(
        self,
        agent_id: Optional[str] = None,
        acknowledged: Optional[bool] = None,
    ) -> List[ContextHandoff]:
        """Get handoffs

        Args:
            agent_id: Filter by agent ID (to_agent)
            acknowledged: Filter by acknowledgment status

        Returns:
            List of handoffs
        """
        handoffs = list(self.handoffs.values())

        if agent_id is not None:
            handoffs = [h for h in handoffs if h.to_agent == agent_id]

        if acknowledged is not None:
            handoffs = [h for h in handoffs if h.acknowledged == acknowledged]

        return handoffs

    async def get_snapshot(
        self,
        snapshot_id: Optional[str] = None,
        interval: Optional[ContextInterval] = None,
    ) -> Optional[Any]:
        """Get a snapshot

        Args:
            snapshot_id: Specific snapshot ID
            interval: Get latest snapshot for interval

        Returns:
            Snapshot or None
        """
        if snapshot_id:
            snapshot = self.snapshots.get(snapshot_id)
            if snapshot is None:
                return None
            snapshot_dict = snapshot.to_dict()
            snapshot_dict.update(snapshot.system_state)
            if "memory_state" in snapshot.metadata:
                snapshot_dict["memory_state"] = (
                    snapshot.metadata["memory_state"]
                )
            if "trigger" in snapshot.metadata:
                snapshot_dict["trigger"] = snapshot.metadata["trigger"]
            return snapshot_dict

        if interval:
            # Get latest snapshot for interval
            interval_snapshots = [
                s for s in self.snapshots.values() if s.interval == interval
            ]
            if interval_snapshots:
                return max(interval_snapshots, key=lambda s: s.timestamp)

        return None

    async def get_context_summary(
        self,
        interval: ContextInterval,
        include_history: bool = True,
    ) -> Dict[str, Any]:
        """Get a context summary for an interval

        Args:
            interval: Time interval
            include_history: Include historical snapshots

        Returns:
            Context summary
        """
        summary: Dict[str, Any] = {
            "interval": interval.value,
            "timestamp": datetime.utcnow().isoformat(),
            "current_context": self.current_context,
        }

        if include_history:
            # Get recent snapshots for this interval
            interval_snapshots = [
                s for s in self.snapshots.values() if s.interval == interval
            ]
            interval_snapshots.sort(key=lambda s: s.timestamp, reverse=True)

            recent_snapshots: List[Dict[str, Any]] = [
                s.to_dict() for s in interval_snapshots[:5]
            ]
            summary["recent_snapshots"] = recent_snapshots

        return summary

    async def get_snapshots(
        self,
        agent_id: Optional[str] = None,
        snapshot_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get snapshots for an agent

        Args:
            agent_id: Filter by agent ID (from metadata)
            snapshot_type: Filter by snapshot type (from metadata)

        Returns:
            List of matching snapshots
        """
        snapshots = list(self.snapshots.values())

        if agent_id is not None:
            snapshots = [
                s
                for s in snapshots
                if s.metadata.get("agent_id") == agent_id
            ]

        if snapshot_type is not None:
            snapshots = [
                s
                for s in snapshots
                if s.metadata.get("snapshot_type") == snapshot_type
            ]

        # Sort by timestamp descending
        snapshots.sort(key=lambda s: s.timestamp, reverse=True)

        normalized_snapshots: List[Dict[str, Any]] = []
        for snapshot in snapshots:
            snapshot_dict = snapshot.to_dict()
            snapshot_dict.update(snapshot.system_state)
            if "memory_state" in snapshot.metadata:
                snapshot_dict["memory_state"] = (
                    snapshot.metadata["memory_state"]
                )
            if "trigger" in snapshot.metadata:
                snapshot_dict["trigger"] = snapshot.metadata["trigger"]
            normalized_snapshots.append(snapshot_dict)

        return normalized_snapshots

    async def create_handoff_snapshot(
        self,
        from_agent: str,
        to_agent: str,
        context: Dict[str, Any],
    ) -> str:
        """Create a handoff with snapshot

        Args:
            from_agent: Source agent ID
            to_agent: Target agent ID
            context: Context to hand off

        Returns:
            Handoff ID
        """
        # Extract instructions from context or use default
        instructions = context.get(
            "instructions",
            [f"Context handoff from {from_agent} to {to_agent}"],
        )

        # Create the handoff
        handoff_id = await self.create_handoff(
            from_agent=from_agent,
            to_agent=to_agent,
            context=context,
            instructions=instructions,
            priority=ContextPriority.HIGH,
        )

        return handoff_id

    async def initialize(self):
        """Initialize context manager (async)"""
        await self.start()

    async def cleanup(self):
        """Cleanup context manager (async)"""
        await self.stop()

    def register_callback(self, callback: Callable):
        """Register a callback for context updates

        Args:
            callback: Async callback function
        """
        self.update_callbacks.append(callback)

    def _is_snapshot_due(
        self, interval: ContextInterval, time_since: timedelta
    ) -> bool:
        """Check if a snapshot is due"""
        intervals = {
            ContextInterval.HOURLY: timedelta(hours=1),
            ContextInterval.DAILY: timedelta(days=1),
            ContextInterval.WEEKLY: timedelta(weeks=1),
            ContextInterval.MONTHLY: timedelta(days=30),
            ContextInterval.SEMI_ANNUALLY: timedelta(days=182),
            ContextInterval.ANNUALLY: timedelta(days=365),
        }

        return time_since >= intervals.get(interval, timedelta(hours=1))

    def _get_completed_tasks(
        self,
        interval: ContextInterval,
    ) -> List[Dict[str, Any]]:
        """Get completed tasks for interval"""
        _ = interval
        completed_tasks = self.current_context.get("completed_tasks", [])
        return completed_tasks if isinstance(completed_tasks, list) else []

    def _get_pending_tasks(self) -> List[Dict[str, Any]]:
        """Get pending tasks"""
        pending_tasks = self.current_context.get("pending_tasks", [])
        return pending_tasks if isinstance(pending_tasks, list) else []

    def _get_decisions(
        self,
        interval: ContextInterval,
    ) -> List[Dict[str, Any]]:
        """Get decisions made in interval"""
        _ = interval
        decisions = self.current_context.get("decisions", [])
        return decisions if isinstance(decisions, list) else []

    def _get_issues(self) -> List[Dict[str, Any]]:
        """Get current issues"""
        issues = self.current_context.get("issues", [])
        return issues if isinstance(issues, list) else []

    def _get_blockers(self) -> List[Dict[str, Any]]:
        """Get current blockers"""
        blockers = self.current_context.get("blockers", [])
        return blockers if isinstance(blockers, list) else []

    def _get_goals(self) -> List[Dict[str, Any]]:
        """Get current goals"""
        goals = self.current_context.get("goals", [])
        return goals if isinstance(goals, list) else []

    def _calculate_progress(self) -> Dict[str, float]:
        """Calculate progress on goals"""
        goals = self._get_goals()
        if not goals:
            return {}

        progress: Dict[str, float] = {}
        for goal in goals:
            goal_id = str(goal.get("id", goal.get("name", "unknown")))
            raw_progress = goal.get("progress", 0.0)
            try:
                progress[goal_id] = max(0.0, min(1.0, float(raw_progress)))
            except (TypeError, ValueError):
                progress[goal_id] = 0.0

        return progress

    def _generate_insights(self, interval: ContextInterval) -> List[str]:
        """Generate insights for interval"""
        insights: List[str] = []
        active_agents = self.current_context.get("active_agents", [])
        if isinstance(active_agents, list) and active_agents:
            insights.append(
                f"{len(active_agents)} active agents tracked for {interval.value}"
            )

        progress = self._calculate_progress()
        if progress:
            avg_progress = sum(progress.values()) / len(progress)
            insights.append(
                f"Average goal progress is {avg_progress:.0%} for {interval.value}"
            )

        return insights

    def _identify_patterns(self, interval: ContextInterval) -> List[str]:
        """Identify patterns in interval"""
        patterns: List[str] = []
        decisions = self._get_decisions(interval)
        if len(decisions) >= 3:
            patterns.append(
                f"Decision volume is elevated for the {interval.value} interval"
            )

        blockers = self._get_blockers()
        if blockers:
            patterns.append(f"{len(blockers)} blockers currently require attention")

        return patterns

    def _generate_recommendations(
        self,
        interval: ContextInterval,
    ) -> List[str]:
        """Generate recommendations for interval"""
        recommendations: List[str] = []
        if self._get_blockers():
            recommendations.append("Prioritize blocker resolution before new work")

        pending_tasks = self._get_pending_tasks()
        if len(pending_tasks) > 10:
            recommendations.append(
                f"Reduce pending task backlog during the {interval.value} cycle"
            )

        if not recommendations:
            recommendations.append("Maintain current execution cadence")

        return recommendations

    async def _notify_callbacks(self, key: str, value: Any):
        """Notify registered callbacks of context update"""
        for callback in self.update_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(key, value)
                else:
                    callback(key, value)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                print(f"Error in context callback: {exc}")

    async def _snapshot_loop(self):
        """Background task for periodic snapshots"""
        while self._running:
            try:
                # Check each interval
                for interval in ContextInterval:
                    await self.create_snapshot(interval)

                # Sleep for 1 minute before next check
                await asyncio.sleep(60)

            except asyncio.CancelledError:
                break
            except Exception as exc:  # pylint: disable=broad-exception-caught
                print(f"Error in snapshot loop: {exc}")
                await asyncio.sleep(60)

    async def _save_snapshot(self, snapshot: ContextSnapshot):
        """Save snapshot to disk"""
        try:
            interval_dir = self.storage_path / snapshot.interval.value
            interval_dir.mkdir(parents=True, exist_ok=True)

            file_path = interval_dir / f"{snapshot.id}.json"

            with open(file_path, "w", encoding="utf-8") as file_handle:
                json.dump(snapshot.to_dict(), file_handle, indent=2)

        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(f"Error saving snapshot: {exc}")

    async def _save_handoff(self, handoff: ContextHandoff):
        """Save handoff to disk"""
        try:
            handoff_dir = self.storage_path / "handoffs"
            handoff_dir.mkdir(parents=True, exist_ok=True)

            file_path = handoff_dir / f"{handoff.id}.json"

            with open(file_path, "w", encoding="utf-8") as file_handle:
                json.dump(handoff.to_dict(), file_handle, indent=2)

        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(f"Error saving handoff: {exc}")

    async def _load_snapshots(self):
        """Load snapshots from disk"""
        try:
            if not self.storage_path.exists():
                return

            # Load snapshots from each interval directory
            for interval in ContextInterval:
                interval_dir = self.storage_path / interval.value
                if not interval_dir.exists():
                    continue

                for file_path in interval_dir.glob("*.json"):
                    try:
                        with open(file_path, "r", encoding="utf-8") as file_handle:
                            data = json.load(file_handle)
                            snapshot = ContextSnapshot.from_dict(data)
                            self.snapshots[snapshot.id] = snapshot
                    except Exception as exc:  # pylint: disable=broad-exception-caught
                        print(f"Error loading snapshot {file_path}: {exc}")

            # Load handoffs
            handoff_dir = self.storage_path / "handoffs"
            if handoff_dir.exists():
                for file_path in handoff_dir.glob("*.json"):
                    try:
                        with open(file_path, "r", encoding="utf-8") as file_handle:
                            data = json.load(file_handle)
                            handoff = ContextHandoff.from_dict(data)
                            self.handoffs[handoff.id] = handoff
                    except Exception as exc:  # pylint: disable=broad-exception-caught
                        print(f"Error loading handoff {file_path}: {exc}")

        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(f"Error loading snapshots: {exc}")


# Made with Bob
