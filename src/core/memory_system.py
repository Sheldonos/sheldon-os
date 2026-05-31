"""
Sheldon OS Advanced Memory System

Implements a sophisticated hybrid memory architecture with:
- Short-term memory (working memory)
- Long-term memory (persistent storage)
- Vector-style retrieval with deterministic embeddings
- Knowledge graph extraction and expansion
- Reranking and synthesized retrieval responses
- Pattern recognition and memory consolidation
"""

import asyncio
import hashlib
import json
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import numpy as np


class MemoryType(Enum):
    """Types of memory entries"""

    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class MemoryPriority(Enum):
    """Memory priority levels"""

    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    MINIMAL = 1


@dataclass
class MemoryEntry:
    """Individual memory entry"""

    id: str
    content: Any
    memory_type: MemoryType
    priority: MemoryPriority
    timestamp: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    related_memories: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "access_count": self.access_count,
            "last_accessed": (
                self.last_accessed.isoformat() if self.last_accessed else None
            ),
            "tags": self.tags,
            "metadata": self.metadata,
            "embedding": self.embedding,
            "related_memories": self.related_memories,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Create from dictionary"""
        return cls(
            id=data["id"],
            content=data["content"],
            memory_type=MemoryType(data["memory_type"]),
            priority=MemoryPriority(data["priority"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            access_count=data.get("access_count", 0),
            last_accessed=(
                datetime.fromisoformat(data["last_accessed"])
                if data.get("last_accessed")
                else None
            ),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            embedding=data.get("embedding"),
            related_memories=data.get("related_memories", []),
        )


@dataclass
class Pattern:
    """Recognized pattern in memory"""

    id: str
    pattern_type: str
    occurrences: int
    confidence: float
    first_seen: datetime
    last_seen: datetime
    examples: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalCandidate:
    """Intermediate retrieval candidate"""

    entry: MemoryEntry
    vector_score: float = 0.0
    graph_score: float = 0.0
    rerank_score: float = 0.0
    source: str = "direct"

    @property
    def final_score(self) -> float:
        """Return the effective score used for final candidate ordering."""
        return self.rerank_score or (self.vector_score + self.graph_score)


@dataclass
class RetrievalResult:
    """Hybrid retrieval result"""

    query: str
    candidates: List[RetrievalCandidate]
    synthesized_summary: Optional[str]
    gaps: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class MemorySystem:  # pylint: disable=too-many-instance-attributes
    """Advanced memory management system

    Implements a multi-tiered memory architecture inspired by human cognition:
    - Short-term memory: Recent, frequently accessed information
    - Long-term memory: Consolidated, important information
    - Hybrid retrieval: vector recall + graph expansion + reranking
    - Pattern recognition: Identifies recurring patterns
    - Memory consolidation: Moves important memories to long-term storage
    """

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        short_term_capacity: int = 1000,
        long_term_capacity: int = 100000,
        consolidation_interval: int = 3600,
        retention_days: int = 90,
        embedding_model: str = "text-embedding-3-small",
        vector_backend: str = "zeroentropy",
        reranker_enabled: bool = True,
        reranker_model: str = "zeroentropy-reranker",
        graph_backend: str = "neo4j",
        graph_expansion_hops: int = 2,
        synthesis_enabled: bool = True,
        gap_analysis_enabled: bool = True,
        config: Optional[Any] = None,
    ):
        """Initialize memory system"""
        self.config = config

        if config is not None:
            memory_config = getattr(config, "memory", None)
            if memory_config is not None:
                short_term_capacity = getattr(
                    memory_config, "short_term_capacity", short_term_capacity
                )
                long_term_capacity = getattr(
                    memory_config, "long_term_capacity", long_term_capacity
                )
                consolidation_interval = getattr(
                    memory_config,
                    "consolidation_interval",
                    consolidation_interval,
                )
                retention_days = getattr(
                    memory_config, "retention_days", retention_days
                )
                embedding_model = getattr(
                    memory_config, "embedding_model", embedding_model
                )
                vector_backend = getattr(
                    memory_config, "vector_backend", vector_backend
                )
                reranker_enabled = getattr(
                    memory_config, "reranker_enabled", reranker_enabled
                )
                reranker_model = getattr(
                    memory_config, "reranker_model", reranker_model
                )
                graph_backend = getattr(
                    memory_config,
                    "graph_backend",
                    graph_backend,
                )
                graph_expansion_hops = getattr(
                    memory_config, "graph_expansion_hops", graph_expansion_hops
                )
                synthesis_enabled = getattr(
                    memory_config, "synthesis_enabled", synthesis_enabled
                )
                gap_analysis_enabled = getattr(
                    memory_config, "gap_analysis_enabled", gap_analysis_enabled
                )

        self.short_term_capacity = short_term_capacity
        self.long_term_capacity = long_term_capacity
        self.consolidation_interval = consolidation_interval
        self.retention_days = retention_days

        self.embedding_model = embedding_model
        self.vector_backend = vector_backend
        self.reranker_enabled = reranker_enabled
        self.reranker_model = reranker_model
        self.graph_backend = graph_backend
        self.graph_expansion_hops = graph_expansion_hops
        self.synthesis_enabled = synthesis_enabled
        self.gap_analysis_enabled = gap_analysis_enabled

        # Memory stores
        self.short_term: Dict[str, MemoryEntry] = {}
        self.long_term: Dict[str, MemoryEntry] = {}
        self.patterns: Dict[str, Pattern] = {}

        # Indexes for fast retrieval
        self.tag_index: Dict[str, List[str]] = defaultdict(list)
        self.type_index: Dict[MemoryType, List[str]] = defaultdict(list)
        self.priority_index: Dict[
            MemoryPriority,
            List[str],
        ] = defaultdict(list)

        # Hybrid retrieval indexes
        self.agent_index: Dict[str, List[str]] = defaultdict(list)
        self.memory_type_name_index: Dict[str, List[str]] = defaultdict(list)
        self.entity_index: Dict[str, Set[str]] = defaultdict(set)
        self.knowledge_graph: Dict[str, Set[str]] = defaultdict(set)

        # Statistics
        self.stats = {
            "total_memories": 0,
            "total_accesses": 0,
            "consolidations": 0,
            "patterns_found": 0,
            "hybrid_searches": 0,
            "graph_expansions": 0,
            "reranks": 0,
            "syntheses": 0,
            "gap_analyses": 0,
        }

        # Background tasks
        self._consolidation_task: Optional[asyncio.Task] = None
        self._running = False
        self.context_manager: Optional[Any] = None

    async def start(self):
        """Start background tasks"""
        self._running = True
        self._consolidation_task = asyncio.create_task(
            self._consolidation_loop()
        )

    async def stop(self):
        """Stop background tasks"""
        self._running = False
        if self._consolidation_task:
            self._consolidation_task.cancel()
            try:
                await self._consolidation_task
            except asyncio.CancelledError:
                pass

    async def initialize(self):
        """Compatibility wrapper for async initialization."""
        await self.start()

    async def cleanup(self):
        """Compatibility wrapper for async cleanup."""
        await self.stop()

    def _generate_id(self, content: Any) -> str:
        """Generate unique ID for memory entry"""
        content_str = json.dumps(content, sort_keys=True, default=str)
        timestamp = datetime.utcnow().isoformat()
        return hashlib.sha256(
            f"{content_str}{timestamp}".encode()
        ).hexdigest()[:16]

    def _content_to_text(self, content: Any) -> str:
        """Normalize content into searchable text"""
        if isinstance(content, str):
            return content
        if isinstance(content, dict):
            return json.dumps(content, sort_keys=True, default=str)
        if isinstance(content, list):
            return " ".join(self._content_to_text(item) for item in content)
        return str(content)

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenizer for deterministic retrieval"""
        normalized = "".join(
            ch.lower() if ch.isalnum() else " "
            for ch in text
        )
        return [token for token in normalized.split() if token]

    def _extract_entities(self, entry: MemoryEntry) -> List[str]:
        """Extract lightweight entities from content, tags, and metadata"""
        entities: Set[str] = set()

        for tag in entry.tags:
            if tag:
                entities.add(tag.lower())

        for token in self._tokenize(self._content_to_text(entry.content)):
            if len(token) >= 4:
                entities.add(token)

        for key, value in entry.metadata.items():
            if isinstance(value, str):
                entities.add(value.lower())
            elif isinstance(value, (int, float)):
                entities.add(f"{key}:{value}")
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        entities.add(item.lower())

        return sorted(entities)

    def _generate_embedding(self, content: Any) -> List[float]:
        """Generate deterministic pseudo-embedding for runtime retrieval"""
        text = self._content_to_text(content)
        tokens = self._tokenize(text)
        dimensions = 32
        vector = [0.0] * dimensions

        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode()).digest()
            for i in range(dimensions):
                vector[i] += digest[i] / 255.0

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    def _cosine_similarity(
        self, left: Optional[List[float]], right: Optional[List[float]]
    ) -> float:
        """Compute cosine similarity between two vectors"""
        if not left or not right or len(left) != len(right):
            return 0.0

        dot = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))

        if left_norm == 0 or right_norm == 0:
            return 0.0

        return dot / (left_norm * right_norm)

    def _all_memories(self) -> List[MemoryEntry]:
        """Return all memories"""
        return list(self.short_term.values()) + list(self.long_term.values())

    def _get_memory_by_id(self, memory_id: str) -> Optional[MemoryEntry]:
        """Get memory without updating access stats"""
        return self.short_term.get(memory_id) or self.long_term.get(memory_id)

    def _build_graph_links(self, entry: MemoryEntry):
        """Update entity graph and related memory links"""
        entities = self._extract_entities(entry)
        entry.metadata["entities"] = entities

        for entity in entities:
            self.entity_index[entity].add(entry.id)

        for i, entity in enumerate(entities):
            for other in entities[i + 1:]:
                self.knowledge_graph[entity].add(other)
                self.knowledge_graph[other].add(entity)

        related_ids: Set[str] = set()
        for entity in entities:
            related_ids.update(self.entity_index.get(entity, set()))

        related_ids.discard(entry.id)
        entry.related_memories = sorted(related_ids)[:50]

    async def store(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        content: Any,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        priority: MemoryPriority = MemoryPriority.MEDIUM,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store a new memory"""
        memory_id = self._generate_id(content)

        entry = MemoryEntry(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            priority=priority,
            timestamp=datetime.utcnow(),
            tags=tags or [],
            metadata=metadata or {},
            embedding=self._generate_embedding(content),
        )

        # Store in appropriate memory tier
        if memory_type == MemoryType.SHORT_TERM:
            self.short_term[memory_id] = entry
            await self._check_short_term_capacity()
        else:
            self.long_term[memory_id] = entry
            await self._check_long_term_capacity()

        # Update indexes
        self._update_indexes(entry)
        self._build_graph_links(entry)

        # Update statistics
        self.stats["total_memories"] += 1

        return memory_id

    async def retrieve(
        self,
        memory_id: str,
        update_access: bool = True,
    ) -> Optional[MemoryEntry]:
        """Retrieve a memory by ID"""
        entry = self._get_memory_by_id(memory_id)

        if entry and update_access:
            entry.access_count += 1
            entry.last_accessed = datetime.utcnow()
            self.stats["total_accesses"] += 1

        return entry

    async def search(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        memory_type: Optional[MemoryType] = None,
        priority: Optional[MemoryPriority] = None,
        limit: int = 10,
    ) -> List[MemoryEntry]:
        """Search memories

        If query is provided, uses hybrid retrieval.
        Otherwise falls back to indexed filtering.
        """
        if query:
            result = await self.hybrid_search(
                query=query,
                tags=tags,
                memory_type=memory_type,
                priority=priority,
                limit=limit,
            )
            return [candidate.entry for candidate in result.candidates[:limit]]

        candidates: List[MemoryEntry] = []

        if tags:
            tag_memory_ids: Set[str] = set()
            for tag in tags:
                tag_memory_ids.update(self.tag_index.get(tag, []))
            retrieved_candidates = [
                await self.retrieve(mid, update_access=False)
                for mid in tag_memory_ids
            ]
            candidates = [c for c in retrieved_candidates if c is not None]
        elif memory_type:
            type_memory_ids: List[str] = list(
                self.type_index.get(memory_type, [])
            )
            retrieved_candidates = [
                await self.retrieve(mid, update_access=False)
                for mid in type_memory_ids
            ]
            candidates = [c for c in retrieved_candidates if c is not None]
        elif priority:
            priority_memory_ids: List[str] = list(
                self.priority_index.get(priority, [])
            )
            retrieved_candidates = [
                await self.retrieve(mid, update_access=False)
                for mid in priority_memory_ids
            ]
            candidates = [c for c in retrieved_candidates if c is not None]
        else:
            candidates = self._all_memories()

        candidates.sort(
            key=lambda m: (m.access_count, m.timestamp),
            reverse=True,
        )

        return candidates[:limit]

    async def hybrid_search(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
        self,
        query: str,
        tags: Optional[List[str]] = None,
        memory_type: Optional[MemoryType] = None,
        priority: Optional[MemoryPriority] = None,
        limit: int = 10,
        graph_hops: Optional[int] = None,
    ) -> RetrievalResult:
        """Hybrid retrieval with vector, graph, reranking, and synthesis."""
        self.stats["hybrid_searches"] += 1
        query_embedding = self._generate_embedding(query)
        query_tokens = set(self._tokenize(query))
        query_entities = {
            token for token in query_tokens if len(token) >= 4
        }

        candidates: Dict[str, RetrievalCandidate] = {}

        for entry in self._all_memories():
            if tags and not set(tags).intersection(entry.tags):
                continue
            if memory_type and entry.memory_type != memory_type:
                continue
            if priority and entry.priority != priority:
                continue

            vector_score = self._cosine_similarity(
                query_embedding,
                entry.embedding,
            )
            lexical_overlap = len(
                query_tokens.intersection(
                    set(self._tokenize(self._content_to_text(entry.content)))
                )
            )
            lexical_score = lexical_overlap / max(len(query_tokens), 1)
            combined_vector_score = (
                vector_score * 0.7
            ) + (lexical_score * 0.3)

            if combined_vector_score > 0:
                candidates[entry.id] = RetrievalCandidate(
                    entry=entry,
                    vector_score=combined_vector_score,
                    source="vector",
                )

        hops = (
            graph_hops
            if graph_hops is not None
            else self.graph_expansion_hops
        )
        expanded_ids = self._expand_graph(query_entities, hops=hops)
        for memory_id in expanded_ids:
            expanded_entry = self._get_memory_by_id(memory_id)
            if expanded_entry is None:
                continue
            candidate = candidates.get(memory_id)
            graph_score = 0.25 + (0.05 * min(hops, 3))
            if candidate:
                candidate.graph_score += graph_score
                candidate.source = "vector+graph"
            else:
                candidates[memory_id] = RetrievalCandidate(
                    entry=expanded_entry,
                    graph_score=graph_score,
                    source="graph",
                )

        reranked = self._rerank_candidates(
            query_tokens,
            list(candidates.values()),
        )
        top_candidates = reranked[:limit]

        for candidate in top_candidates:
            await self.retrieve(candidate.entry.id, update_access=True)

        synthesized_summary = None
        if self.synthesis_enabled:
            synthesized_summary = self._synthesize(query, top_candidates)
            self.stats["syntheses"] += 1

        gaps = []
        if self.gap_analysis_enabled:
            gaps = self._analyze_gaps(query_tokens, top_candidates)
            self.stats["gap_analyses"] += 1

        return RetrievalResult(
            query=query,
            candidates=top_candidates,
            synthesized_summary=synthesized_summary,
            gaps=gaps,
            metadata={
                "vector_backend": self.vector_backend,
                "graph_backend": self.graph_backend,
                "reranker_enabled": self.reranker_enabled,
                "candidate_count": len(candidates),
            },
        )

    def _expand_graph(
        self,
        query_entities: Set[str],
        hops: int = 2,
    ) -> Set[str]:
        """Expand from query entities through the knowledge graph"""
        if not query_entities:
            return set()

        self.stats["graph_expansions"] += 1
        visited_entities = set(query_entities)
        frontier = set(query_entities)
        memory_ids: Set[str] = set()

        for entity in frontier:
            memory_ids.update(self.entity_index.get(entity, set()))

        for _ in range(max(hops, 0)):
            next_frontier: Set[str] = set()
            for entity in frontier:
                neighbors = self.knowledge_graph.get(entity, set())
                for neighbor in neighbors:
                    if neighbor not in visited_entities:
                        visited_entities.add(neighbor)
                        next_frontier.add(neighbor)
                        memory_ids.update(
                            self.entity_index.get(neighbor, set())
                        )
            frontier = next_frontier
            if not frontier:
                break

        return memory_ids

    def _rerank_candidates(
        self,
        query_tokens: Set[str],
        candidates: List[RetrievalCandidate],
    ) -> List[RetrievalCandidate]:
        """Apply deterministic reranking"""
        if self.reranker_enabled:
            self.stats["reranks"] += 1

        for candidate in candidates:
            entry_tokens = set(
                self._tokenize(self._content_to_text(candidate.entry.content))
            )
            overlap = len(query_tokens.intersection(entry_tokens))
            overlap_score = overlap / max(len(query_tokens), 1)

            recency_hours = max(
                (datetime.utcnow() - candidate.entry.timestamp).total_seconds()
                / 3600.0,
                1.0,
            )
            recency_score = 1.0 / math.log(recency_hours + 2.0)
            priority_score = candidate.entry.priority.value / 5.0
            access_score = min(candidate.entry.access_count / 10.0, 1.0)

            candidate.rerank_score = (
                candidate.vector_score * 0.45
                + candidate.graph_score * 0.20
                + overlap_score * 0.20
                + recency_score * 0.10
                + priority_score * 0.03
                + access_score * 0.02
            )

        return sorted(
            candidates,
            key=lambda candidate: candidate.final_score,
            reverse=True,
        )

    def _synthesize(
        self,
        query: str,
        candidates: List[RetrievalCandidate],
    ) -> str:
        """Create a concise synthesized summary from evidence"""
        if not candidates:
            return f"No evidence found for query: {query}"

        evidence_lines = []
        for candidate in candidates[:5]:
            content_text = self._content_to_text(candidate.entry.content)
            snippet = content_text[:180].replace("\n", " ")
            evidence_lines.append(
                f"- [{candidate.entry.memory_type.value}] "
                f"{snippet} (score={candidate.final_score:.3f})"
            )

        return "Synthesized evidence for query '{}':\n{}".format(
            query,
            "\n".join(evidence_lines),
        )

    def _analyze_gaps(
        self, query_tokens: Set[str], candidates: List[RetrievalCandidate]
    ) -> List[str]:
        """Identify missing information in retrieved evidence"""
        if not candidates:
            return ["No supporting memories found for the query."]

        evidence_tokens: Set[str] = set()
        for candidate in candidates:
            evidence_tokens.update(
                self._tokenize(self._content_to_text(candidate.entry.content))
            )

        missing = sorted(
            token
            for token in query_tokens
            if token not in evidence_tokens and len(token) >= 4
        )
        if not missing:
            return []

        return [
            f"Missing corroborating evidence for: "
            f"{', '.join(missing[:8])}"
        ]

    async def delete(self, memory_id: str) -> bool:
        """Delete a memory"""
        entry = self.short_term.pop(memory_id, None)
        if not entry:
            entry = self.long_term.pop(memory_id, None)

        if entry:
            self._remove_from_indexes(entry)
            self._remove_from_graph(entry)
            self.stats["total_memories"] -= 1
            return True

        return False

    async def consolidate(self):
        """Consolidate memories from short-term to long-term"""
        if not self.short_term:
            return

        access_counts = [m.access_count for m in self.short_term.values()]
        if not access_counts:
            return

        threshold = np.percentile(access_counts, 75)

        to_consolidate = []
        for memory_id, entry in list(self.short_term.items()):
            should_consolidate = (
                entry.access_count >= threshold
                or entry.priority.value >= MemoryPriority.HIGH.value
                or (datetime.utcnow() - entry.timestamp).days >= 7
            )

            if should_consolidate:
                to_consolidate.append(memory_id)

        for memory_id in to_consolidate:
            entry = self.short_term.pop(memory_id)
            self._remove_type_index(entry.id, entry.memory_type)
            entry.memory_type = MemoryType.LONG_TERM
            self.long_term[memory_id] = entry
            self._add_type_index(entry.id, entry.memory_type)

        self.stats["consolidations"] += 1
        await self._check_long_term_capacity()

    async def find_patterns(self) -> List[Pattern]:
        """Identify patterns in memories"""
        tag_patterns: Dict[str, int] = defaultdict(int)
        all_memories = self._all_memories()

        for memory in all_memories:
            for tag in memory.tags:
                tag_patterns[tag] += 1

        patterns = []
        for tag, count in tag_patterns.items():
            if count >= 3:
                pattern_id = hashlib.sha256(
                    f"pattern_{tag}".encode()
                ).hexdigest()[:16]

                if pattern_id not in self.patterns:
                    pattern = Pattern(
                        id=pattern_id,
                        pattern_type="tag_frequency",
                        occurrences=count,
                        confidence=min(count / 10.0, 1.0),
                        first_seen=datetime.utcnow(),
                        last_seen=datetime.utcnow(),
                        metadata={"tag": tag},
                    )
                    self.patterns[pattern_id] = pattern
                    patterns.append(pattern)
                    self.stats["patterns_found"] += 1

        return patterns

    def get_statistics(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        return {
            **self.stats,
            "short_term_count": len(self.short_term),
            "long_term_count": len(self.long_term),
            "pattern_count": len(self.patterns),
            "entity_count": len(self.entity_index),
            "graph_node_count": len(self.knowledge_graph),
            "short_term_capacity_used": (
                len(self.short_term) / self.short_term_capacity
            ),
            "long_term_capacity_used": (
                len(self.long_term) / self.long_term_capacity
            ),
            "vector_backend": self.vector_backend,
            "graph_backend": self.graph_backend,
            "reranker_enabled": self.reranker_enabled,
        }

    async def _check_short_term_capacity(self):
        """Check and manage short-term memory capacity"""
        if len(self.short_term) > self.short_term_capacity:
            sorted_memories = sorted(
                self.short_term.items(),
                key=lambda x: (
                    x[1].last_accessed or x[1].timestamp,
                    x[1].access_count,
                ),
            )

            to_remove = len(self.short_term) - self.short_term_capacity
            for memory_id, _ in sorted_memories[:to_remove]:
                await self.delete(memory_id)

    async def _check_long_term_capacity(self):
        """Check and manage long-term memory capacity"""
        if len(self.long_term) > self.long_term_capacity:
            sorted_memories = sorted(
                self.long_term.items(),
                key=lambda x: (x[1].access_count, x[1].timestamp),
            )

            to_remove = len(self.long_term) - self.long_term_capacity
            for memory_id, _ in sorted_memories[:to_remove]:
                await self.delete(memory_id)

    def _add_type_index(self, memory_id: str, memory_type: MemoryType):
        """Add memory to type index"""
        if memory_id not in self.type_index[memory_type]:
            self.type_index[memory_type].append(memory_id)

    def _remove_type_index(self, memory_id: str, memory_type: MemoryType):
        """Remove memory from type index"""
        if memory_id in self.type_index[memory_type]:
            self.type_index[memory_type].remove(memory_id)

    def _update_indexes(self, entry: MemoryEntry):
        """Update search indexes"""
        for tag in entry.tags:
            if entry.id not in self.tag_index[tag]:
                self.tag_index[tag].append(entry.id)

        self._add_type_index(entry.id, entry.memory_type)

        if entry.id not in self.priority_index[entry.priority]:
            self.priority_index[entry.priority].append(entry.id)

        agent_id = entry.metadata.get("agent_id")
        if agent_id and entry.id not in self.agent_index[agent_id]:
            self.agent_index[agent_id].append(entry.id)

        memory_type_name = entry.metadata.get("memory_type_name")
        if (
            memory_type_name
            and entry.id not in self.memory_type_name_index[memory_type_name]
        ):
            self.memory_type_name_index[memory_type_name].append(entry.id)

    def _remove_from_indexes(self, entry: MemoryEntry):
        """Remove from search indexes"""
        for tag in entry.tags:
            if entry.id in self.tag_index[tag]:
                self.tag_index[tag].remove(entry.id)

        self._remove_type_index(entry.id, entry.memory_type)

        if entry.id in self.priority_index[entry.priority]:
            self.priority_index[entry.priority].remove(entry.id)

        agent_id = entry.metadata.get("agent_id")
        if agent_id and entry.id in self.agent_index[agent_id]:
            self.agent_index[agent_id].remove(entry.id)

        memory_type_name = entry.metadata.get("memory_type_name")
        if (
            memory_type_name
            and entry.id in self.memory_type_name_index[memory_type_name]
        ):
            self.memory_type_name_index[memory_type_name].remove(entry.id)

    def _remove_from_graph(self, entry: MemoryEntry):
        """Remove memory from graph indexes"""
        entities = entry.metadata.get("entities", [])
        for entity in entities:
            if entry.id in self.entity_index[entity]:
                self.entity_index[entity].remove(entry.id)
            if not self.entity_index[entity]:
                self.entity_index.pop(entity, None)

    async def _consolidation_loop(self):
        """Background task for periodic memory consolidation"""
        while self._running:
            try:
                await asyncio.sleep(self.consolidation_interval)
                await self.consolidate()
                await self.find_patterns()
            except asyncio.CancelledError:
                break
            except Exception as exc:  # pylint: disable=broad-exception-caught
                print(f"Error in consolidation loop: {exc}")

    async def export_memories(
        self, memory_type: Optional[MemoryType] = None
    ) -> List[Dict[str, Any]]:
        """Export memories to dictionary format"""
        memories: List[Dict[str, Any]] = []

        sources: List[MemoryEntry] = []
        if memory_type is None or memory_type == MemoryType.SHORT_TERM:
            sources.extend(self.short_term.values())
        if memory_type is None or memory_type != MemoryType.SHORT_TERM:
            sources.extend(self.long_term.values())

        for entry in sources:
            if memory_type is None or entry.memory_type == memory_type:
                memories.append(entry.to_dict())

        return memories

    async def import_memories(self, memories: List[Dict[str, Any]]):
        """Import memories from dictionary format"""
        for memory_data in memories:
            entry = MemoryEntry.from_dict(memory_data)
            if entry.embedding is None:
                entry.embedding = self._generate_embedding(entry.content)

            if entry.memory_type == MemoryType.SHORT_TERM:
                self.short_term[entry.id] = entry
            else:
                self.long_term[entry.id] = entry

            self._update_indexes(entry)
            self._build_graph_links(entry)

        self.stats["total_memories"] = (
            len(self.short_term) + len(self.long_term)
        )

    async def store_memory(
        self,
        agent_id: str,
        memory_type: str,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Compatibility helper for integration-style memory API"""
        normalized_type = memory_type.lower()
        mapped_type = {
            "short_term": MemoryType.SHORT_TERM,
            "working": MemoryType.SHORT_TERM,
            "conversation": MemoryType.EPISODIC,
            "task_execution": MemoryType.EPISODIC,
            "episodic": MemoryType.EPISODIC,
            "semantic": MemoryType.SEMANTIC,
            "procedural": MemoryType.PROCEDURAL,
            "long_term": MemoryType.LONG_TERM,
        }.get(normalized_type, MemoryType.LONG_TERM)

        merged_metadata = {
            **(metadata or {}),
            "agent_id": agent_id,
            "memory_type_name": normalized_type,
        }

        tags = [agent_id, normalized_type]
        if isinstance(content, dict):
            tags.extend(str(key) for key in content.keys())

        return await self.store(
            content=content,
            memory_type=mapped_type,
            priority=MemoryPriority.MEDIUM,
            tags=sorted(set(tags)),
            metadata=merged_metadata,
        )

    async def retrieve_memories(
        self,
        agent_id: str,
        memory_type: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Retrieve memories for an agent in integration-friendly format."""
        memory_ids = self.agent_index.get(agent_id, [])
        entries = [
            self._get_memory_by_id(memory_id)
            for memory_id in memory_ids
        ]
        entries = [entry for entry in entries if entry is not None]

        if memory_type:
            normalized_type = memory_type.lower()
            entries = [
                entry
                for entry in entries
                if entry is not None
                and entry.metadata.get("memory_type_name") == normalized_type
            ]

        non_null_entries = [entry for entry in entries if entry is not None]
        non_null_entries.sort(
            key=lambda entry: (
                entry.access_count,
                entry.timestamp,
            ),
            reverse=True,
        )
        return [entry.content for entry in non_null_entries[:limit]]

    async def consolidate_memories(self, agent_id: Optional[str] = None):
        """Compatibility wrapper for consolidation"""
        if agent_id:
            agent_memory_ids = list(self.agent_index.get(agent_id, []))
            consolidated_count = 0
            for memory_id in agent_memory_ids:
                entry = self._get_memory_by_id(memory_id)
                if not entry:
                    continue
                if entry.memory_type == MemoryType.SHORT_TERM:
                    self.short_term.pop(memory_id, None)
                    self._remove_type_index(memory_id, MemoryType.SHORT_TERM)
                    entry.memory_type = MemoryType.LONG_TERM
                    self.long_term[memory_id] = entry
                    self._add_type_index(memory_id, MemoryType.LONG_TERM)
                    consolidated_count += 1
            self.stats["consolidations"] += 1
            await self._check_long_term_capacity()

            context_manager = getattr(self, "context_manager", None)
            if context_manager is not None:
                await context_manager.create_snapshot(
                    agent_id=agent_id,
                    context={
                        "agent_id": agent_id,
                        "consolidated_memories": consolidated_count,
                    },
                    snapshot_type="consolidation",
                    metadata={
                        "trigger": "memory_consolidation",
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
            return consolidated_count

        await self.consolidate()

    async def store_long_term(
        self,
        key: str,
        value: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store a long-term memory entry.

        Uses integration-style key semantics.

        """
        memory_type_name = (
            key.split(":", 1)[0].lower()
            if ":" in key
            else "long_term"
        )
        merged_metadata = {
            **(metadata or {}),
            "memory_type_name": memory_type_name,
            "storage_key": key,
        }

        tags = [memory_type_name, "long_term"]
        if isinstance(value, dict):
            tags.extend(str(k) for k in value.keys())

        return await self.store(
            content=value,
            memory_type=MemoryType.LONG_TERM,
            priority=MemoryPriority.HIGH,
            tags=sorted(set(tags)),
            metadata=merged_metadata,
        )

    async def retrieve_long_term(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a long-term memory entry by integration-style key."""
        for entry in self.long_term.values():
            if entry.metadata.get("storage_key") == key:
                return (
                    entry.content
                    if isinstance(entry.content, dict)
                    else None
                )

        if ":" not in key:
            return None

        prefix, identifier = key.split(":", 1)
        prefix_map = {
            "pattern": "pattern",
            "opportunity": "opportunity",
            "forecast": "forecast",
            "decision": "decision",
        }
        expected_type = prefix_map.get(prefix)
        if expected_type is None:
            return None

        for entry in self.long_term.values():
            if entry.metadata.get("memory_type_name") != expected_type:
                continue
            content = entry.content if isinstance(entry.content, dict) else {}
            if content.get("id") == identifier:
                return content
        return None

    async def query_with_synthesis(
        self,
        query: str,
        limit: int = 8,
    ) -> Dict[str, Any]:
        """Convenience API for higher-level systems"""
        result = await self.hybrid_search(query=query, limit=limit)
        return {
            "query": result.query,
            "summary": result.synthesized_summary,
            "gaps": result.gaps,
            "results": [
                {
                    "id": candidate.entry.id,
                    "content": candidate.entry.content,
                    "memory_type": candidate.entry.memory_type.value,
                    "score": candidate.final_score,
                    "source": candidate.source,
                    "metadata": candidate.entry.metadata,
                }
                for candidate in result.candidates
            ],
            "metadata": result.metadata,
        }


# Made with Bob
