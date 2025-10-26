# Red River Sales MCP API

FastAPI-based Model Context Protocol API for Red River Sales Automation.

## Features

- 🚀 FastAPI web framework with async support
- 📝 Structured JSON logging with request tracking
- 🔍 Request ID tracking and latency measurement
- 🏥 Health check and API info endpoints
- 🧪 Comprehensive test coverage
- 🎨 Textual TUI for interactive management

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

### 4. Run Tests

```bash
# Using Kilo Code
kc run:test

# Or directly
bash scripts/test.sh
```

### 5. Run Linter

```bash
# Using Kilo Code
kc run:lint

# Or directly
bash scripts/lint.sh
```

## API Endpoints

### Health & Info
- `GET /healthz` - Health check endpoint
- `GET /v1/info` - API information

### OEMs
- `GET /v1/oems` - List all OEMs
- `POST /v1/oems` - Create a new OEM
  - Body: `{"name": "string", "authorized": boolean, "threshold": integer}`
- `PATCH /v1/oems/{name}` - Update an OEM (partial updates)
  - Body: `{"authorized": boolean, "threshold": integer}` (all fields optional)
- `DELETE /v1/oems/{name}` - Delete an OEM

### Contract Vehicles
- `GET /v1/contracts` - List all Contract Vehicles
- `POST /v1/contracts` - Create a new Contract Vehicle
  - Body: `{"name": "string", "supported": boolean, "notes": "string"}`
- `PATCH /v1/contracts/{name}` - Update a Contract Vehicle (partial updates)
  - Body: `{"supported": boolean, "notes": "string"}` (all fields optional)
- `DELETE /v1/contracts/{name}` - Delete a Contract Vehicle

**Note:** All create endpoints return `409 Conflict` if a resource with the same name already exists. All update/delete endpoints return `404 Not Found` if the resource doesn't exist.

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

Every response includes an `X-Request-ID` header for request tracking.

## Project Structure

```
red-river-sales-automation/
├── mcp/
│   ├── api/              # API endpoints
│   │   └── main.py       # FastAPI application
│   └── core/             # Core modules
│       ├── config.py     # Configuration loader
│       └── logging.py    # JSON logging setup
├── scripts/              # Shell scripts
│   ├── dev.sh           # Development server
│   ├── test.sh          # Run tests
│   ├── lint.sh          # Run linter
│   └── build.sh         # Build checks
├── tests/               # Test suite
│   └── test_health.py   # Health endpoint tests
├── .env.sample          # Environment template
├── logging.json         # Logging configuration
├── requirements.txt     # Python dependencies
└── kilo.yml            # Kilo Code task aliases
```

## Development

### Kilo Code Tasks

```bash
kc run:dev    # Start development server
kc run:test   # Run test suite
kc run:lint   # Run linter
kc run:build  # Run lint + tests
```

### Environment Variables

See [`.env.sample`](.env.sample) for all available configuration options.

## License

Proprietary - Red River Sales Automation