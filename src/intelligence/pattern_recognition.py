"""
Pattern Recognition System for Sheldon OS

This module provides sophisticated pattern analysis and learning capabilities,
enabling the system to identify recurring patterns, detect anomalies, and learn
from historical successes and failures.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial.distance import cosine
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of patterns that can be detected"""

    TEMPORAL = "temporal"  # Time-based patterns
    BEHAVIORAL = "behavioral"  # User/system behavior patterns
    MARKET = "market"  # Market trend patterns
    OPERATIONAL = "operational"  # Business operation patterns
    ANOMALY = "anomaly"  # Anomalous patterns
    SUCCESS = "success"  # Successful outcome patterns
    FAILURE = "failure"  # Failed outcome patterns


@dataclass
class Pattern:
    """Represents a detected pattern"""

    id: str
    type: PatternType
    description: str
    confidence: float  # 0.0 to 1.0
    occurrences: int
    success_rate: float  # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    features: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert pattern to dictionary"""
        return {
            "id": self.id,
            "type": self.type.value,
            "description": self.description,
            "confidence": self.confidence,
            "occurrences": self.occurrences,
            "success_rate": self.success_rate,
            "metadata": self.metadata,
            "discovered_at": self.discovered_at.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "features": self.features,
        }


@dataclass
class PatternMatch:
    """Represents a match between data and a known pattern"""

    pattern: Pattern
    similarity: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    matched_features: Dict[str, float]
    timestamp: datetime = field(default_factory=datetime.utcnow)


class PatternRecognitionEngine:
    """
    Advanced pattern recognition system that learns from data and identifies
    recurring patterns, anomalies, and trends.
    """

    def __init__(self, memory_system=None):
        """
        Initialize the pattern recognition engine

        Args:
            memory_system: Optional memory system for pattern storage
        """
        self.memory_system = memory_system
        self.patterns: Dict[str, Pattern] = {}
        self.pattern_history: List[Dict[str, Any]] = []
        self.scaler = StandardScaler()

        # Configuration
        self.min_confidence = 0.6
        self.min_occurrences = 3
        self.similarity_threshold = 0.75

        logger.info("Pattern Recognition Engine initialized")

    async def analyze_time_series(
        self,
        data: pd.DataFrame,
        value_column: str,
        time_column: str = "timestamp",
    ) -> List[Pattern]:
        """
        Analyze time series data for temporal patterns

        Args:
            data: DataFrame with time series data
            value_column: Column name containing values
            time_column: Column name containing timestamps

        Returns:
            List of detected temporal patterns
        """
        patterns = []

        try:
            # Ensure data is sorted by time
            data = data.sort_values(time_column)
            values = np.asarray(data[value_column].to_numpy(dtype=float))

            # Detect trends
            trend_pattern = await self._detect_trend(values, data)
            if trend_pattern:
                patterns.append(trend_pattern)

            # Detect seasonality
            seasonal_patterns = await self._detect_seasonality(values, data)
            patterns.extend(seasonal_patterns)

            # Detect cycles
            cycle_patterns = await self._detect_cycles(values, data)
            patterns.extend(cycle_patterns)

            # Store patterns
            for pattern in patterns:
                await self._store_pattern(pattern)

            logger.info(f"Detected {len(patterns)} temporal patterns")
            return patterns

        except Exception as e:
            logger.error(f"Error analyzing time series: {e}")
            return []

    async def _detect_trend(
        self, values: np.ndarray, data: pd.DataFrame
    ) -> Optional[Pattern]:
        """Detect trend in time series data"""
        try:
            # Linear regression for trend
            x = np.arange(len(values))
            regression_values = tuple(stats.linregress(x, values))
            slope = float(regression_values[0])
            intercept = float(regression_values[1])
            r_value = float(regression_values[2])
            p_value = float(regression_values[3])

            # Determine if trend is significant
            if abs(r_value) > 0.7 and p_value < 0.05:
                trend_type = "increasing" if slope > 0 else "decreasing"

                pattern = Pattern(
                    id=f"trend_{datetime.utcnow().timestamp()}",
                    type=PatternType.TEMPORAL,
                    description=f"{trend_type.capitalize()} trend detected",
                    confidence=float(abs(r_value)),
                    occurrences=len(values),
                    success_rate=1.0,  # Trends are descriptive, not predictive
                    metadata={
                        "slope": float(slope),
                        "intercept": float(intercept),
                        "r_squared": float(r_value**2),
                        "p_value": float(p_value),
                        "trend_type": trend_type,
                    },
                    features={
                        "slope": float(slope),
                        "strength": float(abs(r_value)),
                    },
                )

                return pattern

            return None

        except Exception as e:
            logger.error(f"Error detecting trend: {e}")
            return None

    async def _detect_seasonality(
        self, values: np.ndarray, data: pd.DataFrame
    ) -> List[Pattern]:
        """Detect seasonal patterns in time series"""
        patterns = []

        try:
            # Use FFT to detect periodic components
            fft = np.fft.fft(values)
            frequencies = np.fft.fftfreq(len(values))

            # Find dominant frequencies
            power = np.abs(fft) ** 2
            threshold = np.percentile(power, 95)

            dominant_freqs = frequencies[power > threshold]

            for freq in dominant_freqs:
                if freq > 0:  # Ignore DC component
                    period = 1 / freq

                    pattern = Pattern(
                        id=f"seasonal_{datetime.utcnow().timestamp()}_{freq}",
                        type=PatternType.TEMPORAL,
                        description=(
                            f"Seasonal pattern with period {period:.2f}"
                        ),
                        confidence=0.8,
                        occurrences=int(len(values) / period),
                        success_rate=0.85,
                        metadata={
                            "period": float(period),
                            "frequency": float(freq),
                            "power": float(power[frequencies == freq][0]),
                        },
                        features={
                            "period": float(period),
                            "strength": float(power[frequencies == freq][0]),
                        },
                    )

                    patterns.append(pattern)

            return patterns

        except Exception as e:
            logger.error(f"Error detecting seasonality: {e}")
            return []

    async def _detect_cycles(
        self, values: np.ndarray, data: pd.DataFrame
    ) -> List[Pattern]:
        """Detect cyclical patterns"""
        patterns = []

        try:
            # Detect peaks and troughs
            from scipy.signal import find_peaks

            peaks, _ = find_peaks(values, distance=5)
            troughs, _ = find_peaks(-values, distance=5)

            if len(peaks) >= 2 and len(troughs) >= 2:
                # Calculate average cycle length
                peak_distances = np.diff(peaks)
                avg_cycle = np.mean(peak_distances)

                pattern = Pattern(
                    id=f"cycle_{datetime.utcnow().timestamp()}",
                    type=PatternType.TEMPORAL,
                    description=(
                        f"Cyclical pattern with average length "
                        f"{avg_cycle:.2f}"
                    ),
                    confidence=0.75,
                    occurrences=len(peaks),
                    success_rate=0.8,
                    metadata={
                        "avg_cycle_length": float(avg_cycle),
                        "num_peaks": len(peaks),
                        "num_troughs": len(troughs),
                    },
                    features={
                        "cycle_length": float(avg_cycle),
                        "amplitude": float(np.std(values)),
                    },
                )

                patterns.append(pattern)

            return patterns

        except Exception as e:
            logger.error(f"Error detecting cycles: {e}")
            return []

    async def detect_anomalies(
        self,
        data: pd.DataFrame,
        features: List[str],
        contamination: float = 0.1,
    ) -> List[Pattern]:
        """
        Detect anomalous patterns in data using DBSCAN clustering

        Args:
            data: DataFrame with features
            features: List of feature column names
            contamination: Expected proportion of anomalies

        Returns:
            List of anomaly patterns
        """
        patterns = []

        try:
            # Extract feature matrix
            X = data[features].values

            # Standardize features
            X_scaled = self.scaler.fit_transform(X)

            # Apply DBSCAN for anomaly detection
            clustering = DBSCAN(eps=0.5, min_samples=5)
            labels = clustering.fit_predict(X_scaled)

            # Identify anomalies (label = -1)
            anomaly_mask = labels == -1
            num_anomalies = np.sum(anomaly_mask)

            if num_anomalies > 0:
                pattern = Pattern(
                    id=f"anomaly_{datetime.utcnow().timestamp()}",
                    type=PatternType.ANOMALY,
                    description=(
                        f"Detected {num_anomalies} anomalous data points"
                    ),
                    confidence=0.85,
                    occurrences=num_anomalies,
                    success_rate=0.0,  # Anomalies are failures by definition
                    metadata={
                        "num_anomalies": int(num_anomalies),
                        "total_points": len(data),
                        "anomaly_rate": float(num_anomalies / len(data)),
                        "features": features,
                    },
                    features={
                        "anomaly_rate": float(num_anomalies / len(data))
                    },
                )

                patterns.append(pattern)
                await self._store_pattern(pattern)

            logger.info(f"Detected {len(patterns)} anomaly patterns")
            return patterns

        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []

    async def learn_from_outcomes(
        self, outcomes: List[Dict[str, Any]], success_key: str = "success"
    ) -> List[Pattern]:
        """
        Learn patterns from historical outcomes (successes and failures)

        Args:
            outcomes: List of outcome dictionaries
            success_key: Key indicating success/failure

        Returns:
            List of learned patterns
        """
        patterns = []

        try:
            # Separate successes and failures
            successes = [o for o in outcomes if o.get(success_key, False)]
            failures = [o for o in outcomes if not o.get(success_key, False)]

            # Learn success patterns
            if successes:
                success_pattern = await self._extract_common_features(
                    successes, PatternType.SUCCESS, "Success pattern"
                )
                if success_pattern:
                    patterns.append(success_pattern)

            # Learn failure patterns
            if failures:
                failure_pattern = await self._extract_common_features(
                    failures, PatternType.FAILURE, "Failure pattern"
                )
                if failure_pattern:
                    patterns.append(failure_pattern)

            # Store patterns
            for pattern in patterns:
                await self._store_pattern(pattern)

            logger.info(f"Learned {len(patterns)} outcome patterns")
            return patterns

        except Exception as e:
            logger.error(f"Error learning from outcomes: {e}")
            return []

    async def _extract_common_features(
        self,
        data: List[Dict[str, Any]],
        pattern_type: PatternType,
        description: str,
    ) -> Optional[Pattern]:
        """Extract common features from a set of data points"""
        try:
            # Find common keys
            all_keys: Set[str] = set()
            for item in data:
                all_keys.update(item.keys())

            # Calculate feature frequencies
            feature_counts: Dict[str, Dict[Any, int]] = defaultdict(
                lambda: defaultdict(int)
            )
            for item in data:
                for key, value in item.items():
                    if isinstance(value, (int, float, bool, str)):
                        feature_counts[key][value] += 1

            # Extract dominant features
            common_features = {}
            for key, value_counts in feature_counts.items():
                total = sum(value_counts.values())
                for value, count in value_counts.items():
                    frequency = count / total
                    if frequency > 0.6:  # Feature appears in >60% of cases
                        common_features[f"{key}_{value}"] = frequency

            if common_features:
                success_rate = (
                    1.0 if pattern_type == PatternType.SUCCESS else 0.0
                )

                pattern = Pattern(
                    id=f"{pattern_type.value}_{datetime.utcnow().timestamp()}",
                    type=pattern_type,
                    description=description,
                    confidence=0.8,
                    occurrences=len(data),
                    success_rate=success_rate,
                    metadata={
                        "sample_size": len(data),
                        "common_features": common_features,
                    },
                    features=common_features,
                )

                return pattern

            return None

        except Exception as e:
            logger.error(f"Error extracting common features: {e}")
            return None

    async def match_pattern(
        self,
        data: Dict[str, Any],
        pattern_types: Optional[List[PatternType]] = None,
    ) -> List[PatternMatch]:
        """
        Match input data against known patterns

        Args:
            data: Data to match against patterns
            pattern_types: Optional filter for pattern types

        Returns:
            List of pattern matches sorted by similarity
        """
        matches = []

        try:
            # Filter patterns by type if specified
            patterns_to_check: List[Pattern] = list(self.patterns.values())
            if pattern_types:
                patterns_to_check = [
                    p for p in patterns_to_check if p.type in pattern_types
                ]

            # Extract features from input data
            input_features = self._extract_features(data)

            # Compare against each pattern
            for pattern in patterns_to_check:
                similarity = self._calculate_similarity(
                    input_features, pattern.features
                )

                if similarity >= self.similarity_threshold:
                    # Calculate confidence based on pattern history
                    confidence = (
                        similarity * 0.6
                        + pattern.confidence * 0.3
                        + pattern.success_rate * 0.1
                    )

                    match = PatternMatch(
                        pattern=pattern,
                        similarity=similarity,
                        confidence=confidence,
                        matched_features=input_features,
                    )

                    matches.append(match)

            # Sort by confidence
            matches.sort(key=lambda m: m.confidence, reverse=True)

            logger.info(f"Found {len(matches)} pattern matches")
            return matches

        except Exception as e:
            logger.error(f"Error matching patterns: {e}")
            return []

    def _extract_features(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Extract numerical features from data"""
        features = {}

        for key, value in data.items():
            if isinstance(value, (int, float)):
                features[key] = float(value)
            elif isinstance(value, bool):
                features[key] = 1.0 if value else 0.0
            elif isinstance(value, str):
                # Hash string to numerical value
                features[f"{key}_hash"] = float(hash(value) % 1000) / 1000

        return features

    def _calculate_similarity(
        self, features1: Dict[str, float], features2: Dict[str, float]
    ) -> float:
        """Calculate cosine similarity between two feature sets"""
        try:
            # Get common keys
            common_keys = set(features1.keys()) & set(features2.keys())

            if not common_keys:
                return 0.0

            # Create vectors
            vec1 = np.array([features1[k] for k in common_keys])
            vec2 = np.array([features2[k] for k in common_keys])

            # Calculate cosine similarity
            similarity = 1 - cosine(vec1, vec2)

            return float(max(0.0, min(1.0, similarity)))

        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0

    async def _store_pattern(self, pattern: Pattern) -> None:
        """Store pattern in memory system"""
        try:
            self.patterns[pattern.id] = pattern

            if self.memory_system:
                await self.memory_system.store_long_term(
                    key=f"pattern:{pattern.id}",
                    value=pattern.to_dict(),
                    metadata={
                        "type": "pattern",
                        "pattern_type": pattern.type.value,
                    },
                )

            logger.debug(f"Stored pattern: {pattern.id}")

        except Exception as e:
            logger.error(f"Error storing pattern: {e}")

    async def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get statistics about detected patterns"""
        try:
            stats_by_type: Dict[str, Dict[str, float]] = defaultdict(
                lambda: {
                    "count": 0.0,
                    "avg_confidence": 0.0,
                    "avg_success_rate": 0.0,
                }
            )

            for pattern in self.patterns.values():
                type_key = pattern.type.value
                stats_by_type[type_key]["count"] += 1
                stats_by_type[type_key]["avg_confidence"] += pattern.confidence
                stats_by_type[type_key]["avg_success_rate"] += (
                    pattern.success_rate
                )

            # Calculate averages
            for type_stats in stats_by_type.values():
                count = type_stats["count"]
                if count > 0:
                    type_stats["avg_confidence"] /= count
                    type_stats["avg_success_rate"] /= count

            return {
                "total_patterns": len(self.patterns),
                "by_type": dict(stats_by_type),
                "last_updated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting pattern statistics: {e}")
            return {}

    async def retrain(self, new_data: List[Dict[str, Any]]) -> None:
        """Retrain pattern recognition with new data"""
        try:
            logger.info("Retraining pattern recognition engine...")

            # Learn from new outcomes
            await self.learn_from_outcomes(new_data)

            # Update pattern statistics
            stats = await self.get_pattern_statistics()
            logger.info(
                f"Retrained with {len(new_data)} new data points. "
                f"Stats: {stats}"
            )

        except Exception as e:
            logger.error(f"Error retraining: {e}")


# Made with Bob
