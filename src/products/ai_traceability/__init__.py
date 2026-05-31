"""
Enterprise AI Traceability Application.

Keystroke-level monitoring system for enterprise AI usage with
cross-platform coverage. Provides real-time visibility, policy
enforcement, and compliance reporting for AI tool usage.

Market Opportunity:
- TAM: $12.8B (Global enterprise AI governance)
- Target: 500,000+ enterprises with 100+ employees
- Growth: 47% CAGR driven by EU AI Act, SEC requirements
- Pricing: $15-50/user/month, $100K-500K enterprise contracts

Competitive Advantages:
- Keystroke-level granularity (no competitor offers this)
- Cross-platform coverage (ChatGPT, Claude, Gemini, all LLMs)
- Attachment tracking (critical for document-heavy industries)
- User-friendly deployment (download-on-all-devices simplicity)
- Sheldon OS integration (native AI agent capabilities)

Components:
- endpoint_agent: Cross-platform monitoring agent
- backend: Cloud processing and analytics
- dashboard: Admin console and API
- models: Data models and schemas
"""

__version__ = "0.1.0"
__author__ = "Sheldon OS Team"

from . import models
from .models import AISession, Attachment, Keystroke, Policy

__all__ = list(models.__all__)

# Made with Bob
