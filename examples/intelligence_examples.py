"""
Intelligence Module Usage Examples

This file demonstrates how to use the Sheldon OS Intelligence modules
for pattern recognition, opportunity finding, forecasting, decision making,
and market analysis.
"""

import asyncio
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from src.intelligence import (
    PatternRecognitionEngine,
    OpportunityFinder,
    ForecastingEngine,
    ForecastModel,
    DecisionEngine,
    Option,
    Criterion,
    CriteriaType,
    MarketAnalyzer
)


async def example_pattern_recognition():
    """Example: Pattern Recognition"""
    print("\n=== Pattern Recognition Example ===\n")
    
    # Initialize engine
    pattern_engine = PatternRecognitionEngine()
    
    # Example 1: Time Series Analysis
    print("1. Analyzing time series data...")
    dates = pd.date_range(start='2023-01-01', periods=365, freq='D')
    # Create data with trend and seasonality
    trend = np.linspace(100, 200, 365)
    seasonal = 20 * np.sin(np.linspace(0, 4*np.pi, 365))
    noise = np.random.normal(0, 5, 365)
    values = trend + seasonal + noise
    
    data = pd.DataFrame({
        'timestamp': dates,
        'revenue': values
    })
    
    patterns = await pattern_engine.analyze_time_series(data, 'revenue')
    print(f"   Found {len(patterns)} temporal patterns")
    for pattern in patterns:
        print(f"   - {pattern.description} (confidence: {pattern.confidence:.2f})")
    
    # Example 2: Anomaly Detection
    print("\n2. Detecting anomalies...")
    normal_data = np.random.normal(100, 10, 95)
    anomalies = np.array([200, 250, 300, 50, 0])
    all_data = np.concatenate([normal_data, anomalies])
    
    anomaly_data = pd.DataFrame({
        'metric1': all_data,
        'metric2': np.random.normal(50, 5, 100)
    })
    
    anomaly_patterns = await pattern_engine.detect_anomalies(
        anomaly_data,
        features=['metric1', 'metric2']
    )
    print(f"   Detected {len(anomaly_patterns)} anomaly patterns")
    
    # Example 3: Learning from Outcomes
    print("\n3. Learning from historical outcomes...")
    outcomes = [
        {'strategy': 'aggressive', 'market': 'growing', 'success': True},
        {'strategy': 'aggressive', 'market': 'stable', 'success': True},
        {'strategy': 'conservative', 'market': 'declining', 'success': True},
        {'strategy': 'aggressive', 'market': 'declining', 'success': False},
        {'strategy': 'conservative', 'market': 'growing', 'success': False},
    ]
    
    learned_patterns = await pattern_engine.learn_from_outcomes(outcomes)
    print(f"   Learned {len(learned_patterns)} patterns from outcomes")
    for pattern in learned_patterns:
        print(f"   - {pattern.type.value}: {pattern.description}")
    
    # Get statistics
    stats = await pattern_engine.get_pattern_statistics()
    print(f"\n   Total patterns in memory: {stats['total_patterns']}")


async def example_opportunity_finding():
    """Example: Opportunity Finding"""
    print("\n=== Opportunity Finding Example ===\n")
    
    # Initialize finder
    opportunity_finder = OpportunityFinder()
    
    # Example 1: Scan Market
    print("1. Scanning fintech market...")
    opportunities = await opportunity_finder.scan_market(
        industry="fintech",
        keywords=["payments", "blockchain", "digital wallet", "neobank"],
        depth="medium"
    )
    
    print(f"   Discovered {len(opportunities)} opportunities")
    for i, opp in enumerate(opportunities[:3], 1):
        print(f"\n   Opportunity {i}: {opp.title}")
        print(f"   - Market Size: ${opp.market_size.tam/1e9:.1f}B TAM")
        print(f"   - Estimated ROI: {opp.estimated_roi:.1f}x")
        print(f"   - Confidence: {opp.confidence_score:.0%}")
        print(f"   - Time to Market: {opp.time_to_market} months")
        print(f"   - Risk Level: {opp.risk_level.value}")
    
    # Example 2: Rank Opportunities
    if opportunities:
        print("\n2. Ranking opportunities...")
        ranked = await opportunity_finder.rank_opportunities(
            opportunities,
            criteria={
                "market_size": 0.3,
                "roi": 0.3,
                "confidence": 0.2,
                "time_to_market": 0.1,
                "risk": 0.1
            }
        )
        
        print("   Top 3 opportunities by score:")
        for i, (opp, score) in enumerate(ranked[:3], 1):
            print(f"   {i}. {opp.title} (score: {score:.3f})")
    
    # Example 3: Generate Business Plan
    if opportunities:
        print("\n3. Generating business plan for top opportunity...")
        top_opportunity = opportunities[0]
        business_plan = await opportunity_finder.generate_business_plan(top_opportunity)
        
        print(f"   Business Plan for: {business_plan['executive_summary']['title']}")
        print(f"   Market Size: ${business_plan['market_analysis']['market_size']['tam']/1e9:.1f}B")
        print(f"   Business Model: {business_plan['business_model']['model']}")
        print(f"   Key Insights:")
        for insight in business_plan['market_analysis']['key_insights'][:3]:
            print(f"   - {insight}")


async def example_forecasting():
    """Example: Forecasting"""
    print("\n=== Forecasting Example ===\n")
    
    # Initialize engine
    forecasting_engine = ForecastingEngine()
    
    # Example 1: Revenue Forecasting
    print("1. Forecasting revenue...")
    dates = pd.date_range(start='2023-01-01', periods=24, freq='M')
    # Create realistic revenue growth
    base_revenue = 50000
    growth_rate = 0.15
    revenue = [base_revenue * (1 + growth_rate) ** i for i in range(24)]
    revenue = np.array(revenue) + np.random.normal(0, 5000, 24)
    
    historical_data = pd.DataFrame({
        'date': dates,
        'revenue': revenue
    })
    
    forecast = await forecasting_engine.forecast_revenue(
        historical_data,
        periods=12,
        model=ForecastModel.ENSEMBLE
    )
    
    print(f"   Current Revenue: ${forecast.current_value:,.0f}")
    print(f"   Model Used: {forecast.model_used}")
    print(f"   Accuracy Score: {forecast.accuracy_score:.2%}")
    print(f"\n   12-Month Forecast:")
    for i, pred in enumerate(forecast.predictions[:6], 1):
        print(f"   Month {i}: ${pred.value:,.0f} "
              f"(${pred.confidence_interval.lower:,.0f} - ${pred.confidence_interval.upper:,.0f})")
    
    # Example 2: Scenario Analysis
    print("\n2. Performing scenario analysis...")
    scenarios = [
        {
            'name': 'Best Case',
            'description': 'Aggressive growth with market expansion',
            'assumptions': {'growth_rate': 0.5},
            'probability': 0.2
        },
        {
            'name': 'Base Case',
            'description': 'Expected growth trajectory',
            'assumptions': {'growth_rate': 0.2},
            'probability': 0.6
        },
        {
            'name': 'Worst Case',
            'description': 'Market challenges and competition',
            'assumptions': {'growth_rate': 0.0},
            'probability': 0.2
        }
    ]
    
    scenario_results = await forecasting_engine.scenario_analysis(
        historical_data,
        scenarios,
        periods=12
    )
    
    print("   Scenario Forecasts (12 months out):")
    for scenario in scenario_results:
        final_value = scenario.forecast.predictions[-1].value
        print(f"   - {scenario.name}: ${final_value:,.0f} "
              f"(probability: {scenario.probability:.0%})")
    
    # Example 3: Resource Forecasting
    print("\n3. Forecasting resource requirements...")
    resource_ratios = {
        'headcount': 0.00001,  # 1 person per $100K revenue
        'infrastructure_cost': 0.15,  # 15% of revenue
        'marketing_budget': 0.25  # 25% of revenue
    }
    
    resource_forecasts = await forecasting_engine.forecast_resource_requirements(
        forecast,
        resource_ratios
    )
    
    print("   Resource Requirements (12 months out):")
    for resource, resource_forecast in resource_forecasts.items():
        final_value = resource_forecast.predictions[-1].value
        if resource == 'headcount':
            print(f"   - {resource}: {int(final_value)} people")
        else:
            print(f"   - {resource}: ${final_value:,.0f}")


async def example_decision_making():
    """Example: Decision Making"""
    print("\n=== Decision Making Example ===\n")
    
    # Initialize engine
    decision_engine = DecisionEngine()
    
    # Example 1: Strategic Decision
    print("1. Making strategic decision: Which product to build?")
    
    options = [
        Option(
            id="product_a",
            name="Enterprise AI Traceability",
            description="AI monitoring for enterprises",
            scores={
                'market_size': 10.0,  # $10B TAM
                'time_to_market': 12,  # months
                'development_cost': 2.0,  # $2M
                'estimated_roi': 15.0,  # 15x
                'competitive_intensity': 0.3,  # Low
                'technical_risk': 0.4  # Medium
            },
            metadata={'risk_level': 'medium'}
        ),
        Option(
            id="product_b",
            name="Autonomous Business Platform",
            description="AI agents for solopreneurs",
            scores={
                'market_size': 5.0,  # $5B TAM
                'time_to_market': 16,  # months
                'development_cost': 3.0,  # $3M
                'estimated_roi': 20.0,  # 20x
                'competitive_intensity': 0.2,  # Very low
                'technical_risk': 0.6  # High
            },
            metadata={'risk_level': 'high'}
        ),
        Option(
            id="product_c",
            name="Right.ai Platform",
            description="Pay-per-use AI marketplace",
            scores={
                'market_size': 8.0,  # $8B TAM
                'time_to_market': 18,  # months
                'development_cost': 4.0,  # $4M
                'estimated_roi': 25.0,  # 25x
                'competitive_intensity': 0.5,  # Medium
                'technical_risk': 0.5  # Medium
            },
            metadata={'risk_level': 'medium', 'time_to_market': 18}
        )
    ]
    
    criteria = [
        Criterion(
            name='market_size',
            type=CriteriaType.BENEFIT,
            weight=0.25,
            description='Total addressable market size'
        ),
        Criterion(
            name='time_to_market',
            type=CriteriaType.COST,
            weight=0.15,
            description='Time to launch product'
        ),
        Criterion(
            name='development_cost',
            type=CriteriaType.COST,
            weight=0.15,
            description='Development investment required'
        ),
        Criterion(
            name='estimated_roi',
            type=CriteriaType.BENEFIT,
            weight=0.25,
            description='Expected return on investment'
        ),
        Criterion(
            name='competitive_intensity',
            type=CriteriaType.COST,
            weight=0.10,
            description='Level of competition'
        ),
        Criterion(
            name='technical_risk',
            type=CriteriaType.COST,
            weight=0.10,
            description='Technical execution risk'
        )
    ]
    
    decision = await decision_engine.make_decision(
        question="Which product should we build first?",
        options=options,
        criteria=criteria,
        method="topsis"
    )
    
    print(f"\n   Recommendation: {decision.recommended_option.name}")
    print(f"   Confidence: {decision.rationale.confidence:.0%}")
    print(f"\n   Reasoning:")
    for reason in decision.rationale.reasoning:
        print(f"   - {reason}")
    
    if decision.rationale.trade_offs:
        print(f"\n   Trade-offs:")
        for tradeoff in decision.rationale.trade_offs:
            print(f"   - {tradeoff}")
    
    print(f"\n   All Options Ranked:")
    sorted_scores = sorted(decision.scores.items(), key=lambda x: x[1], reverse=True)
    for i, (opt_id, score) in enumerate(sorted_scores, 1):
        opt = next(o for o in options if o.id == opt_id)
        print(f"   {i}. {opt.name}: {score:.3f}")
    
    # Example 2: Cost-Benefit Analysis
    print("\n2. Performing cost-benefit analysis...")
    
    costs = {
        'development': 2_000_000,
        'marketing': 500_000,
        'operations': 300_000,
        'hiring': 800_000
    }
    
    benefits = {
        'year1_revenue': 3_000_000,
        'year2_revenue': 8_000_000,
        'year3_revenue': 15_000_000,
        'cost_savings': 500_000
    }
    
    cba = await decision_engine.cost_benefit_analysis(
        decision.recommended_option,
        costs,
        benefits,
        discount_rate=0.10,
        time_horizon=36
    )
    
    print(f"   Total Costs: ${cba.total_costs:,.0f}")
    print(f"   Total Benefits: ${cba.total_benefits:,.0f}")
    print(f"   Net Benefit: ${cba.net_benefit:,.0f}")
    print(f"   ROI: {cba.roi:.1f}x")
    print(f"   Payback Period: {cba.payback_period:.1f} months")
    print(f"   NPV: ${cba.npv:,.0f}")
    print(f"   IRR: {cba.irr*100:.1f}% annually")


async def example_market_analysis():
    """Example: Market Analysis"""
    print("\n=== Market Analysis Example ===\n")
    
    # Initialize analyzer
    async with MarketAnalyzer() as market_analyzer:
        
        # Example 1: Comprehensive Market Analysis
        print("1. Analyzing fintech market...")
        report = await market_analyzer.analyze_market(
            industry="fintech",
            keywords=["payments", "digital banking", "blockchain"],
            depth="medium"
        )
        
        print(f"\n   Market Report: {report.industry.upper()}")
        print(f"   Market Size: ${report.market_size/1e9:.1f}B")
        print(f"   Growth Rate: {report.growth_rate*100:.1f}% CAGR")
        print(f"   Trend: {report.trend.trend.value}")
        
        print(f"\n   Competitors ({len(report.competitors)}):")
        for comp in report.competitors[:3]:
            print(f"   - {comp.name}: {comp.market_share*100:.1f}% market share ({comp.strength.value})")
        
        print(f"\n   Regulatory Environment:")
        print(f"   - Jurisdiction: {report.regulatory_environment.jurisdiction}")
        print(f"   - Complexity: {report.regulatory_environment.complexity}")
        
        print(f"\n   SWOT Analysis:")
        print(f"   Strengths: {len(report.swot.strengths)}")
        for s in report.swot.strengths[:2]:
            print(f"   - {s}")
        print(f"   Opportunities: {len(report.swot.opportunities)}")
        for o in report.swot.opportunities[:2]:
            print(f"   - {o}")
        
        print(f"\n   Key Insights:")
        for insight in report.key_insights:
            print(f"   - {insight}")
        
        print(f"\n   Recommendations:")
        for rec in report.recommendations[:3]:
            print(f"   - {rec}")
        
        # Example 2: Monitor News
        print("\n2. Monitoring industry news...")
        articles = await market_analyzer.monitor_news(
            industry="fintech",
            keywords=["AI", "automation", "regulation"],
            days=7
        )
        
        print(f"   Found {len(articles)} relevant articles")
        for article in articles[:3]:
            print(f"   - {article['title']} ({article['sentiment']})")


async def example_integrated_workflow():
    """Example: Integrated Intelligence Workflow"""
    print("\n=== Integrated Intelligence Workflow ===\n")
    print("Demonstrating how all intelligence modules work together...\n")
    
    # Step 1: Find Opportunities
    print("Step 1: Discovering market opportunities...")
    opportunity_finder = OpportunityFinder()
    opportunities = await opportunity_finder.scan_market(
        industry="fintech",
        keywords=["AI", "automation", "compliance"]
    )
    print(f"   ✓ Found {len(opportunities)} opportunities")
    
    # Step 2: Analyze Market
    print("\nStep 2: Analyzing market conditions...")
    async with MarketAnalyzer() as market_analyzer:
        market_report = await market_analyzer.analyze_market(
            industry="fintech",
            keywords=["AI", "compliance"]
        )
    print(f"   ✓ Market size: ${market_report.market_size/1e9:.1f}B")
    print(f"   ✓ Growth rate: {market_report.growth_rate*100:.1f}%")
    
    # Step 3: Forecast Revenue
    print("\nStep 3: Forecasting potential revenue...")
    forecasting_engine = ForecastingEngine()
    
    # Create projected revenue based on opportunity
    dates = pd.date_range(start='2024-01-01', periods=12, freq='M')
    projected_revenue = np.linspace(100000, 500000, 12)
    data = pd.DataFrame({'date': dates, 'revenue': projected_revenue})
    
    forecast = await forecasting_engine.forecast_revenue(data, periods=12)
    print(f"   ✓ 12-month forecast: ${forecast.predictions[-1].value:,.0f}")
    
    # Step 4: Make Strategic Decision
    print("\nStep 4: Making go/no-go decision...")
    decision_engine = DecisionEngine()
    
    if opportunities:
        top_opp = opportunities[0]
        
        options = [
            Option(
                id="go",
                name="Pursue Opportunity",
                description="Launch the product",
                scores={
                    'market_size': top_opp.market_size.tam / 1e9,
                    'roi': top_opp.estimated_roi,
                    'confidence': top_opp.confidence_score,
                    'risk': 1.0 - top_opp.confidence_score
                }
            ),
            Option(
                id="no_go",
                name="Pass on Opportunity",
                description="Wait for better timing",
                scores={
                    'market_size': 0.0,
                    'roi': 0.0,
                    'confidence': 1.0,
                    'risk': 0.0
                }
            )
        ]
        
        criteria = [
            Criterion(name='market_size', type=CriteriaType.BENEFIT, weight=0.3),
            Criterion(name='roi', type=CriteriaType.BENEFIT, weight=0.3),
            Criterion(name='confidence', type=CriteriaType.BENEFIT, weight=0.2),
            Criterion(name='risk', type=CriteriaType.COST, weight=0.2)
        ]
        
        decision = await decision_engine.make_decision(
            "Should we pursue this opportunity?",
            options,
            criteria
        )
        
        print(f"   ✓ Decision: {decision.recommended_option.name}")
        print(f"   ✓ Confidence: {decision.rationale.confidence:.0%}")
    
    print("\n✅ Integrated workflow complete!")
    print("\nThe intelligence system has:")
    print("  • Discovered market opportunities")
    print("  • Analyzed market conditions")
    print("  • Forecasted potential outcomes")
    print("  • Made strategic recommendations")


async def main():
    """Run all examples"""
    print("=" * 70)
    print("SHELDON OS INTELLIGENCE MODULE EXAMPLES")
    print("=" * 70)
    
    await example_pattern_recognition()
    await example_opportunity_finding()
    await example_forecasting()
    await example_decision_making()
    await example_market_analysis()
    await example_integrated_workflow()
    
    print("\n" + "=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
