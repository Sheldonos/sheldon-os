# Sheldon OS

**An Autonomous Agentic Operating System for Managing Digital Businesses**

> **Status:** Conditionally production-ready for controlled pilots and technical diligence.  
> Static validation is clean, bounded unit/integration validation is passing, and critical orchestration regressions have been fixed. Repository-wide runtime coverage is not yet above the original 80% target, so broad unqualified production-readiness claims should be avoided until additional runtime coverage is added.

Sheldon OS is a self-learning operating system designed to manage autonomous business units, orchestrate multi-agent systems, and run digital businesses with minimal human intervention.

## Validation Status

- **Bounded validation suite:** 80/80 tests passing
- **Flake8:** passing
- **Mypy:** passing
- **Pylint:** passing with production validation profile
- **Measured repository-wide coverage from bounded suite:** 38%
- **Critical lifecycle/orchestration regressions:** fixed
- **Recommended release posture:** controlled pilot / staged production

See:
- [`DEBUG_REPORT.md`](DEBUG_REPORT.md)
- [`PRODUCTION_CHECKLIST.md`](PRODUCTION_CHECKLIST.md)
- [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md)
- [`docs/PROACTIVE_OS_STRATEGY.md`](docs/PROACTIVE_OS_STRATEGY.md)

## 🧭 Strategic Direction: Prompt-Free, Proactive Operation

Sheldon OS is evolving from a prompt-driven agent platform into a **prompt-light, proactive operating system**.

Target operating modes:
- **Reactive mode**: user gives direct prompts
- **Copilot mode**: system proposes next-best actions for approval
- **Autonomous mode**: system executes within approved guardrails and escalates only when needed

The intended primary interface is a **Mission Control dashboard** that surfaces:
- active agents and workflows
- business KPIs and forecasts
- risks, bottlenecks, and alerts
- recommended next-best actions
- pending approvals
- reusable success patterns and client-specific constraints

Design principle:
- Sheldon OS should store and reuse success patterns
- Sheldon OS should not overwrite client brand identity, tone, or strategic boundaries
- universal optimization logic must remain constrained by client-specific memory and governance rules

See [`docs/PROACTIVE_OS_STRATEGY.md`](docs/PROACTIVE_OS_STRATEGY.md) for the full architecture and competitive positioning direction.

## 🌟 Key Features

- **Multi-Agent Orchestration**: Coordinate hundreds of specialized agents working in parallel
- **Advanced Memory System**: Short-term and long-term memory with pattern recognition
- **Hybrid Retrieval Brain**: Vector recall, reranking, knowledge graph traversal, and synthesis-driven answers
- **Context Management**: Automatic context handoffs across hourly, daily, weekly, monthly, and annual intervals
- **Self-Learning**: Continuous improvement through pattern analysis and performance optimization
- **Business Intelligence**: Opportunity identification, forecasting, and strategic decision-making
- **Autonomous Operations**: Agents can create, deploy, and manage other agents
- **Scalable Architecture**: Built with async/await patterns for high concurrency

## 🏗️ Architecture

```text
sheldon-os/
├── src/
│   ├── core/                  # Core orchestration engine
│   │   ├── orchestrator.py    # Main coordination engine
│   │   ├── memory_system.py   # Advanced memory management
│   │   ├── context_manager.py # Context handoff system
│   │   └── config.py          # System configuration
│   ├── agents/                # Agent management system
│   │   ├── base_agent.py
│   │   ├── agent_factory.py
│   │   ├── agent_registry.py
│   │   └── lifecycle_manager.py
│   ├── intelligence/          # Business intelligence
│   │   ├── pattern_recognition.py
│   │   ├── opportunity_finder.py
│   │   ├── forecasting.py
│   │   ├── decision_engine.py
│   │   └── market_analyzer.py
│   ├── integrations/          # External integrations
│   │   ├── mcp/
│   │   └── connectors/
│   ├── api/                   # API gateway and auth
│   ├── products/              # Business applications
│   │   ├── ai_traceability/
│   │   ├── autonomous_business/
│   │   ├── rightai/
│   │   └── creator_monetization/
│   └── utils/
├── tests/
├── docs/
├── k8s/
├── docker/
├── monitoring/
├── requirements.txt
├── setup.py
└── .env.example
```

## 🚀 Quick Start

### Prerequisites

- Python **3.9 or higher**
- PostgreSQL 14+
- Redis 7+

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/sheldon-os/sheldon-os.git
cd sheldon-os
```

2. **Create a virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Install package or use source path**
```bash
pip install -e .
```

If editable install is restricted in your environment, use:

```bash
PYTHONPATH=src python3 -m pytest tests/test_core.py -q
```

## Basic Usage

```python
import asyncio

from sheldon_os.core import Config, Orchestrator
from sheldon_os.core.context_manager import ContextManager
from sheldon_os.core.memory_system import MemorySystem


async def main():
    config = Config()
    memory = MemorySystem()
    context = ContextManager()

    orchestrator = Orchestrator(
        config=config,
        memory_system=memory,
        context_manager=context,
    )

    await orchestrator.start()

    task_id = await orchestrator.create_task(
        name="example_task",
        description="An example task",
        priority="high",
    )

    print(f"Created task: {task_id}")

    metrics = await orchestrator.get_metrics()
    print(metrics.to_dict())

    await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(main())
```

## 📚 Core Components

### Orchestrator
Coordinates:
- task delegation and execution
- agent coordination
- resource allocation
- health monitoring
- self-learning loops

### Memory System
Provides:
- short-term and long-term memory
- hybrid retrieval
- graph-aware recall
- synthesis support
- gap analysis
- consolidation workflows

### Context Manager
Supports:
- hourly context
- daily context
- weekly context
- monthly context
- semi-annual context
- annual context
- snapshot and handoff generation

### Agent System
Includes:
- `BaseAgent`
- `AgentFactory`
- `AgentRegistry`
- `LifecycleManager`

## 🔧 Configuration

Configuration is managed through environment variables and the `Config` class.

Key areas:
- database
- redis
- llm provider
- agent concurrency and timeouts
- memory retention and retrieval settings
- security and JWT settings
- monitoring and logging
- API host/port/workers

See:
- [`.env.example`](.env.example)
- [`src/core/config.py`](src/core/config.py)

## 🧪 Testing

### Bounded validation suite used in final debugging pass

```bash
cd sheldon-os && PYTHONPATH=src python3 -m pytest \
  tests/test_core.py \
  tests/test_agents.py \
  tests/test_intelligence.py \
  tests/integration/test_core_integration.py \
  tests/integration/test_intelligence_integration.py \
  -m "not slow and not heavy and not sustained" \
  --cov=src --cov-report=term-missing
```

### Additional commands

```bash
# Full test discovery
pytest

# Coverage report
pytest --cov=src --cov-report=html

# Static validation
flake8 src tests
python3 -m mypy --config-file mypy.ini src
python3 -m pylint --rcfile=.pylintrc src
```

## 📈 Performance

Validated in the final bounded pass:

- **80 tests passed**
- **~12m 53s bounded validation runtime**
- **Concurrent agent workflows validated in integration tests**
- **Crash recovery and cascading failure prevention validated**
- **Long-running checkpoint behavior validated**

### Important note
The full performance suite and sustained-load scenarios were **not** completed in the final debugging pass. Claims such as sustained 100+ concurrent agents under production load should be treated as architectural targets until dedicated load validation is completed in a production-like environment.

## 🛣️ Roadmap Status

### Phase 1: Core Infrastructure ✅ COMPLETE
- [x] Orchestrator engine
- [x] Memory system
- [x] Context manager
- [x] Agent system
- [x] Basic test suite
- [x] Agent registry implementation

### Phase 2: Intelligence Layer ✅ COMPLETE
- [x] Pattern recognition engine
- [x] Opportunity finder
- [x] Forecasting system
- [x] Decision engine
- [x] Market analyzer
- [x] Integration tests
- [x] Documentation and examples

### Phase 3: Integrations ✅ COMPLETE
- [x] MCP server management
- [x] External tool connectors
- [x] API gateway
- [x] Documentation

### Phase 4: Business Applications ✅ COMPLETE
- [x] Enterprise AI traceability
- [x] Autonomous business units
- [x] Creator monetization platform
- [x] Workflow orchestration and ROI tracking

### Phase 5+: Hardening and Deployment ✅ IN PROGRESS / PARTIALLY VALIDATED
- [x] Static analysis cleanup
- [x] Bounded unit/integration validation
- [x] Production checklist
- [x] Debug report
- [ ] Repository-wide runtime coverage >80%
- [ ] Full performance/load validation
- [ ] Full API/integration runtime validation
- [ ] Full product runtime validation

## 📊 Current Metrics

- **Bounded validation:** 80/80 passing
- **Repository-wide measured coverage:** 38%
- **Static analysis:** flake8, mypy, pylint passing
- **Core/intelligence validation:** strong
- **API/integration/product runtime coverage:** limited
- **Release recommendation:** controlled pilots only

## 🛠️ Debugging and Troubleshooting

### Common validation commands

```bash
# Core bounded validation
cd sheldon-os && PYTHONPATH=src python3 -m pytest tests/test_core.py tests/test_agents.py tests/test_intelligence.py tests/integration/test_core_integration.py tests/integration/test_intelligence_integration.py -m "not slow and not heavy and not sustained"

# Type checking
cd sheldon-os && PYTHONPATH=src python3 -m mypy --config-file mypy.ini src

# Linting
cd sheldon-os && flake8 src tests
cd sheldon-os && PYTHONPATH=src python3 -m pylint --rcfile=.pylintrc src
```

### Known warning classes during validation

- environment-specific LibreSSL/OpenSSL warning from local Python runtime
- non-fatal forecasting-library warnings may still appear depending on local dependency versions

Resolved during debugging:
- Pydantic v2 deprecation warnings in `src/core/config.py`
- deprecated pandas monthly frequency aliases in forecasting tests
- pytest collection warning for helper agent test class

### If editable install fails

Use a clean virtual environment or run commands with `PYTHONPATH=src`.

### If forecasting tests emit warnings

Current warnings are non-fatal in the validated suite. See [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) for cleanup items.

## ⚠️ Production Readiness Statement

Sheldon OS is **conditionally production-ready** for:
- controlled pilots
- internal demos
- technical diligence
- staged enterprise evaluation

Sheldon OS is **not yet ready for an unqualified broad production-readiness claim** because:
- repository-wide runtime coverage is below target
- API/integration runtime validation is incomplete
- product runtime validation is incomplete
- full sustained-load validation is still pending

## 🤝 Contributing

Contributions are welcome. Before major changes:
1. run bounded tests
2. run flake8
3. run mypy
4. run pylint
5. update docs if behavior changes

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

Built with:
- LangChain
- FastAPI
- Pydantic
- PostgreSQL
- Redis

## 📞 Support

- Documentation: `docs/`
- Debug report: [`DEBUG_REPORT.md`](DEBUG_REPORT.md)
- Production checklist: [`PRODUCTION_CHECKLIST.md`](PRODUCTION_CHECKLIST.md)
- Known issues: [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md)

---

**Built by the Sheldon OS Team**