"""
Decision Engine for Sheldon OS.

This module provides strategic decision-making capabilities using
Multi-Criteria Decision Analysis (MCDA), cost-benefit analysis,
risk assessment, and explainable AI.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class DecisionType(Enum):
    """Types of decisions"""

    GO_NO_GO = "go_no_go"  # Binary decision
    PRIORITIZATION = "prioritization"  # Rank multiple options
    RESOURCE_ALLOCATION = "resource_allocation"  # Allocate resources
    STRATEGIC = "strategic"  # Strategic direction
    TACTICAL = "tactical"  # Tactical execution


class CriteriaType(Enum):
    """Types of decision criteria"""

    BENEFIT = "benefit"  # Higher is better
    COST = "cost"  # Lower is better


@dataclass
class Criterion:
    """Decision criterion"""

    name: str
    type: CriteriaType
    weight: float  # 0.0 to 1.0
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the criterion to a dictionary."""
        return {
            "name": self.name,
            "type": self.type.value,
            "weight": self.weight,
            "description": self.description,
        }


@dataclass
class Option:
    """Decision option"""

    id: str
    name: str
    description: str
    scores: Dict[str, float]  # Criterion name -> score
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the option to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "scores": self.scores,
            "metadata": self.metadata,
        }


@dataclass
class DecisionRationale:
    """Explanation for a decision"""

    reasoning: List[str]
    key_factors: Dict[str, float]
    trade_offs: List[str]
    risks: List[str]
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the decision rationale to a dictionary."""
        return {
            "reasoning": self.reasoning,
            "key_factors": self.key_factors,
            "trade_offs": self.trade_offs,
            "risks": self.risks,
            "confidence": self.confidence,
        }


@dataclass
class Decision:
    """Decision result"""

    id: str
    type: DecisionType
    question: str
    recommended_option: Option
    all_options: List[Option]
    criteria: List[Criterion]
    scores: Dict[str, float]  # Option ID -> final score
    rationale: DecisionRationale
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the decision to a dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "question": self.question,
            "recommended_option": self.recommended_option.to_dict(),
            "all_options": [o.to_dict() for o in self.all_options],
            "criteria": [c.to_dict() for c in self.criteria],
            "scores": self.scores,
            "rationale": self.rationale.to_dict(),
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class CostBenefitAnalysis:
    """Cost-benefit analysis result"""

    option_id: str
    total_costs: float
    total_benefits: float
    net_benefit: float
    roi: float
    payback_period: float  # months
    npv: float  # Net Present Value
    irr: float  # Internal Rate of Return

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the cost-benefit analysis to a dictionary."""
        return {
            "option_id": self.option_id,
            "total_costs": self.total_costs,
            "total_benefits": self.total_benefits,
            "net_benefit": self.net_benefit,
            "roi": self.roi,
            "payback_period": self.payback_period,
            "npv": self.npv,
            "irr": self.irr,
        }


class DecisionEngine:
    """
    Strategic decision-making engine using MCDA and explainable AI
    """

    def __init__(self, memory_system=None):
        """
        Initialize the decision engine

        Args:
            memory_system: Optional memory system for storing decisions
        """
        self.memory_system = memory_system
        self.decisions: Dict[str, Decision] = {}
        self.decision_history: List[Dict[str, Any]] = []

        logger.info("Decision Engine initialized")

    async def make_decision(
        self,
        question: str,
        options: List[Option],
        criteria: List[Criterion],
        decision_type: DecisionType = DecisionType.PRIORITIZATION,
        method: str = "weighted_sum",
    ) -> Decision:
        """
        Make a decision using MCDA

        Args:
            question: Decision question
            options: List of options to evaluate
            criteria: List of decision criteria
            decision_type: Type of decision
            method: MCDA method ("weighted_sum", "topsis", "ahp")

        Returns:
            Decision object with recommendation
        """
        try:
            logger.info("Making decision: %s", question)

            # Validate inputs
            self._validate_inputs(options, criteria)

            # Normalize weights
            criteria = self._normalize_weights(criteria)

            # Calculate scores based on method
            if method == "topsis":
                scores = await self._topsis_method(options, criteria)
            elif method == "ahp":
                scores = await self._ahp_method(options, criteria)
            else:
                scores = await self._weighted_sum_method(options, criteria)

            # Find best option
            best_option_id = max(
                scores.items(),
                key=lambda item: item[1],
            )[0]
            best_option = next(o for o in options if o.id == best_option_id)

            # Generate rationale
            rationale = await self._generate_rationale(
                best_option, options, criteria, scores
            )

            # Create decision
            decision = Decision(
                id=f"decision_{datetime.utcnow().timestamp()}",
                type=decision_type,
                question=question,
                recommended_option=best_option,
                all_options=options,
                criteria=criteria,
                scores=scores,
                rationale=rationale,
                metadata={
                    "method": method,
                    "num_options": len(options),
                    "num_criteria": len(criteria),
                },
            )

            # Store decision
            await self._store_decision(decision)

            logger.info("Decision made: %s", best_option.name)
            return decision

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error making decision: %s", exc)
            raise

    def _validate_inputs(
        self, options: List[Option], criteria: List[Criterion]
    ) -> None:
        """Validate decision inputs"""
        if not options:
            raise ValueError("At least one option required")

        if not criteria:
            raise ValueError("At least one criterion required")

        # Check that all options have scores for all criteria
        criterion_names = {c.name for c in criteria}
        for option in options:
            option_criteria = set(option.scores.keys())
            if option_criteria != criterion_names:
                raise ValueError(
                    f"Option {option.name} missing scores for criteria: "
                    f"{criterion_names - option_criteria}"
                )

    def _normalize_weights(self, criteria: List[Criterion]) -> List[Criterion]:
        """Normalize criterion weights to sum to 1.0"""
        total_weight = sum(c.weight for c in criteria)

        if total_weight == 0:
            # Equal weights if all zero
            weight = 1.0 / len(criteria)
            for criterion in criteria:
                criterion.weight = weight
        elif total_weight != 1.0:
            # Normalize to sum to 1.0
            for criterion in criteria:
                criterion.weight /= total_weight

        return criteria

    async def _weighted_sum_method(
        self, options: List[Option], criteria: List[Criterion]
    ) -> Dict[str, float]:
        """Calculate scores using weighted sum method"""
        scores = {}

        # Normalize scores for each criterion
        normalized_scores = self._normalize_scores(options, criteria)

        for option in options:
            score = 0.0
            for criterion in criteria:
                norm_score = normalized_scores[option.id][criterion.name]
                score += criterion.weight * norm_score

            scores[option.id] = score

        return scores

    def _normalize_scores(
        self, options: List[Option], criteria: List[Criterion]
    ) -> Dict[str, Dict[str, float]]:
        """Normalize scores to 0-1 range"""
        normalized: Dict[str, Dict[str, float]] = {}

        for criterion in criteria:
            # Get all scores for this criterion
            criterion_scores = [
                option.scores[criterion.name] for option in options
            ]

            min_score = min(criterion_scores)
            max_score = max(criterion_scores)
            score_range = max_score - min_score

            # Normalize each option's score
            for option in options:
                if option.id not in normalized:
                    normalized[option.id] = {}

                raw_score = option.scores[criterion.name]

                if score_range == 0:
                    norm_score = 1.0
                else:
                    if criterion.type == CriteriaType.BENEFIT:
                        # Higher is better
                        norm_score = (raw_score - min_score) / score_range
                    else:
                        # Lower is better (cost)
                        norm_score = (max_score - raw_score) / score_range

                normalized[option.id][criterion.name] = norm_score

        return normalized

    async def _topsis_method(
        self, options: List[Option], criteria: List[Criterion]
    ) -> Dict[str, float]:
        """
        Calculate scores using TOPSIS (Technique for Order of Preference
        by Similarity to Ideal Solution)
        """
        # Normalize scores
        normalized = self._normalize_scores(options, criteria)

        # Find ideal and anti-ideal solutions
        ideal: Dict[str, float] = {}
        anti_ideal: Dict[str, float] = {}

        for criterion in criteria:
            criterion_scores = [
                normalized[o.id][criterion.name] for o in options
            ]
            ideal[criterion.name] = max(criterion_scores)
            anti_ideal[criterion.name] = min(criterion_scores)

        # Calculate distances
        scores: Dict[str, float] = {}
        for option in options:
            # Distance to ideal
            dist_ideal = np.sqrt(
                sum(
                    criterion.weight
                    * (
                        normalized[option.id][criterion.name]
                        - ideal[criterion.name]
                    )
                    ** 2
                    for criterion in criteria
                )
            )

            # Distance to anti-ideal
            dist_anti_ideal = np.sqrt(
                sum(
                    criterion.weight
                    * (
                        normalized[option.id][criterion.name]
                        - anti_ideal[criterion.name]
                    )
                    ** 2
                    for criterion in criteria
                )
            )

            # Relative closeness to ideal
            if dist_ideal + dist_anti_ideal == 0:
                scores[option.id] = 0.5
            else:
                scores[option.id] = (
                    dist_anti_ideal / (dist_ideal + dist_anti_ideal)
                )

        return scores

    async def _ahp_method(
        self, options: List[Option], criteria: List[Criterion]
    ) -> Dict[str, float]:
        """
        Calculate scores using AHP (Analytic Hierarchy Process)
        Simplified version using weighted geometric mean
        """
        scores = {}

        for option in options:
            # Geometric mean of weighted scores
            product = 1.0
            for criterion in criteria:
                score = option.scores[criterion.name]
                # Normalize to 0-1 range
                max_score = max(o.scores[criterion.name] for o in options)
                min_score = min(o.scores[criterion.name] for o in options)

                if max_score == min_score:
                    norm_score = 1.0
                else:
                    if criterion.type == CriteriaType.BENEFIT:
                        norm_score = (
                            score - min_score
                        ) / (max_score - min_score)
                    else:
                        norm_score = (
                            max_score - score
                        ) / (max_score - min_score)

                # Weighted geometric mean
                product *= norm_score**criterion.weight

            scores[option.id] = product

        return scores

    async def _generate_rationale(
        self,
        best_option: Option,
        all_options: List[Option],
        criteria: List[Criterion],
        scores: Dict[str, float],
    ) -> DecisionRationale:
        """Generate explanation for the decision"""
        reasoning = []
        key_factors = {}
        trade_offs = []
        risks = []

        # Identify key factors
        for criterion in criteria:
            best_score = best_option.scores[criterion.name]
            avg_score = np.mean(
                [o.scores[criterion.name] for o in all_options]
            )

            if best_score > avg_score * 1.2:  # 20% better than average
                reasoning.append(
                    f"{best_option.name} excels in {criterion.name} "
                    f"(score: {best_score:.2f} vs avg: {avg_score:.2f})"
                )
                key_factors[criterion.name] = best_score

        # Identify trade-offs
        for criterion in criteria:
            best_score = best_option.scores[criterion.name]
            max_score = max(o.scores[criterion.name] for o in all_options)

            if best_score < max_score * 0.8:  # 20% worse than best
                trade_offs.append(
                    f"Trade-off in {criterion.name}: "
                    f"{best_option.name} scores "
                    f"{best_score:.2f} vs best option's "
                    f"{max_score:.2f}"
                )

        # Identify risks
        if best_option.metadata.get("risk_level") in ["high", "very_high"]:
            risks.append("High risk level associated with this option")

        if best_option.metadata.get("time_to_market", 0) > 18:
            risks.append("Long time to market (>18 months)")

        # Calculate confidence
        best_score = scores[best_option.id]
        second_best_score = (
            sorted(scores.values(), reverse=True)[1] if len(scores) > 1 else 0
        )
        score_gap = best_score - second_best_score
        confidence = min(
            1.0, 0.5 + score_gap
        )  # Higher gap = higher confidence

        return DecisionRationale(
            reasoning=reasoning,
            key_factors=key_factors,
            trade_offs=trade_offs,
            risks=risks,
            confidence=confidence,
        )

    async def cost_benefit_analysis(
        self,
        option: Option,
        costs: Dict[str, float],
        benefits: Dict[str, float],
        discount_rate: float = 0.1,
        time_horizon: int = 36,  # months
    ) -> CostBenefitAnalysis:
        """
        Perform cost-benefit analysis for an option

        Args:
            option: Option to analyze
            costs: Dictionary of cost items
            benefits: Dictionary of benefit items
            discount_rate: Annual discount rate
            time_horizon: Analysis period in months

        Returns:
            CostBenefitAnalysis object
        """
        try:
            # Calculate totals
            total_costs = sum(costs.values())
            total_benefits = sum(benefits.values())
            net_benefit = total_benefits - total_costs

            # Calculate ROI
            roi = (net_benefit / total_costs) if total_costs > 0 else 0

            # Calculate payback period
            monthly_net_benefit = net_benefit / time_horizon
            payback_period = (
                (total_costs / monthly_net_benefit)
                if monthly_net_benefit > 0
                else float("inf")
            )

            # Calculate NPV
            monthly_rate = discount_rate / 12
            npv = (
                sum(
                    monthly_net_benefit / ((1 + monthly_rate) ** month)
                    for month in range(1, time_horizon + 1)
                )
                - total_costs
            )

            # Estimate IRR (simplified)
            irr = self._calculate_irr(
                total_costs,
                monthly_net_benefit,
                time_horizon,
            )

            analysis = CostBenefitAnalysis(
                option_id=option.id,
                total_costs=total_costs,
                total_benefits=total_benefits,
                net_benefit=net_benefit,
                roi=roi,
                payback_period=payback_period,
                npv=npv,
                irr=irr,
            )

            logger.info(
                "Cost-benefit analysis complete for %s: ROI=%.2f",
                option.name,
                roi,
            )
            return analysis

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error in cost-benefit analysis: %s", exc)
            raise

    def _calculate_irr(
        self, initial_investment: float, monthly_cash_flow: float, periods: int
    ) -> float:
        """Calculate Internal Rate of Return (simplified)"""
        # Use Newton's method to find IRR
        rate = 0.1  # Initial guess

        for _ in range(100):  # Max iterations
            npv = -initial_investment + sum(
                monthly_cash_flow / ((1 + rate) ** month)
                for month in range(1, periods + 1)
            )

            # Derivative of NPV
            dnpv = sum(
                -month * monthly_cash_flow / ((1 + rate) ** (month + 1))
                for month in range(1, periods + 1)
            )

            if abs(npv) < 0.01:  # Converged
                break

            if dnpv == 0:
                break

            rate = rate - npv / dnpv

        return rate * 12  # Convert to annual rate

    async def sensitivity_analysis(
        self,
        decision: Decision,
        variable_criterion: str,
        value_range: Tuple[float, float],
        steps: int = 10,
    ) -> Dict[str, List[Tuple[float, float]]]:
        """
        Perform sensitivity analysis on a decision

        Args:
            decision: Decision to analyze
            variable_criterion: Criterion to vary
            value_range: (min, max) range for the criterion
            steps: Number of steps in the range

        Returns:
            Dictionary mapping option IDs to (value, score) tuples
        """
        results: Dict[str, List[Tuple[float, float]]] = {
            option.id: [] for option in decision.all_options
        }

        try:
            # Generate values to test
            values = np.linspace(value_range[0], value_range[1], steps)

            for value in values:
                # Create modified options
                modified_options = []
                for option in decision.all_options:
                    modified_scores = option.scores.copy()
                    modified_scores[variable_criterion] = value

                    modified_option = Option(
                        id=option.id,
                        name=option.name,
                        description=option.description,
                        scores=modified_scores,
                        metadata=option.metadata,
                    )
                    modified_options.append(modified_option)

                # Recalculate scores
                scores = await self._weighted_sum_method(
                    modified_options, decision.criteria
                )

                # Store results
                for option_id, score in scores.items():
                    results[option_id].append((float(value), float(score)))

            logger.info(
                "Sensitivity analysis complete for %s",
                variable_criterion,
            )
            return results

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error in sensitivity analysis: %s", exc)
            return results

    async def portfolio_optimization(
        self, options: List[Option], budget: float, criteria: List[Criterion]
    ) -> List[Option]:
        """
        Optimize portfolio of options within budget constraint

        Args:
            options: Available options
            budget: Total budget
            criteria: Decision criteria

        Returns:
            Optimal portfolio of options
        """
        try:
            # Calculate value/cost ratio for each option
            scores = await self._weighted_sum_method(options, criteria)

            # Sort by value/cost ratio
            options_with_scores = [
                (option, scores[option.id], option.metadata.get("cost", 0))
                for option in options
            ]

            # Greedy selection (simplified knapsack)
            selected = []
            remaining_budget = budget

            # Sort by score/cost ratio
            options_with_scores.sort(
                key=lambda x: x[1] / x[2] if x[2] > 0 else 0, reverse=True
            )

            for option, _score, cost in options_with_scores:
                if cost <= remaining_budget:
                    selected.append(option)
                    remaining_budget -= cost

            logger.info(
                "Portfolio optimization: selected %d options",
                len(selected),
            )
            return selected

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error in portfolio optimization: %s", exc)
            return []

    async def _store_decision(self, decision: Decision) -> None:
        """Store decision in memory system"""
        try:
            self.decisions[decision.id] = decision
            self.decision_history.append(
                {
                    "decision_id": decision.id,
                    "question": decision.question,
                    "recommendation": decision.recommended_option.name,
                    "timestamp": decision.created_at.isoformat(),
                }
            )

            if self.memory_system:
                await self.memory_system.store_long_term(
                    key=f"decision:{decision.id}",
                    value=decision.to_dict(),
                    metadata={
                        "type": "decision",
                        "decision_type": decision.type.value,
                    },
                )

            logger.debug("Stored decision: %s", decision.id)

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error storing decision: %s", exc)

    async def learn_from_outcome(
        self, decision_id: str, actual_outcome: Dict[str, Any], success: bool
    ) -> None:
        """Learn from decision outcomes to improve future decisions"""
        try:
            decision = self.decisions.get(decision_id)
            if not decision:
                logger.warning("Decision %s not found", decision_id)
                return

            # Store outcome
            outcome_record = {
                "decision_id": decision_id,
                "recommended_option": decision.recommended_option.id,
                "actual_outcome": actual_outcome,
                "success": success,
                "timestamp": datetime.utcnow().isoformat(),
            }

            self.decision_history.append(outcome_record)

            # Update criterion weights based on outcome
            if success:
                logger.info("Decision %s was successful", decision_id)
            else:
                logger.info(
                    "Decision %s was unsuccessful - learning from failure",
                    decision_id,
                )

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error learning from outcome: %s", exc)

    def get_decision_statistics(self) -> Dict[str, Any]:
        """Get statistics about decisions made"""
        try:
            total_decisions = len(self.decisions)

            # Count by type
            by_type: Dict[str, int] = {}
            for decision in self.decisions.values():
                type_key = decision.type.value
                by_type[type_key] = by_type.get(type_key, 0) + 1

            # Average confidence
            avg_confidence = (
                np.mean(
                    [d.rationale.confidence for d in self.decisions.values()]
                )
                if self.decisions
                else 0
            )

            return {
                "total_decisions": total_decisions,
                "by_type": by_type,
                "avg_confidence": float(avg_confidence),
                "history_length": len(self.decision_history),
            }

        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Error getting statistics: %s", exc)
            return {}


# Made with Bob
