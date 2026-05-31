"""
Autonomous Business Unit Platform

A comprehensive AI-powered business automation platform that enables
solopreneurs and SMBs to run digital businesses with minimal manual
intervention.

Key Features:
- Specialized business agents
  (sales, marketing, finance, operations, customer service)
- Workflow automation and orchestration
- 100+ tool integrations
- ROI tracking and analytics
- No-code workflow builder
- Template library

Target Market:
- Solopreneurs and digital entrepreneurs
- Small agencies (2-10 employees)
- Freelancers and consultants
- E-commerce store owners
- Content creators

Value Proposition:
- 10x ROI through automation
- Save 20+ hours per week
- Comprehensive business operations coverage
- Customizable to any business type
"""

from .models.business import Business, BusinessConfig
from .models.task import Task, TaskPriority, TaskStatus
from .models.workflow import Workflow, WorkflowStep, WorkflowTrigger

__version__ = "0.1.0"

__all__ = [
    "Business",
    "BusinessConfig",
    "Workflow",
    "WorkflowStep",
    "WorkflowTrigger",
    "Task",
    "TaskStatus",
    "TaskPriority",
]

# Made with Bob
