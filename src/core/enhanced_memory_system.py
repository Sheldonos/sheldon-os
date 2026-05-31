"""
Enhanced Memory System - Network Effects Engine

Three-Layer Architecture:
1. Universal Layer: Cross-client patterns (10M+ patterns)
2. Vertical Layer: Industry-specific playbooks (50+ industries)
3. Client Identity Layer: Brand/constraints customization

This is the competitive moat that creates network effects:
- More clients → More patterns → Better recommendations → More clients
- Privacy-preserving learning across customer base
- Industry benchmarks and best practices
- Client-specific customization and constraints

Performance Targets:
- Pattern lookup: <10ms
- Similarity search: <50ms
- Learning update: <100ms (async)
- Memory consolidation: <5s (background)
"""

import asyncio
import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

import numpy as np
from pydantic import BaseModel, Field


class MemoryLayer(str, Enum):
    """Memory layer types"""
    UNIVERSAL = "universal"  # Cross-client patterns
    VERTICAL = "vertical"    # Industry-specific
    CLIENT = "client"        # Client-specific


class IndustryVertical(str, Enum):
    """Industry verticals for specialized playbooks"""
    ECOMMERCE = "ecommerce"
    SAAS = "saas"
    CONSULTING = "consulting"
    AGENCY = "agency"
    RETAIL = "retail"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    EDUCATION = "education"
    REAL_ESTATE = "real_estate"
    MANUFACTURING = "manufacturing"


class PatternType(str, Enum):
    """Types of patterns we learn"""
    WORKFLOW = "workflow"
    OPTIMIZATION = "optimization"
    FAILURE = "failure"
    BENCHMARK = "benchmark"
    BEST_PRACTICE = "best_practice"
    CONSTRAINT = "constraint"


@dataclass
class UniversalPattern:
    """Cross-client pattern (anonymized)"""
    pattern_id: UUID
    pattern_type: PatternType
    description: str
    trigger_conditions: Dict[str, Any]
    expected_outcomes: Dict[str, Any]
    success_rate: float
    sample_size: int
    confidence: float
    avg_roi: float
    avg_time_to_result: timedelta
    created_at: datetime
    last_updated: datetime
    observation_count: int
    industry_distribution: Dict[IndustryVertical, int] = field(default_factory=dict)


@dataclass
class VerticalPlaybook:
    """Industry-specific playbook"""
    playbook_id: UUID
    industry: IndustryVertical
    name: str
    description: str
    workflows: List[Dict[str, Any]]
    benchmarks: Dict[str, float]
    best_practices: List[str]
    pitfalls: List[str]
    patterns: List[UUID]
    created_at: datetime
    last_updated: datetime
    usage_count: int


@dataclass
class ClientIdentity:
    """Client-specific customization and constraints"""
    client_id: UUID
    industry: IndustryVertical
    brand_voice: str
    brand_guidelines: Dict[str, Any]
    risk_tolerance: float
    budget_constraints: Dict[str, float]
    approval_thresholds: Dict[str, float]
    preferred_tools: Set[str]
    blocked_tools: Set[str]
    custom_workflows: List[Dict[str, Any]]
    learning_enabled: bool
    share_benchmarks: bool
    historical_roi: float
    successful_patterns: List[UUID]
    failed_patterns: List[UUID]
    created_at: datetime
    last_updated: datetime


class EnhancedMemorySystem:
    """Three-layer memory system with network effects"""
    
    def __init__(self):
        self.universal_patterns: Dict[UUID, UniversalPattern] = {}
        self.pattern_index: Dict[str, List[UUID]] = defaultdict(list)
        self.vertical_playbooks: Dict[IndustryVertical, VerticalPlaybook] = {}
        self.client_identities: Dict[UUID, ClientIdentity] = {}
        self.learning_queue: List[Dict[str, Any]] = []
        self.consolidation_task: Optional[asyncio.Task] = None
        self.query_count = 0
        self.learning_count = 0
        self.consolidation_count = 0
    
    async def start(self):
        """Start background learning and consolidation"""
        self.consolidation_task = asyncio.create_task(
            self._consolidation_loop()
        )
    
    async def stop(self):
        """Stop background tasks"""
        if self.consolidation_task:
            self.consolidation_task.cancel()
            try:
                await self.consolidation_task
            except asyncio.CancelledError:
                pass
    
    async def get_recommendations(
        self,
        client_id: UUID,
        context: Dict[str, Any],
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recommendations using all three layers (Target: <50ms)"""
        start_time = datetime.now()
        
        client = self.client_identities.get(client_id)
        if not client:
            raise ValueError(f"Unknown client: {client_id}")
        
        client_recommendations = await self._query_client_layer(client, context)
        vertical_recommendations = await self._query_vertical_layer(client.industry, context)
        universal_recommendations = await self._query_universal_layer(context)
        
        all_recommendations = (
            client_recommendations +
            vertical_recommendations +
            universal_recommendations
        )
        
        ranked = self._rank_recommendations(all_recommendations, client, context)
        
        self.query_count += 1
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        print(f"Memory query completed in {elapsed:.1f}ms")
        
        return ranked[:max_results]
    
    async def _query_client_layer(
        self,
        client: ClientIdentity,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Query client-specific patterns"""
        recommendations = []
        
        for pattern_id in client.successful_patterns:
            pattern = self.universal_patterns.get(pattern_id)
            if pattern and self._pattern_matches(pattern, context):
                recommendations.append({
                    "source": "client",
                    "pattern": pattern,
                    "confidence": 0.9,
                    "reason": "Previously successful for this client"
                })
        
        for workflow in client.custom_workflows:
            if self._workflow_matches(workflow, context):
                recommendations.append({
                    "source": "client",
                    "workflow": workflow,
                    "confidence": 0.85,
                    "reason": "Custom workflow for this client"
                })
        
        return recommendations
    
    async def _query_vertical_layer(
        self,
        industry: IndustryVertical,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Query industry-specific playbook"""
        recommendations = []
        
        playbook = self.vertical_playbooks.get(industry)
        if not playbook:
            return recommendations
        
        for workflow in playbook.workflows:
            if self._workflow_matches(workflow, context):
                recommendations.append({
                    "source": "vertical",
                    "workflow": workflow,
                    "confidence": 0.75,
                    "reason": f"Best practice for {industry.value} industry"
                })
        
        for pattern_id in playbook.patterns:
            pattern = self.universal_patterns.get(pattern_id)
            if pattern and self._pattern_matches(pattern, context):
                recommendations.append({
                    "source": "vertical",
                    "pattern": pattern,
                    "confidence": 0.7,
                    "reason": f"Common pattern in {industry.value}"
                })
        
        return recommendations
    
    async def _query_universal_layer(
        self,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Query universal cross-client patterns"""
        recommendations = []
        
        for pattern in self.universal_patterns.values():
            if self._pattern_matches(pattern, context):
                confidence = min(
                    pattern.confidence * (pattern.sample_size / 100),
                    0.95
                )
                
                recommendations.append({
                    "source": "universal",
                    "pattern": pattern,
                    "confidence": confidence,
                    "reason": f"Successful for {pattern.sample_size} clients"
                })
        
        return recommendations
    
    def _pattern_matches(
        self,
        pattern: UniversalPattern,
        context: Dict[str, Any]
    ) -> bool:
        """Check if pattern matches current context"""
        for key, value in pattern.trigger_conditions.items():
            if key not in context:
                return False
            
            if isinstance(value, (int, float)):
                ctx_value = context[key]
                if not (value * 0.8 <= ctx_value <= value * 1.2):
                    return False
            elif context[key] != value:
                return False
        
        return True
    
    def _workflow_matches(
        self,
        workflow: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Check if workflow is applicable to context"""
        conditions = workflow.get("conditions", {})
        for key, value in conditions.items():
            if key not in context or context[key] != value:
                return False
        return True
    
    def _rank_recommendations(
        self,
        recommendations: List[Dict[str, Any]],
        client: ClientIdentity,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Rank recommendations by relevance"""
        for rec in recommendations:
            score = rec["confidence"]
            
            if rec["source"] == "client":
                score *= 1.5
            elif rec["source"] == "vertical":
                score *= 1.2
            
            if "pattern" in rec:
                pattern = rec["pattern"]
                if pattern.avg_roi > 2.0:
                    score *= 1.3
            
            if "pattern" in rec:
                pattern = rec["pattern"]
                risk_factor = 1.0 - abs(client.risk_tolerance - 0.5)
                score *= (0.8 + risk_factor * 0.4)
            
            rec["score"] = score
        
        return sorted(recommendations, key=lambda x: x["score"], reverse=True)
    
    async def record_outcome(
        self,
        client_id: UUID,
        action: Dict[str, Any],
        outcome: Dict[str, Any],
        success: bool
    ):
        """Record action outcome for learning"""
        client = self.client_identities.get(client_id)
        if not client or not client.learning_enabled:
            return
        
        self.learning_queue.append({
            "client_id": client_id,
            "industry": client.industry,
            "action": action,
            "outcome": outcome,
            "success": success,
            "timestamp": datetime.now()
        })
        
        self.learning_count += 1
        
        if len(self.learning_queue) >= 100:
            await self._consolidate_learning()
    
    async def _consolidation_loop(self):
        """Background task for learning consolidation"""
        while True:
            try:
                await asyncio.sleep(300)
                await self._consolidate_learning()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Consolidation error: {e}")
    
    async def _consolidate_learning(self):
        """Consolidate learning queue into patterns (Target: <5s for 1000 observations)"""
        if not self.learning_queue:
            return
        
        start_time = datetime.now()
        
        batch = self.learning_queue[:1000]
        self.learning_queue = self.learning_queue[1000:]
        
        groups = self._group_observations(batch)
        
        new_patterns = []
        for group in groups:
            pattern = self._extract_pattern(group)
            if pattern:
                new_patterns.append(pattern)
        
        await self._update_universal_layer(new_patterns)
        await self._update_vertical_layer(batch)
        await self._update_client_layer(batch)
        
        self.consolidation_count += 1
        
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"Consolidated {len(batch)} observations in {elapsed:.1f}s")
    
    def _group_observations(
        self,
        observations: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """Group similar observations"""
        groups = defaultdict(list)
        
        for obs in observations:
            action_type = obs["action"].get("type", "unknown")
            success = obs["success"]
            key = f"{action_type}_{success}"
            groups[key].append(obs)
        
        return list(groups.values())
    
    def _extract_pattern(
        self,
        group: List[Dict[str, Any]]
    ) -> Optional[UniversalPattern]:
        """Extract pattern from observation group"""
        if len(group) < 5:
            return None
        
        success_rate = sum(1 for obs in group if obs["success"]) / len(group)
        
        if success_rate < 0.6:
            return None
        
        trigger_conditions = self._extract_conditions(group)
        expected_outcomes = self._extract_outcomes(group)
        
        rois = [
            obs["outcome"].get("roi", 0.0)
            for obs in group
            if obs["success"]
        ]
        avg_roi = float(np.mean(rois)) if rois else 0.0
        
        pattern = UniversalPattern(
            pattern_id=uuid4(),
            pattern_type=PatternType.WORKFLOW,
            description=f"Pattern from {len(group)} observations",
            trigger_conditions=trigger_conditions,
            expected_outcomes=expected_outcomes,
            success_rate=success_rate,
            sample_size=len(group),
            confidence=min(success_rate * (len(group) / 100), 0.95),
            avg_roi=avg_roi,
            avg_time_to_result=timedelta(days=7),
            created_at=datetime.now(),
            last_updated=datetime.now(),
            observation_count=len(group)
        )
        
        return pattern
    
    def _extract_conditions(
        self,
        group: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract common trigger conditions"""
        conditions = {}
        
        all_keys = set()
        for obs in group:
            all_keys.update(obs["action"].keys())
        
        for key in all_keys:
            values = [
                obs["action"].get(key)
                for obs in group
                if key in obs["action"]
            ]
            
            if len(values) >= len(group) * 0.8:
                if isinstance(values[0], (int, float)):
                    conditions[key] = float(np.mean(values))
                else:
                    conditions[key] = max(set(values), key=values.count)
        
        return conditions
    
    def _extract_outcomes(
        self,
        group: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract expected outcomes"""
        outcomes = {}
        
        all_keys = set()
        for obs in group:
            if obs["success"]:
                all_keys.update(obs["outcome"].keys())
        
        for key in all_keys:
            values = [
                obs["outcome"].get(key)
                for obs in group
                if obs["success"] and key in obs["outcome"]
            ]
            
            if values and isinstance(values[0], (int, float)):
                outcomes[key] = float(np.mean(values))
        
        return outcomes
    
    async def _update_universal_layer(
        self,
        new_patterns: List[UniversalPattern]
    ):
        """Update universal patterns"""
        for pattern in new_patterns:
            existing = self._find_similar_pattern(pattern)
            
            if existing:
                self._merge_patterns(existing, pattern)
            else:
                self.universal_patterns[pattern.pattern_id] = pattern
                pattern_sig = self._pattern_signature(pattern)
                self.pattern_index[pattern_sig].append(pattern.pattern_id)
    
    async def _update_vertical_layer(
        self,
        observations: List[Dict[str, Any]]
    ):
        """Update industry playbooks"""
        by_industry = defaultdict(list)
        for obs in observations:
            by_industry[obs["industry"]].append(obs)
        
        for industry, obs_list in by_industry.items():
            playbook = self.vertical_playbooks.get(industry)
            if not playbook:
                continue
            
            self._update_benchmarks(playbook, obs_list)
            playbook.usage_count += len(obs_list)
            playbook.last_updated = datetime.now()
    
    async def _update_client_layer(
        self,
        observations: List[Dict[str, Any]]
    ):
        """Update client identities"""
        by_client = defaultdict(list)
        for obs in observations:
            by_client[obs["client_id"]].append(obs)
        
        for client_id, obs_list in by_client.items():
            client = self.client_identities.get(client_id)
            if not client:
                continue
            
            for obs in obs_list:
                pattern_id = obs.get("pattern_id")
                if not pattern_id:
                    continue
                
                if obs["success"]:
                    if pattern_id not in client.successful_patterns:
                        client.successful_patterns.append(pattern_id)
                else:
                    if pattern_id not in client.failed_patterns:
                        client.failed_patterns.append(pattern_id)
            
            rois = [obs["outcome"].get("roi", 0.0) for obs in obs_list]
            if rois:
                client.historical_roi = float(np.mean(rois))
            
            client.last_updated = datetime.now()
    
    def _find_similar_pattern(
        self,
        pattern: UniversalPattern
    ) -> Optional[UniversalPattern]:
        """Find similar existing pattern"""
        pattern_sig = self._pattern_signature(pattern)
        similar_ids = self.pattern_index.get(pattern_sig, [])
        
        for pattern_id in similar_ids:
            existing = self.universal_patterns.get(pattern_id)
            if existing and self._patterns_similar(existing, pattern):
                return existing
        
        return None
    
    def _pattern_signature(self, pattern: UniversalPattern) -> str:
        """Create pattern signature for indexing"""
        conditions_str = json.dumps(
            pattern.trigger_conditions,
            sort_keys=True
        )
        return hashlib.md5(conditions_str.encode()).hexdigest()
    
    def _patterns_similar(
        self,
        p1: UniversalPattern,
        p2: UniversalPattern
    ) -> bool:
        """Check if two patterns are similar"""
        if set(p1.trigger_conditions.keys()) != set(p2.trigger_conditions.keys()):
            return False
        
        for key in p1.trigger_conditions:
            v1 = p1.trigger_conditions[key]
            v2 = p2.trigger_conditions[key]
            
            if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                if abs(v1 - v2) / max(abs(v1), abs(v2), 1) > 0.2:
                    return False
            elif v1 != v2:
                return False
        
        return True
    
    def _merge_patterns(
        self,
        existing: UniversalPattern,
        new: UniversalPattern
    ):
        """Merge new pattern into existing"""
        total_obs = existing.observation_count + new.observation_count
        
        existing.success_rate = (
            existing.success_rate * existing.observation_count +
            new.success_rate * new.observation_count
        ) / total_obs
        
        existing.sample_size += new.sample_size
        existing.observation_count = total_obs
        
        existing.avg_roi = (
            existing.avg_roi * existing.observation_count +
            new.avg_roi * new.observation_count
        ) / total_obs
        
        existing.confidence = min(
            existing.success_rate * (existing.sample_size / 100),
            0.95
        )
        
        existing.last_updated = datetime.now()
    
    def _update_benchmarks(
        self,
        playbook: VerticalPlaybook,
        observations: List[Dict[str, Any]]
    ):
        """Update industry benchmarks"""
        metrics = defaultdict(list)
        
        for obs in observations:
            for key, value in obs["outcome"].items():
                if isinstance(value, (int, float)):
                    metrics[key].append(value)
        
        for key, values in metrics.items():
            if values:
                playbook.benchmarks[key] = float(np.mean(values))
    
    async def register_client(
        self,
        client_id: UUID,
        industry: IndustryVertical,
        config: Dict[str, Any]
    ) -> ClientIdentity:
        """Register new client"""
        client = ClientIdentity(
            client_id=client_id,
            industry=industry,
            brand_voice=config.get("brand_voice", "professional"),
            brand_guidelines=config.get("brand_guidelines", {}),
            risk_tolerance=config.get("risk_tolerance", 0.5),
            budget_constraints=config.get("budget_constraints", {}),
            approval_thresholds=config.get("approval_thresholds", {}),
            preferred_tools=set(config.get("preferred_tools", [])),
            blocked_tools=set(config.get("blocked_tools", [])),
            custom_workflows=config.get("custom_workflows", []),
            learning_enabled=config.get("learning_enabled", True),
            share_benchmarks=config.get("share_benchmarks", True),
            historical_roi=0.0,
            successful_patterns=[],
            failed_patterns=[],
            created_at=datetime.now(),
            last_updated=datetime.now()
        )
        
        self.client_identities[client_id] = client
        return client
    
    async def get_client_stats(self, client_id: UUID) -> Dict[str, Any]:
        """Get client statistics"""
        client = self.client_identities.get(client_id)
        if not client:
            raise ValueError(f"Unknown client: {client_id}")
        
        return {
            "client_id": str(client_id),
            "industry": client.industry.value,
            "historical_roi": client.historical_roi,
            "successful_patterns": len(client.successful_patterns),
            "failed_patterns": len(client.failed_patterns),
            "learning_enabled": client.learning_enabled,
            "created_at": client.created_at.isoformat(),
            "last_updated": client.last_updated.isoformat()
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide statistics"""
        return {
            "universal_patterns": len(self.universal_patterns),
            "vertical_playbooks": len(self.vertical_playbooks),
            "registered_clients": len(self.client_identities),
            "query_count": self.query_count,
            "learning_count": self.learning_count,
            "consolidation_count": self.consolidation_count,
            "learning_queue_size": len(self.learning_queue)
        }

# Made with Bob
