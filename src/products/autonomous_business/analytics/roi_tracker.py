"""
ROI Tracker
Tracks return on investment for business activities
"""

import logging
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ROITracker:
    """
    Tracks ROI for business activities
    """

    def __init__(self, business_id: str):
        self.business_id = business_id
        self._investments: Dict[str, Dict[str, Any]] = {}
        logger.info(
            "ROI Tracker initialized for business %s",
            business_id,
        )

    async def track_investment(
        self, investment_id: str, amount: float, category: str
    ) -> bool:
        """Track an investment"""
        self._investments[investment_id] = {
            "amount": amount,
            "category": category,
            "date": datetime.utcnow(),
            "returns": 0.0,
        }
        logger.info(
            "Tracking investment %s: $%s",
            investment_id,
            amount,
        )
        return True

    async def record_return(
        self,
        investment_id: str,
        return_amount: float,
    ) -> bool:
        """Record return on investment"""
        if investment_id in self._investments:
            self._investments[investment_id]["returns"] += return_amount
            logger.info(
                "Recorded return for %s: $%s",
                investment_id,
                return_amount,
            )
            return True
        return False

    async def calculate_roi(self, investment_id: str) -> Dict[str, Any]:
        """Calculate ROI for an investment"""
        if investment_id not in self._investments:
            return {"error": "Investment not found"}

        investment = self._investments[investment_id]
        roi = (
            investment["returns"] - investment["amount"]
        ) / investment["amount"]

        return {
            "investment_id": investment_id,
            "invested": investment["amount"],
            "returns": investment["returns"],
            "roi": roi,
            "roi_percentage": roi * 100,
        }

    async def get_total_roi(self) -> Dict[str, Any]:
        """Get total ROI across all investments"""
        total_invested = sum(
            inv["amount"] for inv in self._investments.values()
        )
        total_returns = sum(
            inv["returns"] for inv in self._investments.values()
        )

        if total_invested == 0:
            return {"total_roi": 0, "total_invested": 0, "total_returns": 0}

        total_roi = (total_returns - total_invested) / total_invested

        return {
            "total_invested": total_invested,
            "total_returns": total_returns,
            "total_roi": total_roi,
            "roi_percentage": total_roi * 100,
        }
