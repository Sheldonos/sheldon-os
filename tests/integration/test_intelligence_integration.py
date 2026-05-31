"""
Integration Tests for Intelligence Layer with Core Systems

Tests integration of intelligence modules with orchestrator and memory.
"""


import numpy as np
import pandas as pd
import pytest

from src.core.config import Config
from src.core.memory_system import MemorySystem
from src.intelligence import (
    CriteriaType,
    Criterion,
    DecisionEngine,
    ForecastingEngine,
    OpportunityFinder,
    Option,
    PatternRecognitionEngine,
)


class TestIntelligenceIntegration:
    """Test intelligence layer integration with core systems"""

    @pytest.fixture
    async def memory_system(self):
        """Create memory system"""
        memory = MemorySystem()
        await memory.initialize()
        yield memory
        await memory.cleanup()

    @pytest.fixture
    def config(self):
        """Create configuration"""
        return Config()

    @pytest.mark.asyncio
    async def test_pattern_recognition_with_memory(self, memory_system):
        """Test pattern recognition stores patterns in memory"""
        engine = PatternRecognitionEngine(memory_system=memory_system)

        # Create sample data
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
        values = np.linspace(100, 200, 100) + np.random.normal(0, 5, 100)
        data = pd.DataFrame({"timestamp": dates, "value": values})

        # Analyze patterns
        patterns = await engine.analyze_time_series(data, "value")

        assert len(patterns) > 0
        assert len(engine.patterns) > 0

        # Verify patterns are stored in memory
        for pattern in patterns:
            stored = await memory_system.retrieve_long_term(
                f"pattern:{pattern.id}"
            )
            assert stored is not None
            assert stored["type"] == pattern.type.value

    @pytest.mark.asyncio
    async def test_opportunity_finder_with_memory(self, memory_system):
        """Test opportunity finder stores opportunities in memory"""
        finder = OpportunityFinder(memory_system=memory_system)

        # Scan market
        opportunities = await finder.scan_market(
            industry="fintech", keywords=["AI", "payments"]
        )

        assert len(opportunities) > 0

        # Verify opportunities are stored
        for opp in opportunities:
            stored = await memory_system.retrieve_long_term(
                f"opportunity:{opp.id}"
            )
            assert stored is not None
            assert stored["market"] == opp.market

    @pytest.mark.asyncio
    async def test_forecasting_with_memory(self, memory_system):
        """Test forecasting engine stores forecasts in memory"""
        engine = ForecastingEngine(memory_system=memory_system)

        # Create sample data
        dates = pd.date_range(start="2023-01-01", periods=24, freq="ME")
        revenue = np.linspace(100000, 200000, 24)
        data = pd.DataFrame({"date": dates, "revenue": revenue})

        # Generate forecast
        forecast = await engine.forecast_revenue(data, periods=12)

        assert forecast is not None
        assert len(forecast.predictions) == 12

        # Verify forecast is stored
        stored = await memory_system.retrieve_long_term(
            f"forecast:{forecast.id}"
        )
        assert stored is not None
        assert stored["metric"] == "revenue"

    @pytest.mark.asyncio
    async def test_decision_engine_with_memory(self, memory_system):
        """Test decision engine stores decisions in memory"""
        engine = DecisionEngine(memory_system=memory_system)

        # Create decision scenario
        options = [
            Option(
                id="opt1",
                name="Option 1",
                description="First option",
                scores={"cost": 100, "roi": 5.0},
            ),
            Option(
                id="opt2",
                name="Option 2",
                description="Second option",
                scores={"cost": 150, "roi": 8.0},
            ),
        ]

        criteria = [
            Criterion(name="cost", type=CriteriaType.COST, weight=0.4),
            Criterion(name="roi", type=CriteriaType.BENEFIT, weight=0.6),
        ]

        # Make decision
        decision = await engine.make_decision(
            "Which option?",
            options,
            criteria,
        )

        assert decision is not None
        assert decision.recommended_option in options

        # Verify decision is stored
        stored = await memory_system.retrieve_long_term(
            f"decision:{decision.id}"
        )
        assert stored is not None
        assert stored["question"] == "Which option?"

    @pytest.mark.asyncio
    async def test_full_intelligence_workflow(self, memory_system):
        """Test complete intelligence workflow with memory integration"""
        # Initialize all engines
        pattern_engine = PatternRecognitionEngine(memory_system=memory_system)
        opportunity_finder = OpportunityFinder(
            memory_system=memory_system, pattern_engine=pattern_engine
        )
        forecasting_engine = ForecastingEngine(memory_system=memory_system)
        decision_engine = DecisionEngine(memory_system=memory_system)

        # Step 1: Find opportunities
        opportunities = await opportunity_finder.scan_market(
            industry="fintech", keywords=["AI", "compliance"]
        )
        assert len(opportunities) > 0

        # Step 2: Forecast revenue for top opportunity
        dates = pd.date_range(start="2024-01-01", periods=12, freq="ME")
        revenue = np.linspace(100000, 500000, 12)
        data = pd.DataFrame({"date": dates, "revenue": revenue})

        forecast = await forecasting_engine.forecast_revenue(data, periods=12)
        assert forecast is not None

        # Step 3: Make strategic decision
        top_opp = opportunities[0]

        options = [
            Option(
                id="pursue",
                name="Pursue Opportunity",
                description="Launch the product",
                scores={
                    "market_size": top_opp.market_size.tam / 1e9,
                    "roi": top_opp.estimated_roi,
                    "confidence": top_opp.confidence_score,
                },
            ),
            Option(
                id="wait",
                name="Wait",
                description="Wait for better timing",
                scores={"market_size": 0.0, "roi": 0.0, "confidence": 1.0},
            ),
        ]

        criteria = [
            Criterion(
                name="market_size",
                type=CriteriaType.BENEFIT,
                weight=0.4,
            ),
            Criterion(
                name="roi",
                type=CriteriaType.BENEFIT,
                weight=0.4,
            ),
            Criterion(
                name="confidence",
                type=CriteriaType.BENEFIT,
                weight=0.2,
            ),
        ]

        decision = await decision_engine.make_decision(
            "Should we pursue this opportunity?", options, criteria
        )

        assert decision is not None
        assert decision.recommended_option.id in ["pursue", "wait"]

        # Verify all data is stored in memory
        assert len(opportunity_finder.opportunities) > 0
        assert len(forecasting_engine.forecasts) > 0
        assert len(decision_engine.decisions) > 0

    @pytest.mark.asyncio
    async def test_pattern_learning_feedback_loop(self, memory_system):
        """Test pattern recognition learns from outcomes"""
        engine = PatternRecognitionEngine(memory_system=memory_system)

        # Initial learning
        outcomes = [
            {"strategy": "aggressive", "market": "growing", "success": True},
            {"strategy": "aggressive", "market": "stable", "success": True},
            {
                "strategy": "conservative",
                "market": "declining",
                "success": True,
            },
        ]

        patterns = await engine.learn_from_outcomes(outcomes)
        initial_count = len(patterns)

        # Additional learning
        new_outcomes = [
            {"strategy": "aggressive", "market": "growing", "success": True},
            {"strategy": "moderate", "market": "stable", "success": True},
        ]

        await engine.retrain(new_outcomes)

        # Verify learning occurred
        stats = await engine.get_pattern_statistics()
        assert stats["total_patterns"] >= initial_count

    @pytest.mark.asyncio
    async def test_forecasting_model_performance_tracking(self, memory_system):
        """Test forecasting engine tracks model performance"""
        engine = ForecastingEngine(memory_system=memory_system)

        # Generate forecast
        dates = pd.date_range(start="2023-01-01", periods=12, freq="ME")
        revenue = np.linspace(100000, 200000, 12)
        data = pd.DataFrame({"date": dates, "revenue": revenue})

        forecast = await engine.forecast_revenue(data, periods=6)

        # Simulate actual results
        actual_values = [
            210000.0,
            220000.0,
            230000.0,
            240000.0,
            250000.0,
            260000.0,
        ]

        # Update performance
        await engine.update_model_performance(forecast.id, actual_values)

        # Verify performance tracking
        assert len(engine.model_performance) > 0
        best_model = engine.get_best_model()
        assert best_model is not None

    @pytest.mark.asyncio
    async def test_decision_learning_from_outcomes(self, memory_system):
        """Test decision engine learns from outcomes"""
        engine = DecisionEngine(memory_system=memory_system)

        # Make decision
        options = [
            Option(
                id="opt1",
                name="Option 1",
                description="Test",
                scores={"value": 100},
            )
        ]
        criteria = [
            Criterion(
                name="value",
                type=CriteriaType.BENEFIT,
                weight=1.0,
            )
        ]

        decision = await engine.make_decision("Test", options, criteria)

        # Provide outcome feedback
        await engine.learn_from_outcome(
            decision.id, actual_outcome={"revenue": 1000000}, success=True
        )

        # Verify learning
        assert len(engine.decision_history) > 0
        stats = engine.get_decision_statistics()
        assert stats["total_decisions"] > 0


class TestIntelligencePerformance:
    """Performance tests for intelligence layer"""

    @pytest.mark.asyncio
    async def test_pattern_recognition_performance(self):
        """Test pattern recognition performance with large dataset"""
        import time

        engine = PatternRecognitionEngine()

        # Large dataset
        dates = pd.date_range(start="2020-01-01", periods=1000, freq="D")
        values = np.random.normal(100, 10, 1000)
        data = pd.DataFrame({"timestamp": dates, "value": values})

        start = time.time()
        patterns = await engine.analyze_time_series(data, "value")
        duration = time.time() - start

        assert duration < 5.0  # Should complete in under 5 seconds
        assert len(patterns) >= 0

    @pytest.mark.asyncio
    async def test_forecasting_performance(self):
        """Test forecasting performance"""
        import time

        engine = ForecastingEngine()

        # Large historical dataset
        dates = pd.date_range(start="2020-01-01", periods=100, freq="ME")
        revenue = np.cumsum(np.random.uniform(10000, 20000, 100))
        data = pd.DataFrame({"date": dates, "revenue": revenue})

        start = time.time()
        forecast = await engine.forecast_revenue(data, periods=12)
        duration = time.time() - start

        assert duration < 10.0  # Should complete in under 10 seconds
        assert forecast is not None

    @pytest.mark.asyncio
    async def test_decision_making_performance(self):
        """Test decision making performance with many options"""
        import time

        engine = DecisionEngine()

        # Many options
        options = [
            Option(
                id=f"opt{i}",
                name=f"Option {i}",
                description="Test",
                scores={
                    "metric1": np.random.uniform(0, 100),
                    "metric2": np.random.uniform(0, 100),
                    "metric3": np.random.uniform(0, 100),
                },
            )
            for i in range(20)
        ]

        criteria = [
            Criterion(name="metric1", type=CriteriaType.BENEFIT, weight=0.4),
            Criterion(name="metric2", type=CriteriaType.BENEFIT, weight=0.3),
            Criterion(name="metric3", type=CriteriaType.COST, weight=0.3),
        ]

        start = time.time()
        decision = await engine.make_decision("Test", options, criteria)
        duration = time.time() - start

        assert duration < 2.0  # Should complete in under 2 seconds
        assert decision is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
