# API Endpoints Reference

Complete reference for all Red River Sales MCP API endpoints.

## Core Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/healthz` | Health check endpoint |
| `GET` | `/v1/info` | API information and available endpoints |

## AI & Intelligence

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/ai/ask` | Unified AI query interface (multi-model) |
| `GET` | `/v1/ai/models` | List available AI models (6 models) |
| `GET` | `/v1/ai/models/detailed` | Detailed model info with providers |
| `POST` | `/v1/ai/guidance` | Generate RFQ guidance with AI analysis |

### AI Models

**OpenAI:**
- `gpt-5-thinking` (default)
- `gpt-4-turbo`

**Anthropic:**
- `claude-3.5`
- `claude-3-opus`

**Gemini:**
- `gemini-1.5-pro`
- `gemini-1.5-flash`

## System Monitoring

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/system/recent-actions` | Last 10 API requests with metadata |

## Obsidian Integration

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/obsidian/opportunity` | Create opportunity note with FY routing |

## Contacts Export

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/contacts/export.csv` | Export contacts as CSV (RFC 4180) |
| `GET` | `/v1/contacts/export.vcf` | Export contacts as vCard 3.0 |

## Email Ingestion

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/email/rfq/ingest` | Ingest RFQ email for processing |
| `POST` | `/v1/email/govly/ingest` | Ingest Govly event notification |
| `POST` | `/v1/email/intromail/ingest` | Ingest IntroMail for analysis |

## OEM Management

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/oems` | List all OEMs |
| `POST` | `/v1/oems` | Create new OEM |
| `PATCH` | `/v1/oems/{name}` | Update OEM (partial) |
| `DELETE` | `/v1/oems/{name}` | Delete OEM |

**OEM Body Schema:**
```json
{
  "name": "string",
  "authorized": boolean,
  "threshold": integer
}
```

## Contract Vehicles

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/contracts` | List all contract vehicles |
| `POST` | `/v1/contracts` | Create new contract vehicle |
| `PATCH` | `/v1/contracts/{name}` | Update contract (partial) |
| `DELETE` | `/v1/contracts/{name}` | Delete contract |

**Contract Body Schema:**
```json
{
  "name": "string",
  "supported": boolean,
  "notes": "string"
}
```

## Forecast & Metrics (v1.4.0+)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/forecast/run` | Generate multi-year forecasts (FY25, FY26, FY27) |
| `GET` | `/v1/forecast/summary` | Aggregate forecast analytics with confidence tiers |
| `GET` | `/v1/metrics` | Comprehensive performance metrics |
| `POST` | `/v1/metrics/accuracy` | Record accuracy results |
| `GET` | `/v1/metrics/health` | Health check endpoint |

## Webhook Ingestion (v1.4.0+)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/govly/webhook` | Ingest federal opportunity events from Govly |
| `POST` | `/v1/radar/webhook` | Ingest contract modifications from Radar |

## Response Headers

All API responses include:
- `x-request-id`: UUID4 for distributed tracing
- `x-latency-ms`: Request duration in milliseconds

## Error Responses

- `409 Conflict` - Resource already exists (create operations)
- `404 Not Found` - Resource not found (update/delete operations)
- `422 Unprocessable Entity` - Invalid request payload
- `500 Internal Server Error` - Server error

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Average Latency | <250ms | ~3ms |
| P95 Latency | <500ms | <5ms |
| P99 Latency | <1000ms | <10ms |

---

See also:
- [Full API Documentation](../../README.md)
- [Architecture Overview](../architecture/phase3.md)
- [Release Notes](../releases/)