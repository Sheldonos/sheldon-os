"""
Opportunity Finder for Sheldon OS

This module autonomously discovers market opportunities by analyzing markets,
identifying gaps, evaluating competitive landscapes, and scoring opportunities
by potential ROI. Inspired by the Polymarket/Kalshi discovery approach.
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class OpportunityType(Enum):
    """Types of business opportunities"""

    MARKET_GAP = "market_gap"  # Underserved market segment
    WHITE_SPACE = "white_space"  # Uncontested market space
    DISRUPTION = "disruption"  # Opportunity to disrupt existing market
    TREND = "trend"  # Emerging trend opportunity
    ARBITRAGE = "arbitrage"  # Market inefficiency
    PLATFORM = "platform"  # Platform/marketplace opportunity


class RiskLevel(Enum):
    """Risk levels for opportunities"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class MarketSize:
    """Market size estimates"""

    tam: float  # Total Addressable Market
    sam: float  # Serviceable Addressable Market
    som: float  # Serviceable Obtainable Market
    currency: str = "USD"
    year: int = field(default_factory=lambda: datetime.utcnow().year)
    growth_rate: float = 0.0  # Annual growth rate (CAGR)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tam": self.tam,
            "sam": self.sam,
            "som": self.som,
            "currency": self.currency,
            "year": self.year,
            "growth_rate": self.growth_rate,
        }


@dataclass
class Competitor:
    """Competitor information"""

    name: str
    market_share: float  # 0.0 to 1.0
    strengths: List[str]
    weaknesses: List[str]
    funding: Optional[float] = None
    valuation: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "market_share": self.market_share,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "funding": self.funding,
            "valuation": self.valuation,
        }


@dataclass
class Opportunity:
    """Represents a business opportunity"""

    id: str
    title: str
    description: str
    type: OpportunityType
    market: str
    market_size: MarketSize
    confidence_score: float  # 0.0 to 1.0
    estimated_roi: float  # Expected return multiple
    time_to_market: int  # Months
    risk_level: RiskLevel
    competitive_landscape: List[Competitor]
    business_model: str
    key_insights: List[str]
    barriers_to_entry: List[str]
    success_factors: List[str]
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "type": self.type.value,
            "market": self.market,
            "market_size": self.market_size.to_dict(),
            "confidence_score": self.confidence_score,
            "estimated_roi": self.estimated_roi,
            "time_to_market": self.time_to_market,
            "risk_level": self.risk_level.value,
            "competitive_landscape": [
                c.to_dict() for c in self.competitive_landscape
            ],
            "business_model": self.business_model,
            "key_insights": self.key_insights,
            "barriers_to_entry": self.barriers_to_entry,
            "success_factors": self.success_factors,
            "discovered_at": self.discovered_at.isoformat(),
            "metadata": self.metadata,
        }

    def calculate_score(self) -> float:
        """Calculate overall opportunity score"""
        # Weighted scoring
        market_score = (
            min(self.market_size.tam / 1e9, 1.0) * 0.25
        )  # Normalize to billions
        roi_score = (
            min(self.estimated_roi / 10, 1.0) * 0.25
        )  # Normalize to 10x
        confidence_score = self.confidence_score * 0.20
        time_score = (
            max(0, 1 - (self.time_to_market / 36)) * 0.15
        )  # Prefer faster TTM
        risk_score = (1 - self._risk_to_score()) * 0.15

        return (
            market_score
            + roi_score
            + confidence_score
            + time_score
            + risk_score
        )

    def _risk_to_score(self) -> float:
        """Convert risk level to score (0-1)"""
        risk_map = {
            RiskLevel.LOW: 0.2,
            RiskLevel.MEDIUM: 0.4,
            RiskLevel.HIGH: 0.7,
            RiskLevel.VERY_HIGH: 0.9,
        }
        return risk_map.get(self.risk_level, 0.5)


class OpportunityFinder:
    """
    Autonomous opportunity discovery system that scans markets,
    identifies gaps, and evaluates business opportunities.
    """

    def __init__(self, memory_system=None, pattern_engine=None):
        """
        Initialize the opportunity finder

        Args:
            memory_system: Optional memory system for storing opportunities
            pattern_engine: Optional pattern recognition engine
        """
        self.memory_system = memory_system
        self.pattern_engine = pattern_engine
        self.opportunities: Dict[str, Opportunity] = {}

        # Configuration
        self.min_confidence = 0.6
        self.min_tam = 100_000_000  # $100M minimum TAM

        logger.info("Opportunity Finder initialized")

    async def scan_market(
        self, industry: str, keywords: List[str], depth: str = "medium"
    ) -> List[Opportunity]:
        """
        Scan a market for opportunities

        Args:
            industry: Industry to scan (e.g., "fintech", "edtech")
            keywords: Keywords to search for
            depth: Scan depth ("shallow", "medium", "deep")

        Returns:
            List of discovered opportunities
        """
        opportunities = []

        try:
            logger.info(
                "Scanning %s market with keywords: %s",
                industry,
                keywords,
            )

            # Analyze market trends
            trends = await self._analyze_trends(industry, keywords)

            # Identify market gaps
            gaps = await self._identify_gaps(industry, trends)

            # Evaluate each gap as an opportunity
            for gap in gaps:
                opportunity = await self._evaluate_gap(gap, industry)
                if (
                    opportunity
                    and opportunity.confidence_score >= self.min_confidence
                ):
                    opportunities.append(opportunity)
                    await self._store_opportunity(opportunity)

            # Sort by score
            opportunities.sort(key=lambda o: o.calculate_score(), reverse=True)

            logger.info(
                "Discovered %d opportunities in %s",
                len(opportunities),
                industry,
            )
            return opportunities

        except Exception as e:
            logger.error(f"Error scanning market: {e}")
            return []

    async def _analyze_trends(
        self, industry: str, keywords: List[str]
    ) -> Dict[str, Any]:
        """Analyze market trends using web data"""
        trends: Dict[str, Any] = {
            "search_volume": {},
            "social_mentions": {},
            "news_sentiment": {},
            "growth_indicators": [],
        }

        try:
            # Simulate trend analysis
            # (in production, use Google Trends API, etc.)
            for keyword in keywords:
                # Mock data - replace with actual API calls
                trends["search_volume"][keyword] = np.random.randint(
                    1000,
                    100000,
                )
                trends["social_mentions"][keyword] = np.random.randint(
                    500,
                    50000,
                )
                trends["news_sentiment"][keyword] = np.random.uniform(-1, 1)

            # Identify growth indicators
            for keyword, volume in trends["search_volume"].items():
                if volume > 50000:
                    trends["growth_indicators"].append(
                        {
                            "keyword": keyword,
                            "signal": "high_search_volume",
                            "strength": "strong",
                        }
                    )

            logger.debug(
                "Analyzed trends for %s: %d indicators",
                industry,
                len(trends["growth_indicators"]),
            )
            return trends

        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return trends

    async def _identify_gaps(
        self, industry: str, trends: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify market gaps based on trends"""
        gaps = []

        try:
            # Analyze search volume vs competition
            for keyword, volume in trends["search_volume"].items():
                # High search volume + low competition = gap
                if volume > 30000:
                    gap = {
                        "keyword": keyword,
                        "type": "underserved",
                        "demand_signal": volume,
                        "competition_level": "low",  # Simplified
                        "opportunity_score": 0.8,
                    }
                    gaps.append(gap)

            # Analyze sentiment gaps
            for keyword, sentiment in trends["news_sentiment"].items():
                if sentiment < -0.3:  # Negative sentiment = pain point
                    gap = {
                        "keyword": keyword,
                        "type": "pain_point",
                        "sentiment": sentiment,
                        "opportunity_score": 0.7,
                    }
                    gaps.append(gap)

            if not gaps and trends["search_volume"]:
                fallback_keyword, fallback_volume = max(
                    trends["search_volume"].items(),
                    key=lambda item: item[1],
                )
                gaps.append(
                    {
                        "keyword": fallback_keyword,
                        "type": "trend",
                        "demand_signal": fallback_volume,
                        "competition_level": "medium",
                        "opportunity_score": 0.65,
                    }
                )

            logger.debug("Identified %d market gaps", len(gaps))
            return gaps

        except Exception as e:
            logger.error(f"Error identifying gaps: {e}")
            return []

    async def _evaluate_gap(
        self, gap: Dict[str, Any], industry: str
    ) -> Optional[Opportunity]:
        """Evaluate a market gap as a business opportunity"""
        try:
            # Generate opportunity ID
            opp_id = hashlib.md5(
                (
                    f"{industry}_{gap['keyword']}_"
                    f"{datetime.utcnow().timestamp()}"
                ).encode()
            ).hexdigest()[:16]

            # Estimate market size
            market_size = await self._estimate_market_size(industry, gap)

            # Analyze competition
            competitors = await self._analyze_competition(industry, gap)

            # Determine opportunity type
            opp_type = self._determine_opportunity_type(gap, competitors)

            # Calculate confidence and ROI
            confidence = self._calculate_confidence(
                gap,
                market_size,
                competitors,
            )
            estimated_roi = self._estimate_roi(gap, market_size, competitors)

            # Determine risk level
            risk_level = self._assess_risk(gap, market_size, competitors)

            # Generate business model hypothesis
            business_model = self._generate_business_model(gap, opp_type)

            # Extract insights
            insights = self._extract_insights(gap, market_size, competitors)

            opportunity = Opportunity(
                id=opp_id,
                title=f"{gap['keyword'].title()} Opportunity in {industry}",
                description=(
                    f"Market gap identified in {industry} "
                    f"for {gap['keyword']}"
                ),
                type=opp_type,
                market=industry,
                market_size=market_size,
                confidence_score=confidence,
                estimated_roi=estimated_roi,
                time_to_market=self._estimate_time_to_market(opp_type),
                risk_level=risk_level,
                competitive_landscape=competitors,
                business_model=business_model,
                key_insights=insights,
                barriers_to_entry=self._identify_barriers(
                    industry,
                    competitors,
                ),
                success_factors=self._identify_success_factors(
                    gap,
                    opp_type,
                ),
                metadata={
                    "gap_data": gap,
                    "discovery_method": "trend_analysis",
                },
            )

            return opportunity

        except Exception as e:
            logger.error(f"Error evaluating gap: {e}")
            return None

    async def _estimate_market_size(
        self, industry: str, gap: Dict[str, Any]
    ) -> MarketSize:
        """Estimate TAM/SAM/SOM for opportunity"""
        # Simplified estimation - in production, use market research APIs
        base_tam = gap.get("demand_signal", 10000) * 1000  # Scale up

        return MarketSize(
            tam=float(base_tam),
            sam=float(base_tam * 0.3),  # 30% serviceable
            som=float(base_tam * 0.05),  # 5% obtainable
            growth_rate=0.15,  # 15% CAGR assumption
        )

    async def _analyze_competition(
        self, industry: str, gap: Dict[str, Any]
    ) -> List[Competitor]:
        """Analyze competitive landscape"""
        # Simplified - in production, scrape competitor data
        competitors = []

        # Mock competitor data
        if gap.get("competition_level") == "low":
            competitors.append(
                Competitor(
                    name="Generic Competitor",
                    market_share=0.15,
                    strengths=["Established brand"],
                    weaknesses=["Legacy technology", "Poor UX"],
                    funding=5_000_000,
                )
            )

        return competitors

    def _determine_opportunity_type(
        self, gap: Dict[str, Any], competitors: List[Competitor]
    ) -> OpportunityType:
        """Determine the type of opportunity"""
        if gap.get("type") == "underserved":
            return OpportunityType.MARKET_GAP
        elif len(competitors) == 0:
            return OpportunityType.WHITE_SPACE
        elif gap.get("type") == "pain_point":
            return OpportunityType.DISRUPTION
        else:
            return OpportunityType.TREND

    def _calculate_confidence(
        self,
        gap: Dict[str, Any],
        market_size: MarketSize,
        competitors: List[Competitor],
    ) -> float:
        """Calculate confidence score for opportunity"""
        # Base confidence from gap score
        confidence = gap.get("opportunity_score", 0.5)

        # Adjust for market size
        if market_size.tam > 1_000_000_000:  # $1B+
            confidence += 0.1

        # Adjust for competition
        if len(competitors) < 3:
            confidence += 0.1

        return float(min(1.0, confidence))

    def _estimate_roi(
        self,
        gap: Dict[str, Any],
        market_size: MarketSize,
        competitors: List[Competitor],
    ) -> float:
        """Estimate potential ROI multiple"""
        # Base ROI on market size and competition
        base_roi = 3.0

        # Large market bonus
        if market_size.tam > 1_000_000_000:
            base_roi += 2.0

        # Low competition bonus
        if len(competitors) < 2:
            base_roi += 1.5

        # High growth bonus
        if market_size.growth_rate > 0.20:
            base_roi += 1.0

        return base_roi

    def _assess_risk(
        self,
        gap: Dict[str, Any],
        market_size: MarketSize,
        competitors: List[Competitor],
    ) -> RiskLevel:
        """Assess risk level for opportunity"""
        risk_score = 0

        # Market size risk
        if market_size.tam < 100_000_000:
            risk_score += 2

        # Competition risk
        if len(competitors) > 5:
            risk_score += 2

        # Execution risk
        if gap.get("type") == "disruption":
            risk_score += 1

        # Map score to risk level
        if risk_score <= 1:
            return RiskLevel.LOW
        elif risk_score <= 3:
            return RiskLevel.MEDIUM
        elif risk_score <= 5:
            return RiskLevel.HIGH
        else:
            return RiskLevel.VERY_HIGH

    def _generate_business_model(
        self, gap: Dict[str, Any], opp_type: OpportunityType
    ) -> str:
        """Generate business model hypothesis"""
        models = {
            OpportunityType.MARKET_GAP: (
                "SaaS subscription with freemium tier"
            ),
            OpportunityType.WHITE_SPACE: (
                "Platform marketplace with transaction fees"
            ),
            OpportunityType.DISRUPTION: (
                "Direct-to-consumer with subscription"
            ),
            OpportunityType.TREND: "Usage-based pricing model",
            OpportunityType.ARBITRAGE: "Commission-based marketplace",
            OpportunityType.PLATFORM: (
                "Multi-sided platform with network effects"
            ),
        }
        return models.get(opp_type, "Subscription-based model")

    def _extract_insights(
        self,
        gap: Dict[str, Any],
        market_size: MarketSize,
        competitors: List[Competitor],
    ) -> List[str]:
        """Extract key insights about the opportunity"""
        insights = []

        if market_size.tam > 1_000_000_000:
            insights.append(
                f"Large market opportunity (${market_size.tam / 1e9:.1f}B TAM)"
            )

        if len(competitors) < 3:
            insights.append("Low competition - early mover advantage possible")

        if market_size.growth_rate > 0.20:
            insights.append(
                "High growth market "
                f"({market_size.growth_rate * 100:.0f}% CAGR)"
            )

        if gap.get("demand_signal", 0) > 50000:
            insights.append("Strong demand signals from market research")

        return insights

    def _identify_barriers(
        self, industry: str, competitors: List[Competitor]
    ) -> List[str]:
        """Identify barriers to entry"""
        barriers = []

        if len(competitors) > 5:
            barriers.append("Crowded market with established players")

        if industry in ["fintech", "healthcare", "insurance"]:
            barriers.append("Regulatory compliance requirements")

        barriers.append("Customer acquisition costs")
        barriers.append("Building brand trust")

        return barriers

    def _identify_success_factors(
        self, gap: Dict[str, Any], opp_type: OpportunityType
    ) -> List[str]:
        """Identify critical success factors"""
        factors = [
            "Product-market fit validation",
            "Efficient customer acquisition",
            "Strong unit economics",
        ]

        if opp_type == OpportunityType.PLATFORM:
            factors.append("Network effects and marketplace liquidity")

        if opp_type == OpportunityType.DISRUPTION:
            factors.append("Superior user experience")
            factors.append("10x better value proposition")

        return factors

    def _estimate_time_to_market(self, opp_type: OpportunityType) -> int:
        """Estimate time to market in months"""
        ttm_map = {
            OpportunityType.MARKET_GAP: 12,
            OpportunityType.WHITE_SPACE: 18,
            OpportunityType.DISRUPTION: 24,
            OpportunityType.TREND: 9,
            OpportunityType.ARBITRAGE: 6,
            OpportunityType.PLATFORM: 18,
        }
        return ttm_map.get(opp_type, 12)

    async def _store_opportunity(self, opportunity: Opportunity) -> None:
        """Store opportunity in memory system"""
        try:
            self.opportunities[opportunity.id] = opportunity

            if self.memory_system:
                await self.memory_system.store_long_term(
                    key=f"opportunity:{opportunity.id}",
                    value=opportunity.to_dict(),
                    metadata={
                        "type": "opportunity",
                        "market": opportunity.market,
                        "score": opportunity.calculate_score(),
                    },
                )

            logger.debug(f"Stored opportunity: {opportunity.id}")

        except Exception as e:
            logger.error(f"Error storing opportunity: {e}")

    async def rank_opportunities(
        self,
        opportunities: List[Opportunity],
        criteria: Optional[Dict[str, float]] = None,
    ) -> List[Tuple[Opportunity, float]]:
        """
        Rank opportunities by custom criteria

        Args:
            opportunities: List of opportunities to rank
            criteria: Optional custom weights for ranking

        Returns:
            List of (opportunity, score) tuples sorted by score
        """
        if not criteria:
            # Default criteria weights
            criteria = {
                "market_size": 0.3,
                "roi": 0.25,
                "confidence": 0.2,
                "time_to_market": 0.15,
                "risk": 0.1,
            }

        ranked = []

        for opp in opportunities:
            score = (
                min(opp.market_size.tam / 1e9, 1.0)
                * criteria.get("market_size", 0.3)
                + min(opp.estimated_roi / 10, 1.0) * criteria.get("roi", 0.25)
                + opp.confidence_score * criteria.get("confidence", 0.2)
                + max(0, 1 - (opp.time_to_market / 36))
                * criteria.get("time_to_market", 0.15)
                + (1 - opp._risk_to_score()) * criteria.get("risk", 0.1)
            )
            ranked.append((opp, score))

        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked

    async def generate_business_plan(
        self,
        opportunity: Opportunity,
    ) -> Dict[str, Any]:
        """Generate a business plan outline for an opportunity"""
        plan = {
            "opportunity_id": opportunity.id,
            "executive_summary": {
                "title": opportunity.title,
                "description": opportunity.description,
                "market": opportunity.market,
                "estimated_roi": opportunity.estimated_roi,
            },
            "market_analysis": {
                "market_size": opportunity.market_size.to_dict(),
                "competition": [
                    c.to_dict() for c in opportunity.competitive_landscape
                ],
                "key_insights": opportunity.key_insights,
            },
            "business_model": {
                "model": opportunity.business_model,
                "revenue_streams": self._generate_revenue_streams(opportunity),
                "cost_structure": self._generate_cost_structure(opportunity),
            },
            "go_to_market": {
                "target_customers": self._identify_target_customers(
                    opportunity
                ),
                "channels": self._identify_channels(opportunity),
                "positioning": self._generate_positioning(opportunity),
            },
            "financial_projections": {
                "time_to_market": opportunity.time_to_market,
                "estimated_roi": opportunity.estimated_roi,
                "risk_level": opportunity.risk_level.value,
            },
            "success_factors": opportunity.success_factors,
            "risks": {
                "barriers": opportunity.barriers_to_entry,
                "mitigation": self._generate_risk_mitigation(opportunity),
            },
            "generated_at": datetime.utcnow().isoformat(),
        }

        return plan

    def _generate_revenue_streams(self, opportunity: Opportunity) -> List[str]:
        """Generate potential revenue streams"""
        if "subscription" in opportunity.business_model.lower():
            return [
                "Monthly subscriptions",
                "Annual subscriptions",
                "Enterprise licenses",
            ]
        elif "marketplace" in opportunity.business_model.lower():
            return ["Transaction fees", "Listing fees", "Premium features"]
        else:
            return [
                "Primary product sales",
                "Premium features",
                "Professional services",
            ]

    def _generate_cost_structure(self, opportunity: Opportunity) -> List[str]:
        """Generate cost structure"""
        return [
            "Product development",
            "Customer acquisition",
            "Operations and infrastructure",
            "Team salaries",
            "Marketing and sales",
        ]

    def _identify_target_customers(
        self,
        opportunity: Opportunity,
    ) -> List[str]:
        """Identify target customer segments"""
        # Simplified - in production, use market research
        return [
            "Early adopters",
            "SMBs",
            "Enterprise customers",
        ]

    def _identify_channels(self, opportunity: Opportunity) -> List[str]:
        """Identify distribution channels"""
        return [
            "Direct sales",
            "Content marketing",
            "Partnerships",
            "Product-led growth",
        ]

    def _generate_positioning(self, opportunity: Opportunity) -> str:
        """Generate positioning statement"""
        return (
            f"The leading solution for {opportunity.market} "
            f"that solves {opportunity.description}"
        )

    def _generate_risk_mitigation(self, opportunity: Opportunity) -> List[str]:
        """Generate risk mitigation strategies"""
        strategies = []

        if opportunity.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            strategies.append("Start with MVP to validate assumptions")
            strategies.append("Secure strategic partnerships early")

        strategies.append("Focus on customer feedback and iteration")
        strategies.append("Build strong unit economics from day one")

        return strategies


# Made with Bob
