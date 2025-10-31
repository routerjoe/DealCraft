# DealCraft API

[![Build Status](https://img.shields.io/github/actions/workflow/status/routerjoe/DealCraft/ci.yml?branch=main)](https://github.com/routerjoe/DealCraft/actions)
[![Tests](https://img.shields.io/badge/tests-71%20passing-success)](https://github.com/routerjoe/DealCraft/actions)
[![Latest Release](https://img.shields.io/github/v/release/routerjoe/DealCraft)](https://github.com/routerjoe/DealCraft/releases/tag/v2.0.0)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Proprietary-red)](LICENSE)

FastAPI-based Model Context Protocol API for DealCraft with integrated TUI management interface and Obsidian dashboard generation.

## Features

- 🚀 **FastAPI** web framework with async support
- 🤖 **AI Router** with multi-model selection (OpenAI, Anthropic, Gemini)
- 📊 **System Monitoring** with last-10-actions logging
- 📝 **Structured JSON logging** with request tracking
- 🔍 **Request ID tracking** and latency measurement (<3ms avg)
- 📁 **Federal FY Routing** for opportunity management
- 📈 **Obsidian Dataview Dashboard** with 10+ query views
- 🏥 **Health check** and API info endpoints
- 🧪 **Comprehensive test coverage** (71 tests passing)
- 🎨 **Textual TUI** for interactive management

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.sample .env
# Edit .env as needed
```

### 3. Run Development Server

```bash
# Using Kilo Code aliases
kc run:dev

# Or directly
bash scripts/dev.sh
```

The API will be available at http://localhost:8000

### 4. Run TUI Interface

```bash
# Using Kilo Code
kc run:tui

# Or directly
python -m tui.app
```

### 5. Run Tests

```bash
# Using Kilo Code
kc run:test

# Or directly
bash scripts/test.sh
```

## API Endpoints

The API provides 30+ endpoints across multiple categories:

- **Core:** Health checks, API info
- **AI & Intelligence:** Multi-model AI routing (6 models), RFQ guidance
- **System:** Monitoring, recent actions, metrics (v1.4.0+)
- **Obsidian:** Opportunity creation with FY routing
- **Contacts:** CSV/vCard export
- **Email:** RFQ/Govly/IntroMail ingestion
- **OEM & Contracts:** CRUD operations
- **Forecast:** Multi-year projections (v1.4.0+)
- **Webhooks:** Govly/Radar ingestion (v1.4.0+)

**📖 [Complete API Reference →](docs/api/endpoints.md)**

## TUI Interface

The Textual-based Terminal User Interface provides interactive management of sales operations:

### Features
- **RFQ Management** - View, filter, and process RFQs
- **Analytics Dashboard** - Real-time pipeline metrics
- **OEM & Contract Management** - CRUD operations for vendors
- **AI Guidance** - Get AI-powered recommendations
- **IntroMail Analysis** - Automated email processing
- **Artifacts View** - Export and file management

### Screenshot
```
┌─ DealCraft TUI ──────────────────────────────────────────────┐
│  📊 Dashboard  │  📧 RFQs  │  🤝 OEMs  │  📋 Contracts  │    │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Pipeline Summary:                                            │
│  ├─ Total RFQs: 42                                           │
│  ├─ Qualified: 28                                            │
│  ├─ In Progress: 14                                          │
│  └─ Won This Month: 6                                        │
│                                                               │
│  Recent Activity:                                             │
│  • RFQ-2025-001: Federal IT Modernization                   │
│  • RFQ-2025-002: Cloud Migration Project                    │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### Launch TUI
```bash
# Development mode
kc run:tui

# Production mode
python -m tui.app --config production
```

## Phase 3 Enhancements (v1.3.0)

### AI Router
- **Multi-model support:** OpenAI (gpt-5-thinking, gpt-4-turbo), Anthropic (claude-3.5, claude-3-opus), Gemini (gemini-1.5-pro, gemini-1.5-flash)
- **Unified endpoint:** `/v1/ai/ask` for general queries
- **Model validation:** Automatic fallback to default model

### System Monitoring
- **Recent actions logging:** Last 10 requests tracked in `data/state.json`
- **Request tracking:** All responses include `x-request-id` and `x-latency-ms` headers
- **Performance:** <3ms average latency

### Federal FY Routing
- **Automatic routing:** Opportunities routed to `40 Projects/Opportunities/FYxx/` based on close date
- **Triage queue:** Invalid dates route to `Triage/` folder
- **FY calculation:** Oct 1 (N-1) to Sep 30 (N)

### Obsidian Dashboard
- **Location:** `obsidian/50 Dashboards/Opportunities Dashboard.md`
- **10 Dataview queries:** Pipeline analysis, FY breakdown, top opportunities, etc.
- **YAML aliases:** Non-breaking aliases for dashboard compatibility

See [CHANGELOG.md](CHANGELOG.md) for complete details.

## Logging

All requests are logged in structured JSON format with the following fields:

```json
{
  "timestamp": "2025-10-26 01:30:45,123",
  "level": "INFO",
  "message": "GET /healthz 200",
  "request_id": "a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5g6h7",
  "latency_ms": 1.23,
  "method": "GET",
  "path": "/healthz",
  "status": 200
}
```

Every response includes an `X-Request-ID` header for request tracking and an `X-Latency-MS` header for performance monitoring.

## Project Structure

```
red-river-sales-automation/
├── mcp/
│   ├── api/                  # API endpoints
│   │   ├── main.py          # FastAPI application
│   │   └── v1/              # Version 1 endpoints
│   │       ├── ai.py        # AI router endpoints
│   │       ├── contacts.py  # Contact export
│   │       ├── contracts.py # Contract vehicles
│   │       ├── email.py     # Email ingestion
│   │       ├── obsidian.py  # Obsidian integration
│   │       ├── oems.py      # OEM management
│   │       └── system.py    # System monitoring
│   └── core/                # Core modules
│       ├── ai_router.py     # AI model routing
│       ├── config.py        # Configuration loader
│       ├── logging.py       # JSON logging setup
│       └── store.py         # State persistence
├── tui/                     # Terminal UI
│   ├── app.py              # TUI application
│   └── rrtui/              # UI components
├── obsidian/               # Obsidian vault integration
│   ├── 40 Projects/        # Project notes (FY-routed)
│   ├── 50 Dashboards/      # Dataview dashboards
│   └── 60 Projects/        # Sprint summaries
├── scripts/                # Shell scripts
│   ├── dev.sh             # Development server
│   ├── test.sh            # Run tests
│   ├── lint.sh            # Run linter
│   └── build.sh           # Build checks
├── tests/                  # Test suite (71 tests)
│   ├── test_ai_endpoints.py
│   ├── test_contacts_export.py
│   ├── test_contracts.py
│   ├── test_email_ingest.py
│   ├── test_health.py
│   ├── test_obsidian.py
│   └── test_oems.py
├── docs/                   # Documentation
│   ├── PHASE3_OVERVIEW.md # Phase 3 features
│   └── architecture_phase3.md # Architecture diagram
├── .env.sample            # Environment template
├── CHANGELOG.md           # Version history
├── logging.json           # Logging configuration
├── requirements.txt       # Python dependencies
└── kilo.yml              # Kilo Code task aliases
```

## Development

### Kilo Code Tasks

```bash
kc run:dev    # Start development server
kc run:test   # Run test suite
kc run:lint   # Run linter
kc run:build  # Run lint + tests
kc run:tui    # Launch TUI interface
```

### Environment Variables

See [`.env.sample`](.env.sample) for all available configuration options.

### Running Tests

```bash
# Run all tests
pytest -v

# Run specific test file
pytest tests/test_ai_endpoints.py -v

# Run with coverage
pytest --cov=mcp --cov-report=html
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking (if mypy configured)
mypy mcp/
```

## Architecture

See [docs/architecture_phase3.md](docs/architecture_phase3.md) for detailed architecture diagrams and component descriptions.

## Releases

Release notes are maintained in [`docs/releases/`](docs/releases/) with full changelogs, upgrade notes, and smoke tests.

- **Latest:** [v1.4.0](docs/releases/v1.4.0.md) - Phase 4: Forecast & Govly Automation Batch (October 28, 2025)
- **All Releases:** [Release Notes Index](docs/releases/README.md)
- **GitHub Releases:** [Tags & Downloads](https://github.com/routerjoe/red-river-sales-automation/releases)

## Documentation

- [CHANGELOG.md](CHANGELOG.md) - Version history and release notes
- [docs/releases/](docs/releases/) - Detailed release notes by version
- [docs/PHASE3_OVERVIEW.md](docs/PHASE3_OVERVIEW.md) - Phase 3 feature overview
- [docs/architecture_phase3.md](docs/architecture_phase3.md) - Architecture diagrams
- [RUNBOOK.md](RUNBOOK.md) - Operational procedures
- [TUI README](tui/README.md) - TUI-specific documentation

## Release History

- **v1.4.0** (2025-10-28) - Phase 4: Forecast & Govly Automation Batch
  - Forecast Hub Engine with multi-year projections
  - Govly/Radar webhook ingestion
  - Metrics & latency monitoring
  - 101 tests passing
  - [Full Release Notes →](docs/releases/v1.4.0.md)

- **v1.3.0** (2025-10-26) - Phase 3: Integrations & Dashboard Enhancements
  - AI Router with 6 models
  - System monitoring & logging
  - Federal FY routing
  - [Overview →](docs/guides/phase3_overview.md)

**📋 [All Releases →](docs/releases/)** | **📝 [CHANGELOG →](CHANGELOG.md)**

## Contributing

This is a proprietary project for DealCraft. For internal contributions:

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and add tests
3. Run quality checks: `kc run:build`
4. Commit with conventional commits: `feat:`, `fix:`, `docs:`, etc.
5. Push and create a PR

## License

Proprietary - DealCraft

---

**Built with** FastAPI, Textual, Obsidian, and powered by AI ✨
