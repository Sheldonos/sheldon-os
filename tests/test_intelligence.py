"""
Tests for Intelligence Module

Comprehensive test suite for pattern recognition, opportunity finding,
forecasting, decision making, and market analysis.
"""


import numpy as np
import pandas as pd
import pytest

from src.intelligence import (
    CriteriaType,
    Criterion,
    DecisionEngine,
    ForecastingEngine,
    ForecastModel,
    MarketAnalyzer,
    MarketSize,
    OpportunityFinder,
    OpportunityType,
    Option,
    PatternRecognitionEngine,
    PatternType,
)


class TestPatternRecognition:
    """Tests for Pattern Recognition Engine"""

    @pytest.fixture
    def pattern_engine(self):
        """Create pattern recognition engine"""
        return PatternRecognitionEngine()

    @pytest.mark.asyncio
    async def test_time_series_analysis(self, pattern_engine):
        """Test time series pattern detection"""
        # Create sample time series data
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
        values = np.sin(np.linspace(0, 4 * np.pi, 100)) + np.random.normal(
            0,
            0.1,
            100,
        )

        data = pd.DataFrame({"timestamp": dates, "value": values})

        patterns = await pattern_engine.analyze_time_series(
            data,
            value_column="value",
        )

        assert len(patterns) > 0
        assert all(p.type == PatternType.TEMPORAL for p in patterns)

    @pytest.mark.asyncio
    async def test_anomaly_detection(self, pattern_engine):
        """Test anomaly detection"""
        # Create data with anomalies
        normal_data = np.random.normal(100, 10, 95)
        anomalies = np.array([200, 250, 300, 50, 0])
        all_data = np.concatenate([normal_data, anomalies])

        data = pd.DataFrame(
            {"feature1": all_data, "feature2": np.random.normal(50, 5, 100)}
        )

        patterns = await pattern_engine.detect_anomalies(
            data, features=["feature1", "feature2"]
        )

        assert len(patterns) > 0
        assert patterns[0].type == PatternType.ANOMALY

    @pytest.mark.asyncio
    async def test_learn_from_outcomes(self, pattern_engine):
        """Test learning from outcomes"""
        outcomes = [
            {"feature1": "high", "feature2": "low", "success": True},
            {"feature1": "high", "feature2": "medium", "success": True},
            {"feature1": "low", "feature2": "high", "success": False},
            {"feature1": "low", "feature2": "low", "success": False},
        ]

        patterns = await pattern_engine.learn_from_outcomes(outcomes)

        assert len(patterns) >= 1
        success_patterns = [
            p for p in patterns if p.type == PatternType.SUCCESS
        ]
        assert len(success_patterns) > 0

    @pytest.mark.asyncio
    async def test_pattern_matching(self, pattern_engine):
        """Test pattern matching"""
        # First, learn some patterns
        outcomes = [
            {"metric1": 100, "metric2": 50, "success": True},
            {"metric1": 110, "metric2": 55, "success": True},
        ]

        await pattern_engine.learn_from_outcomes(outcomes)

        # Now match against new data
        new_data = {"metric1": 105, "metric2": 52}
        matches = await pattern_engine.match_pattern(new_data)

        # Should find matches if patterns were learned
        assert isinstance(matches, list)


class TestOpportunityFinder:
    """Tests for Opportunity Finder"""

    @pytest.fixture
    def opportunity_finder(self):
        """Create opportunity finder"""
        return OpportunityFinder()

    @pytest.mark.asyncio
    async def test_scan_market(self, opportunity_finder):
        """Test market scanning"""
        opportunities = await opportunity_finder.scan_market(
            industry="fintech",
            keywords=["payments", "blockchain", "digital wallet"],
        )

        assert isinstance(opportunities, list)
        if opportunities:
            opp = opportunities[0]
            assert hasattr(opp, "market_size")
            assert hasattr(opp, "confidence_score")
            assert hasattr(opp, "estimated_roi")

    @pytest.mark.asyncio
    async def test_rank_opportunities(self, opportunity_finder):
        """Test opportunity ranking"""
        # Create mock opportunities
        from src.intelligence.opportunity_finder import Opportunity, RiskLevel

        opp1 = Opportunity(
            id="opp1",
            title="Opportunity 1",
            description="Test",
            type=OpportunityType.MARKET_GAP,
            market="fintech",
            market_size=MarketSize(tam=1e9, sam=3e8, som=5e7),
            confidence_score=0.8,
            estimated_roi=5.0,
            time_to_market=12,
            risk_level=RiskLevel.MEDIUM,
            competitive_landscape=[],
            business_model="SaaS",
            key_insights=[],
            barriers_to_entry=[],
            success_factors=[],
        )

        opp2 = Opportunity(
            id="opp2",
            title="Opportunity 2",
            description="Test",
            type=OpportunityType.WHITE_SPACE,
            market="edtech",
            market_size=MarketSize(tam=5e8, sam=1.5e8, som=2.5e7),
            confidence_score=0.9,
            estimated_roi=8.0,
            time_to_market=18,
            risk_level=RiskLevel.LOW,
            competitive_landscape=[],
            business_model="Marketplace",
            key_insights=[],
            barriers_to_entry=[],
            success_factors=[],
        )

        ranked = await opportunity_finder.rank_opportunities([opp1, opp2])

        assert len(ranked) == 2
        assert all(isinstance(item, tuple) for item in ranked)
        assert ranked[0][1] >= ranked[1][1]  # Sorted by score

    @pytest.mark.asyncio
    async def test_generate_business_plan(self, opportunity_finder):
        """Test business plan generation"""
        from src.intelligence.opportunity_finder import Opportunity, RiskLevel

        opp = Opportunity(
            id="test_opp",
            title="Test Opportunity",
            description="Test description",
            type=OpportunityType.MARKET_GAP,
            market="test",
            market_size=MarketSize(tam=1e9, sam=3e8, som=5e7),
            confidence_score=0.8,
            estimated_roi=5.0,
            time_to_market=12,
            risk_level=RiskLevel.MEDIUM,
            competitive_landscape=[],
            business_model="SaaS",
            key_insights=["Insight 1"],
            barriers_to_entry=["Barrier 1"],
            success_factors=["Factor 1"],
        )

        plan = await opportunity_finder.generate_business_plan(opp)

        assert "executive_summary" in plan
        assert "market_analysis" in plan
        assert "business_model" in plan
        assert "go_to_market" in plan


class TestForecasting:
    """Tests for Forecasting Engine"""

    @pytest.fixture
    def forecasting_engine(self):
        """Create forecasting engine"""
        return ForecastingEngine()

    @pytest.mark.asyncio
    async def test_revenue_forecast(self, forecasting_engine):
        """Test revenue forecasting"""
        # Create sample revenue data
        dates = pd.date_range(start="2023-01-01", periods=24, freq="ME")
        revenue = np.cumsum(np.random.uniform(10000, 20000, 24))

        data = pd.DataFrame({"date": dates, "revenue": revenue})

        forecast = await forecasting_engine.forecast_revenue(
            data, periods=12, model=ForecastModel.LINEAR_REGRESSION
        )

        assert forecast is not None
        assert len(forecast.predictions) == 12
        assert forecast.current_value > 0
        assert forecast.accuracy_score >= 0

    @pytest.mark.asyncio
    async def test_scenario_analysis(self, forecasting_engine):
        """Test scenario analysis"""
        # Create sample data
        dates = pd.date_range(start="2023-01-01", periods=12, freq="ME")
        revenue = np.linspace(100000, 200000, 12)

        data = pd.DataFrame({"date": dates, "revenue": revenue})

        scenarios = [
            {
                "name": "Best Case",
                "description": "Optimistic scenario",
                "assumptions": {"growth_rate": 0.5},
                "probability": 0.2,
            },
            {
                "name": "Base Case",
                "description": "Expected scenario",
                "assumptions": {"growth_rate": 0.2},
                "probability": 0.6,
            },
            {
                "name": "Worst Case",
                "description": "Pessimistic scenario",
                "assumptions": {"growth_rate": -0.1},
                "probability": 0.2,
            },
        ]

        results = await forecasting_engine.scenario_analysis(
            data,
            scenarios,
            periods=6,
        )

        assert len(results) == 3
        assert all(hasattr(s, "forecast") for s in results)

    @pytest.mark.asyncio
    async def test_resource_forecasting(self, forecasting_engine):
        """Test resource requirement forecasting"""
        # Create revenue forecast first
        dates = pd.date_range(start="2023-01-01", periods=12, freq="ME")
        revenue = np.linspace(100000, 200000, 12)

        data = pd.DataFrame({"date": dates, "revenue": revenue})

        revenue_forecast = await forecasting_engine.forecast_revenue(
            data,
            periods=6,
        )

        # Forecast resources
        resource_ratios = {
            "headcount": 0.00001,  # 1 person per $100K revenue
            "infrastructure": 0.1,  # 10% of revenue
            "marketing": 0.2,  # 20% of revenue
        }

        resource_forecasts = (
            await forecasting_engine.forecast_resource_requirements(
                revenue_forecast,
                resource_ratios,
            )
        )

        assert len(resource_forecasts) == 3
        assert "headcount" in resource_forecasts
        assert "infrastructure" in resource_forecasts


class TestDecisionEngine:
    """Tests for Decision Engine"""

    @pytest.fixture
    def decision_engine(self):
        """Create decision engine"""
        return DecisionEngine()

    @pytest.mark.asyncio
    async def test_make_decision(self, decision_engine):
        """Test decision making"""
        # Create options
        options = [
            Option(
                id="opt1",
                name="Option 1",
                description="First option",
                scores={"cost": 100, "roi": 5.0, "time": 12, "risk": 0.3},
            ),
            Option(
                id="opt2",
                name="Option 2",
                description="Second option",
                scores={"cost": 150, "roi": 8.0, "time": 18, "risk": 0.5},
            ),
        ]

        # Create criteria
        criteria = [
            Criterion(name="cost", type=CriteriaType.COST, weight=0.3),
            Criterion(name="roi", type=CriteriaType.BENEFIT, weight=0.4),
            Criterion(name="time", type=CriteriaType.COST, weight=0.2),
            Criterion(name="risk", type=CriteriaType.COST, weight=0.1),
        ]

        decision = await decision_engine.make_decision(
            question="Which option should we pursue?",
            options=options,
            criteria=criteria,
        )

        assert decision is not None
        assert decision.recommended_option in options
        assert len(decision.scores) == 2
        assert decision.rationale.confidence > 0

    @pytest.mark.asyncio
    async def test_cost_benefit_analysis(self, decision_engine):
        """Test cost-benefit analysis"""
        option = Option(
            id="test",
            name="Test Option",
            description="Test",
            scores={"value": 100},
        )

        costs = {
            "development": 100000,
            "marketing": 50000,
            "operations": 30000,
        }

        benefits = {"revenue": 500000, "cost_savings": 100000}

        analysis = await decision_engine.cost_benefit_analysis(
            option, costs, benefits, time_horizon=24
        )

        assert analysis.total_costs == 180000
        assert analysis.total_benefits == 600000
        assert analysis.net_benefit == 420000
        assert analysis.roi > 0

    @pytest.mark.asyncio
    async def test_sensitivity_analysis(self, decision_engine):
        """Test sensitivity analysis"""
        # First make a decision
        options = [
            Option(
                id="opt1",
                name="Option 1",
                description="Test",
                scores={"metric1": 100, "metric2": 50},
            )
        ]

        criteria = [
            Criterion(name="metric1", type=CriteriaType.BENEFIT, weight=0.6),
            Criterion(name="metric2", type=CriteriaType.BENEFIT, weight=0.4),
        ]

        decision = await decision_engine.make_decision(
            "Test",
            options,
            criteria,
        )

        # Perform sensitivity analysis
        results = await decision_engine.sensitivity_analysis(
            decision,
            variable_criterion="metric1",
            value_range=(50, 150),
            steps=5,
        )

        assert "opt1" in results
        assert len(results["opt1"]) == 5


class TestMarketAnalyzer:
    """Tests for Market Analyzer"""

    @pytest.fixture
    async def market_analyzer(self):
        """Create market analyzer"""
        analyzer = MarketAnalyzer()
        async with analyzer:
            yield analyzer

    @pytest.mark.asyncio
    async def test_analyze_market(self, market_analyzer):
        """Test market analysis"""
        report = await market_analyzer.analyze_market(
            industry="fintech", keywords=["payments", "digital wallet"]
        )

        assert report is not None
        assert report.industry == "fintech"
        assert report.market_size > 0
        assert len(report.competitors) > 0
        assert report.swot is not None
        assert len(report.key_insights) > 0

    @pytest.mark.asyncio
    async def test_monitor_news(self, market_analyzer):
        """Test news monitoring"""
        articles = await market_analyzer.monitor_news(
            industry="fintech", keywords=["blockchain", "crypto"], days=7
        )

        assert isinstance(articles, list)

    def test_get_report_summary(self, market_analyzer):
        """Test report summary"""
        # This test doesn't require async
        # Would need to create a report first in real scenario
        summary = market_analyzer.get_report_summary("nonexistent")
        assert summary is None


class TestIntegration:
    """Integration tests for intelligence modules"""

    @pytest.mark.asyncio
    async def test_full_intelligence_pipeline(self):
        """Test complete intelligence pipeline"""
        # 1. Find opportunities
        opportunity_finder = OpportunityFinder()
        opportunities = await opportunity_finder.scan_market(
            industry="fintech", keywords=["payments"]
        )

        assert len(opportunities) > 0

        # 2. Forecast revenue for top opportunity
        if opportunities:
            forecasting_engine = ForecastingEngine()

            # Create sample historical data
            dates = pd.date_range(start="2023-01-01", periods=12, freq="ME")
            revenue = np.linspace(50000, 150000, 12)
            data = pd.DataFrame({"date": dates, "revenue": revenue})

            forecast = await forecasting_engine.forecast_revenue(
                data,
                periods=12,
            )
            assert forecast is not None

            # 3. Make decision
            decision_engine = DecisionEngine()

            options = [
                Option(
                    id="pursue",
                    name="Pursue Opportunity",
                    description="Go ahead with the opportunity",
                    scores={
                        "market_size": opportunities[0].market_size.tam / 1e9,
                        "roi": opportunities[0].estimated_roi,
                        "risk": 1.0 - opportunities[0].confidence_score,
                    },
                ),
                Option(
                    id="wait",
                    name="Wait",
                    description="Wait for better timing",
                    scores={"market_size": 0.5, "roi": 2.0, "risk": 0.2},
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
                    name="risk",
                    type=CriteriaType.COST,
                    weight=0.2,
                ),
            ]

            decision = await decision_engine.make_decision(
                "Should we pursue this opportunity?", options, criteria
            )

            assert decision is not None
            assert decision.recommended_option.id in ["pursue", "wait"]


@pytest.mark.asyncio
async def test_performance_benchmarks():
    """Test performance of intelligence modules"""
    import time

    # Pattern Recognition Performance
    pattern_engine = PatternRecognitionEngine()
    dates = pd.date_range(start="2023-01-01", periods=1000, freq="D")
    values = np.random.normal(100, 10, 1000)
    data = pd.DataFrame({"timestamp": dates, "value": values})

    start = time.time()
    await pattern_engine.analyze_time_series(data, "value")
    pattern_time = time.time() - start

    assert pattern_time < 5.0  # Should complete in under 5 seconds

    # Forecasting Performance
    forecasting_engine = ForecastingEngine()
    dates = pd.date_range(start="2023-01-01", periods=100, freq="ME")
    revenue = np.cumsum(np.random.uniform(10000, 20000, 100))
    data = pd.DataFrame({"date": dates, "revenue": revenue})

    start = time.time()
    await forecasting_engine.forecast_revenue(data, periods=12)
    forecast_time = time.time() - start

    assert forecast_time < 10.0  # Should complete in under 10 seconds


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
