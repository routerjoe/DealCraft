# Architecture Documentation

System architecture and design documentation for DealCraft.

## Available Documentation

### Phase 3 Architecture
- **File:** [phase3.md](phase3.md)
- **Version:** v1.3.0
- **Last Updated:** October 26, 2025
- **Topics:**
  - System overview and high-level architecture
  - Component details (Client Layer, API Layer, Core Services)
  - Data storage (state.json, Obsidian vault)
  - Data flow diagrams
  - Technology stack
  - Security and scalability considerations

### Phase 4 Architecture (Planned)
- **Status:** In development
- **Version:** v1.4.0+
- **Topics:** Forecast engine, webhook ingestion, metrics monitoring

## Architecture Highlights

### System Components

```
Client Layer (TUI, CLI, API Clients)
    ↓
API Layer (FastAPI with Middleware)
    ↓
Core Services (AI Router, State Store, FY Calculator, Logger)
    ↓
Data Storage (state.json, Obsidian Vault, Dashboards)
```

### Key Features
- **FastAPI-based** web framework with async support
- **Multi-model AI routing** (OpenAI, Anthropic, Gemini)
- **Atomic JSON persistence** for state management
- **Federal FY routing** for opportunity organization
- **Request tracking** with UUID and latency monitoring
- **Structured logging** with JSON format

### Performance Metrics
- Average API latency: <3ms
- P95 latency: <5ms
- P99 latency: <10ms
- Test suite execution: ~3 seconds
- Test count: 101 passing

## Related Documentation
- [Phase 3 Overview](../guides/phase3_overview.md) - Feature descriptions
- [API Endpoints](../api/endpoints.md) - Complete API reference
- [Releases](../releases/) - Version history and changelogs

---

**Note:** Architecture documentation is updated with each major release.