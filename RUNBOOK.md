# DealCraft API - Runbook

Operational guide for the DealCraft Model Context Protocol API and TUI.

## Table of Contents

1. [Setup](#setup)
2. [Environment Variables](#environment-variables)
3. [Running the Application](#running-the-application)
4. [API Endpoints](#api-endpoints)
5. [TUI Usage](#tui-usage)
6. [Troubleshooting](#troubleshooting)
7. [Development](#development)

## Setup

### Prerequisites

- Python 3.11 or higher
- pip package manager
- (Optional) Kilo Code CLI for task aliases

### Installation

1. **Clone the repository**
   ```bash
   cd /path/to/DealCraft
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.sample .env
   # Edit .env as needed (defaults work for local development)
   ```

4. **Initialize data directory**
   ```bash
   # data/state.json is created automatically if missing
   # Default structure includes empty oems, contracts, and default AI model
   ```

## Environment Variables

All configuration is managed through the `.env` file. See [`.env.sample`](.env.sample) for defaults.

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | API server bind address |
| `API_PORT` | `8000` | API server port |
| `API_RELOAD` | `true` | Enable auto-reload in development |
| `ENVIRONMENT` | `development` | Environment name (development/production) |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |

**Security Note:** Never commit `.env` to version control. Use `.env.sample` as a template.

## Running the Application

### Using Kilo Code (Recommended)

```bash
kc run:dev     # Start API development server
kc run:test    # Run test suite
kc run:lint    # Run code linter
kc run:build   # Run lint + tests
kc run:tui     # Launch TUI (requires API to be running)
```

### Using Shell Scripts Directly

```bash
bash scripts/dev.sh      # Start API server
bash scripts/test.sh     # Run tests
bash scripts/lint.sh     # Run linter
bash scripts/build.sh    # Full build check
```

### Manual Commands

```bash
# API Server
uvicorn mcp.api.main:app --host 0.0.0.0 --port 8000 --reload

# Tests
pytest -q tests/

# Linter
ruff check mcp/api/ mcp/core/ tests/ --exclude mcp/cli.py

# TUI
python -m tui.app
```

## API Endpoints

### Health & Info

- **GET** `/healthz`
  - Returns: `{"status": "healthy"}`
  - Headers: `X-Request-ID`

- **GET** `/v1/info`
  - Returns: `{"name": "...", "version": "...", "environment": "..."}`
  - Headers: `X-Request-ID`

### OEMs

- **GET** `/v1/oems`
  - Returns: Array of OEM objects

- **POST** `/v1/oems`
  - Body: `{"name": "string", "authorized": boolean, "threshold": integer}`
  - Returns: Created OEM object
  - Status: `201 Created` or `409 Conflict` (duplicate name)

- **PATCH** `/v1/oems/{name}`
  - Body: `{"authorized": boolean, "threshold": integer}` (partial)
  - Returns: Updated OEM object
  - Status: `200 OK` or `404 Not Found`

- **DELETE** `/v1/oems/{name}`
  - Returns: No content
  - Status: `204 No Content` or `404 Not Found`

### Contract Vehicles

- **GET** `/v1/contracts`
  - Returns: Array of contract objects

- **POST** `/v1/contracts`
  - Body: `{"name": "string", "supported": boolean, "notes": "string"}`
  - Returns: Created contract object
  - Status: `201 Created` or `409 Conflict` (duplicate name)

- **PATCH** `/v1/contracts/{name}`
  - Body: `{"supported": boolean, "notes": "string"}` (partial)
  - Returns: Updated contract object
  - Status: `200 OK` or `404 Not Found`

- **DELETE** `/v1/contracts/{name}`
  - Returns: No content
  - Status: `204 No Content` or `404 Not Found`

### AI

- **GET** `/v1/ai/models`
  - Returns: `["gpt-5-thinking", "claude-3.5", "gemini-1.5-pro"]`

- **POST** `/v1/ai/guidance`
  - Body:
    ```json
    {
      "oems": [{"name": "...", "authorized": true}],
      "contracts": [{"name": "...", "supported": true}],
      "rfq_text": "...",
      "model": "gpt-5-thinking"
    }
    ```
  - Returns:
    ```json
    {
      "summary": "...",
      "actions": ["...", "..."],
      "risks": ["..."]
    }
    ```

## TUI Usage

See [`README_TUI.md`](README_TUI.md) for detailed TUI documentation.

### Basic Workflow

1. **Start API server** (in terminal 1)
   ```bash
   kc run:dev
   ```

2. **Launch TUI** (in terminal 2)
   ```bash
   kc run:tui
   ```

3. **Manage OEMs**
   - Press `A` to add OEMs
   - Press `T` to toggle authorization
   - Use `↑↓` to adjust thresholds

4. **Manage Contracts**
   - Press `C` to add contracts
   - Press `S` to toggle support
   - Press `E` to edit notes

5. **Generate AI Guidance**
   - Press `I` to select AI model
   - Press `G` to generate guidance

## Troubleshooting

### API Server Issues

**Problem:** Server won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill process if needed
kill -9 <PID>
```

**Problem:** Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Verify Python version
python --version  # Should be 3.11+
```

### Data Persistence Issues

**Problem:** Changes not persisting
```bash
# Check data/state.json exists and is writable
ls -la data/state.json

# Verify file permissions
chmod 644 data/state.json

# Check for write errors in logs
```

**Problem:** Corrupted state file
```bash
# Backup existing file
cp data/state.json data/state.json.bak

# Reset to default
cat > data/state.json << 'EOF'
{
  "oems": [],
  "contracts": [],
  "selected_ai": "gpt-5-thinking"
}
EOF
```

### TUI Issues

**Problem:** TUI won't connect to API
```bash
# Verify API is running
curl http://localhost:8000/healthz

# Check API logs for errors
# Ensure API_HOST and API_PORT match in .env
```

**Problem:** TUI crashes or freezes
```bash
# Check terminal size (minimum 80x24 recommended)
# Restart TUI: Ctrl+C then kc run:tui
# Check for API connectivity issues
```

### Test Failures

**Problem:** Tests fail
```bash
# Run tests with verbose output
pytest -v tests/

# Run specific test file
pytest -v tests/test_oems.py

# Check for file permission issues with temp files
```

### Lint Errors

**Problem:** Lint errors in new code
```bash
# Auto-fix common issues
ruff check --fix mcp/api/ mcp/core/ tests/

# View specific errors
ruff check mcp/api/ mcp/core/ tests/
```

## Development

### Adding New Endpoints

1. Create router file in `mcp/api/v1/`
2. Define Pydantic models for request/response
3. Implement endpoint functions
4. Include router in `mcp/api/main.py`
5. Write tests in `tests/`
6. Update this runbook and README

### Adding New TUI Panels

1. Create panel file in `tui/panels/`
2. Implement key bindings and UI logic
3. Add panel to `tui/app.py` layout
4. Update `README_TUI.md` with keyboard shortcuts
5. Test with `kc run:tui`

### Running Tests in Watch Mode

```bash
# Install pytest-watch
pip install pytest-watch

# Run tests on file changes
ptw tests/
```

## Logging

All API requests are logged in JSON format to stdout. Each log entry includes:

- `timestamp` - ISO format timestamp
- `level` - Log level (INFO, WARNING, ERROR)
- `message` - Log message
- `request_id` - Unique request identifier
- `method` - HTTP method (GET, POST, etc.)
- `path` - Request path
- `status` - HTTP status code
- `latency_ms` - Request duration in milliseconds

Example log entry:
```json
{
  "timestamp": "2025-10-26 03:30:45,123",
  "level": "INFO",
  "message": "GET /v1/oems 200",
  "request_id": "a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5g6h7",
  "latency_ms": 1.23,
  "method": "GET",
  "path": "/v1/oems",
  "status": 200
}
```

### Log Aggregation

For production deployments, configure log aggregation:

```bash
# Example: Forward logs to file
kc run:dev 2>&1 | tee api.log

# Example: Forward to logging service
kc run:dev 2>&1 | your-log-forwarder
```

## Data Storage

### File Structure

Data is stored in `data/state.json` with atomic writes to prevent corruption.

```json
{
  "oems": [
    {"name": "Dell", "authorized": true, "threshold": 1000}
  ],
  "contracts": [
    {"name": "GSA Schedule", "supported": true, "notes": "Federal vehicle"}
  ],
  "selected_ai": "gpt-5-thinking"
}
```

### Backup Strategy

```bash
# Manual backup
cp data/state.json data/state.json.backup

# Automated daily backups (cron example)
0 2 * * * cp /path/to/data/state.json /path/to/backups/state-$(date +\%Y\%m\%d).json
```

## Monitoring

### Health Checks

```bash
# Basic health check
curl http://localhost:8000/healthz

# API info
curl http://localhost:8000/v1/info

# Monitor with watch
watch -n 5 curl -s http://localhost:8000/healthz
```

### Performance Metrics

Monitor `latency_ms` in logs to identify slow endpoints:

```bash
# Extract latency metrics from logs
grep latency_ms api.log | jq .latency_ms | awk '{sum+=$1; count++} END {print "Avg:", sum/count, "ms"}'
```

## Security

### Best Practices

1. **Never commit secrets** - Use `.env` for sensitive data
2. **Rotate credentials** - Periodically update any API keys (when implemented)
3. **Monitor access** - Review logs for unusual patterns
4. **Validate input** - All endpoints use Pydantic validation
5. **Limit exposure** - Use firewall rules in production

### Production Deployment

For production deployments:

1. Set `ENVIRONMENT=production` in `.env`
2. Use a production WSGI server (e.g., gunicorn)
3. Configure proper logging aggregation
4. Set up automated backups
5. Implement proper authentication/authorization (TODO)
6. Use HTTPS with proper certificates

## Support

For issues or questions:

1. Check this runbook first
2. Review API logs for error details
3. Run diagnostic commands in Troubleshooting section
4. Check test output: `kc run:test -v`

## Maintenance

### Regular Tasks

- **Daily**: Review logs for errors
- **Weekly**: Run full test suite: `kc run:build`
- **Monthly**: Update dependencies: `pip install --upgrade -r requirements.txt`
- **As needed**: Backup `data/state.json`

### Version Updates

```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Run tests to verify compatibility
kc run:build

# Update requirements.txt if needed
pip freeze > requirements.txt
