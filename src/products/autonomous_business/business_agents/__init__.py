"""
Specialized business agents for Autonomous Business Platform

These agents handle specific business functions:
- Sales: Lead qualification, outreach, pipeline management
- Marketing: Content creation, campaigns, social media
- Finance: Invoicing, expenses, reporting
- Operations: Task management, project coordination
- Customer Service: Support tickets, responses, satisfaction
"""

from .finance_agent import FinanceAgent
from .marketing_agent import MarketingAgent
from .operations_agent import OperationsAgent
from .sales_agent import SalesAgent

__all__ = [
    "SalesAgent",
    "MarketingAgent",
    "FinanceAgent",
    "OperationsAgent",
]

# Made with Bob
