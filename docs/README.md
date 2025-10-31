# DealCraft — Documentation

Welcome to the complete documentation for DealCraft MCP API.

## Quick Links

### 📚 Getting Started
- [Main README](../README.md) - Project overview and quick start
- [CHANGELOG](../CHANGELOG.md) - Version history and release notes
- [API Endpoints](api/endpoints.md) - Complete API reference

### 🏗️ Architecture
- [Architecture Overview](architecture/) - System design and components
- [Phase 3 Architecture](architecture/phase3.md) - Current architecture details

### 📖 Guides & Tutorials
- [Guides Index](guides/) - All available guides
- [Phase 3 Overview](guides/phase3_overview.md) - Latest features and capabilities

### 🚀 Releases
- [Release Index](releases/) - All release notes
- [Latest: v1.4.0](releases/v1.4.0.md) - Phase 4: Forecast & Govly Automation (Oct 28, 2025)
- [v1.3.0](releases/) - Phase 3: Documentation Enhancements (Oct 26, 2025)

### 🔌 API Reference
- [API Endpoints](api/endpoints.md) - Complete endpoint documentation
- Core, AI, System, Obsidian, Contacts, Email, OEM, Contracts
- Forecast, Metrics, Webhooks (v1.4.0+)

### 🎨 TUI Interface
- [TUI Preview](tui/preview.md) - Terminal UI documentation and screenshots

### 📝 Obsidian Integration
- [Obsidian Docs](obsidian/) - Vault integration and dashboard documentation
- Opportunity templates, FY routing, Dataview queries

## Documentation by Topic

### Installation & Setup
- [Main README — Quick Start](../README.md#quick-start)
- Environment configuration
- Running the API server
- Launching the TUI

### API Usage
- [Endpoint Reference](api/endpoints.md)
- Request/response formats
- Error handling
- Performance targets

### Features

#### AI & Intelligence
- Multi-model AI routing (6 models, 3 providers)
- Unified AI query interface
- RFQ guidance generation
- [API Documentation](api/endpoints.md#ai--intelligence)

#### Forecasting (v1.4.0+)
- Multi-year projections (FY25, FY26, FY27)
- Confidence scoring (0-100)
- Aggregate analytics
- [Release Notes](releases/v1.4.0.md#1-forecast-hub-engine)

#### System Monitoring
- Request tracking with UUID
- Latency measurement
- Recent actions log (last 10)
- Metrics and performance monitoring (v1.4.0+)
- [Architecture Details](architecture/phase3.md#monitoring--observability)

#### Obsidian Integration
- Federal FY routing for opportunities
- Automated dashboard generation
- Dataview query support
- Webhook-ingested opportunity notes (v1.4.0+)
- [Obsidian Documentation](obsidian/)

#### Webhook Ingestion (v1.4.0+)
- Govly federal opportunities
- Radar contract modifications
- Automatic opportunity creation
- [API Documentation](api/endpoints.md#webhook-ingestion-v140)

### Development

#### Testing
- 101 tests passing (v1.4.0)
- Comprehensive test coverage
- Performance benchmarks
- [Testing Strategy](guides/phase3_overview.md#testing-strategy)

#### Architecture
- FastAPI with async support
- Atomic JSON persistence
- Multi-model AI routing
- Request/response middleware
- [Architecture Documentation](architecture/)

#### Contributing
- Code quality standards
- Conventional commits
- Testing requirements
- [Main README — Contributing](../README.md#contributing)

## Version History

| Version | Date | Status | Notes |
|---------|------|--------|-------|
| v1.4.0 | 2025-10-28 | Current | Forecast, webhooks, metrics |
| v1.3.0 | 2025-10-26 | Stable | AI routing, FY routing, dashboards |

See [Release Notes](releases/) for complete version history.

## Performance Metrics

### Current Performance (v1.4.0)
- **Average API Latency:** ~3ms (forecast: ~45ms)
- **P95 Latency:** <5ms
- **P99 Latency:** <10ms
- **Test Suite Execution:** ~4.3s
- **Test Count:** 101 passing
- **Build Time:** ~6s

### Targets
- Average latency <250ms
- P95 latency <500ms
- Test coverage >90%

## Support & Resources

### Documentation Locations
- **Project Root:** README.md, CHANGELOG.md
- **Documentation:** `/docs` (this directory)
- **API Code:** `/mcp/api/`
- **TUI Code:** `/tui/`
- **Tests:** `/tests/`

### External Links
- [GitHub Repository](https://github.com/routerjoe/DealCraft)
- [GitHub Releases](https://github.com/routerjoe/DealCraft/releases)
- [Issue Tracker](https://github.com/routerjoe/DealCraft/issues)

## Documentation Updates

This documentation is maintained alongside the codebase and updated with each major release.

**Last Major Update:** v1.4.0 — October 28, 2025 EDT

---

**Navigate:** [← Back to Project Root](../README.md) | [Releases →](releases/) | [Architecture →](architecture/) | [API Reference →](api/endpoints.md)