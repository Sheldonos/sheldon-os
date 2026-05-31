"""
Intelligence Module for Sheldon OS.

This module provides the "brain" of Sheldon OS with sophisticated
pattern recognition, opportunity identification, forecasting,
decision-making, and market analysis capabilities.
"""

from .decision_engine import (
    CostBenefitAnalysis,
    CriteriaType,
    Criterion,
    Decision,
    DecisionEngine,
    DecisionRationale,
    DecisionType,
    Option,
)
from .forecasting import (
    ConfidenceInterval,
    Forecast,
    ForecastHorizon,
    ForecastingEngine,
    ForecastModel,
    ForecastPoint,
    Scenario,
)
from .market_analyzer import (
    CompetitorStrength,
    MarketAnalyzer,
    MarketReport,
    MarketTrend,
    MarketTrendData,
    RegulatoryEnvironment,
    SWOTAnalysis,
)
from .opportunity_finder import (
    Competitor,
    MarketSize,
    Opportunity,
    OpportunityFinder,
    OpportunityType,
    RiskLevel,
)
from .pattern_recognition import (
    Pattern,
    PatternMatch,
    PatternRecognitionEngine,
    PatternType,
)

__all__ = [
    # Pattern Recognition
    "PatternRecognitionEngine",
    "Pattern",
    "PatternType",
    "PatternMatch",
    # Opportunity Finding
    "OpportunityFinder",
    "Opportunity",
    "OpportunityType",
    "MarketSize",
    "Competitor",
    "RiskLevel",
    # Forecasting
    "ForecastingEngine",
    "Forecast",
    "ForecastModel",
    "ForecastHorizon",
    "ForecastPoint",
    "ConfidenceInterval",
    "Scenario",
    # Decision Making
    "DecisionEngine",
    "Decision",
    "DecisionType",
    "Option",
    "Criterion",
    "CriteriaType",
    "DecisionRationale",
    "CostBenefitAnalysis",
    # Market Analysis
    "MarketAnalyzer",
    "MarketReport",
    "MarketTrend",
    "MarketTrendData",
    "CompetitorStrength",
    "RegulatoryEnvironment",
    "SWOTAnalysis",
]

__version__ = "1.0.0"

# Made with Bob
