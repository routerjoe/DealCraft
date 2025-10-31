# Slack Bot Integration Guide

**Version:** 1.0  
**Last Updated:** October 29, 2025 EDT  
**Sprint:** 11 - Slack Bot + MCP Bridge

## Overview

The DealCraft Slack bot provides real-time access to sales intelligence through slash commands. Team members can query forecasts, get CV recommendations, and view recent activity directly from Slack channels.

## Features

- 📊 **Forecast Queries** - View top opportunities and pipeline projections
- 🎯 **CV Recommendations** - Get contract vehicle suggestions for agencies
- 📝 **Recent Activity** - Track system events and changes
- 🔒 **Role-Based Permissions** - Control access by workspace role
- 🧪 **Dry-Run Mode** - Test commands without side effects
- ⚡ **Fast Responses** - Sub-second command execution

## Slash Commands

### `/rr forecast top`

Get the top forecasted opportunities from the pipeline.

**Usage:**
```
/rr forecast top [count]
```

**Parameters:**
- `count` (optional): Number of opportunities to show (default: 5, max: 20)

**Examples:**
```
/rr forecast top           # Show top 5 opportunities
/rr forecast top 10        # Show top 10 opportunities
/rr forecast top 20        # Show maximum 20 opportunities
```

**Response Format:**
```
🎯 Top 5 Forecasted Opportunities

1. Federal Cloud Migration - GSA
   Amount: $2.5M | Close: 2025-12-15 | Score: 0.87

2. DEPARTMENT-ALPHA Cybersecurity Refresh - DEPARTMENT-ALPHA
   Amount: $1.8M | Close: 2025-11-30 | Score: 0.82

3. NASA Data Center Upgrade - NASA
   Amount: $3.2M | Close: 2026-01-20 | Score: 0.79

4. VA Electronic Health Records - VA
   Amount: $1.2M | Close: 2025-12-01 | Score: 0.76

5. DHS Network Modernization - DHS
   Amount: $2.0M | Close: 2026-02-10 | Score: 0.73

Total Pipeline Value: $10.7M
Data as of: 2025-10-29 13:00 EDT
```

**Permissions Required:** Member (read-only access)

---

### `/rr cv recommend`

Get contract vehicle recommendations for federal opportunities.

**Usage:**
```
/rr cv recommend [agency]
```

**Parameters:**
- `agency` (optional): Filter by federal agency code or name

**Examples:**
```
/rr cv recommend           # All available CVs
/rr cv recommend DEPARTMENT-ALPHA       # DEPARTMENT-ALPHA-specific CVs
/rr cv recommend "Air Force"  # AGENCY-ALPHA/AGENCY-BRAVO CVs
```

**Response Format:**
```
📋 Contract Vehicle Recommendations

🏆 SEWP VI (NASA GSFC)
   Eligibility: ✅ Certified Prime
   Categories: IT Hardware, Software, Services
   Ceiling: $50B | Expires: 2031
   Best for: Federal IT procurement, short lead times

⭐ GSA MAS (Schedule 70)
   Eligibility: ✅ Active Contract
   Categories: IT Solutions, Cloud Services
   Ceiling: No limit | Expires: 2027
   Best for: Broad federal access, flexible pricing

💼 CHESS (Army)
   Eligibility: ⚠️ Teaming Required
   Categories: Hardware, Software, Services
   Ceiling: $8B | Expires: 2028
   Best for: Army-specific requirements

Use /rr cv details [name] for full information
```

**Permissions Required:** Member (read-only access)

---

### `/rr recent`

Show recent system activity including webhooks, opportunities, and changes.

**Usage:**
```
/rr recent [hours]
```

**Parameters:**
- `hours` (optional): Lookback window in hours (default: 24, max: 168)

**Examples:**
```
/rr recent            # Last 24 hours
/rr recent 48         # Last 2 days
/rr recent 168        # Last week
```

**Response Format:**
```
📅 Recent Activity (Last 24 hours)

🆕 New Opportunities (3)
  • Federal IT Modernization - GSA ($500K)
  • Cloud Migration Phase 2 - DEPARTMENT-ALPHA ($1.2M)
  • Data Center Refresh - NASA ($800K)

📥 Webhook Events (5)
  • Govly: 3 opportunities ingested
  • Radar: 2 contract modifications detected

🔄 Updates (2)
  • Opportunity "Network Upgrade" moved to FY26
  • CV recommendation engine updated

⚡ System Health: All services operational
Last updated: 2025-10-29 13:00 EDT
```

**Permissions Required:** Member (read-only access)

---

## Permission Model

### Workspace Roles

Commands are authorized based on Slack workspace roles:

| Role | Access Level | Commands Available |
|------|-------------|-------------------|
| **Owner** | Full access | All commands + admin functions |
| **Admin** | Full access | All commands + configuration |
| **Member** | Read-only | Query commands (forecast, cv, recent) |
| **Guest** | No access | Denied |

### Command Permissions

| Command | Owner | Admin | Member | Guest |
|---------|-------|-------|--------|-------|
| `/rr forecast top` | ✅ | ✅ | ✅ | ❌ |
| `/rr cv recommend` | ✅ | ✅ | ✅ | ❌ |
| `/rr recent` | ✅ | ✅ | ✅ | ❌ |
| `/rr config` (future) | ✅ | ✅ | ❌ | ❌ |
| `/rr admin` (future) | ✅ | ❌ | ❌ | ❌ |

### Permission Errors

When a user lacks permission:
```
🔒 Permission Denied

You don't have access to this command.

Required role: Member
Your role: Guest

Contact your workspace admin to request access.
```

---

## Installation Guide

### Prerequisites

- Slack workspace with admin access
- Red River Sales MCP API running
- Public endpoint or ngrok for local development

### Step 1: Create Slack App

1. Visit [api.slack.com/apps](https://api.slack.com/apps)
2. Click **"Create New App"**
3. Select **"From scratch"**
4. Enter app name: `Red River Sales Bot`
5. Select your workspace
6. Click **"Create App"**

### Step 2: Configure OAuth & Permissions

1. Navigate to **"OAuth & Permissions"**
2. Scroll to **"Scopes"** section
3. Add Bot Token Scopes:
   - `commands` - Slash command access
   - `chat:write` - Send messages
   - `users:read` - Read user info for permissions
   - `channels:read` - Read channel info

4. Click **"Install to Workspace"**
5. Authorize the app
6. Copy the **"Bot User OAuth Token"** (starts with `xoxb-`)

### Step 3: Configure Slash Commands

1. Navigate to **"Slash Commands"**
2. Click **"Create New Command"**

**For `/rr forecast`:**
- Command: `/rr`
- Request URL: `https://your-domain.com/v1/slack/command`
- Short Description: `Red River sales automation commands`
- Usage Hint: `forecast top [count] | cv recommend [agency] | recent [hours]`

3. Click **"Save"**

### Step 4: Get Signing Secret

1. Navigate to **"Basic Information"**
2. Scroll to **"App Credentials"**
3. Copy the **"Signing Secret"**

### Step 5: Configure Environment Variables

Add to your `.env` file:

```bash
# Slack Bot Configuration
SLACK_BOT_TOKEN=xox*-***
SLACK_SIGNING_SECRET=your-signing-secret-here
SLACK_ENABLED=true
SLACK_DEFAULT_CHANNEL=#sales-automation
```

### Step 6: Restart Services

```bash
# Restart MCP API
pm2 restart mcp-api

# Or if using docker
docker-compose restart api
```

### Step 7: Test Commands

In any Slack channel:
```
/rr forecast top 5
```

You should see a response with top opportunities!

---

## Configuration

### Environment Variables

Required variables in `.env`:

```bash
# Slack Bot Token (required)
SLACK_BOT_TOKEN=xox*-***

# Slack Signing Secret (required)
SLACK_SIGNING_SECRET=YOUR-SIGNING-SECRET-HERE

# Enable/Disable Slack integration (optional)
SLACK_ENABLED=true

# Default channel for bot messages (optional)
SLACK_DEFAULT_CHANNEL=#sales-automation

# Command timeout in seconds (optional)
SLACK_COMMAND_TIMEOUT=3

# Enable dry-run mode (optional, for testing)
SLACK_DRY_RUN=false
```

### Token Security

**CRITICAL SECURITY NOTES:**

1. **Never commit tokens to git**
   - Tokens in `.env` file
   - Add `.env` to `.gitignore`
   - Use separate tokens for dev/staging/production

2. **Token rotation**
   - Rotate tokens every 90 days
   - Immediately rotate if compromised
   - Test new token before removing old

3. **Token storage**
   - Store in environment variables only
   - Use secrets manager in production (AWS Secrets Manager, HashiCorp Vault)
   - Never log tokens

### Token Rotation Procedure

1. **Generate new token:**
   - Visit Slack App settings
   - Navigate to "OAuth & Permissions"
   - Click "Reinstall to Workspace"
   - Copy new Bot User OAuth Token

2. **Update environment:**
   ```bash
   # Temporarily support both tokens
   SLACK_BOT_TOKEN=new-token-here
   SLACK_BOT_TOKEN_OLD=old-token-here
   ```

3. **Deploy and test:**
   ```bash
   # Test with new token
   /rr forecast top 5
   ```

4. **Remove old token:**
   ```bash
   # After 24 hours, remove old token
   SLACK_BOT_TOKEN=new-token-here
   ```

---

## Command Parsing

Commands are parsed with the following grammar:

```
/rr <action> <subaction> [args]
```

**Examples:**
- `/rr forecast top` → action: forecast, subaction: top
- `/rr forecast top 10` → action: forecast, subaction: top, args: [10]
- `/rr cv recommend DEPARTMENT-ALPHA` → action: cv, subaction: recommend, args: [DEPARTMENT-ALPHA]

### Argument Types

- **Numeric:** `10`, `20`, `168`
- **String:** `DEPARTMENT-ALPHA`, `"Air Force"`, `GSA`
- **Flags:** `--dry-run`, `--verbose`

### Error Handling

Invalid commands return helpful errors:

```
❌ Invalid Command

Usage: /rr <command> [options]

Available commands:
  • forecast top [count]
  • cv recommend [agency]
  • recent [hours]

Example: /rr forecast top 10

Type /rr help for detailed documentation.
```

---

## Dry-Run Mode

Test commands without side effects using dry-run mode.

### Enabling Dry-Run

**Environment Variable:**
```bash
SLACK_DRY_RUN=true
```

**Per-Command Flag:**
```
/rr forecast top --dry-run
```

### Dry-Run Response

Commands in dry-run mode return preview of what would execute:

```
🧪 Dry-Run Mode

Command: /rr forecast top 5
Would execute: GET /v1/forecast/top?count=5
Expected response: List of 5 opportunities
Estimated latency: ~200ms

No actual data returned in dry-run mode.
Use without --dry-run to execute.
```

---

## Monitoring & Debugging

### Logging

All Slack commands are logged in structured JSON:

```json
{
  "timestamp": "2025-10-29T13:00:00Z",
  "level": "INFO",
  "message": "Slack command executed",
  "command": "/rr forecast top 5",
  "user_id": "U***-***-****",
  "channel_id": "C***-***-****",
  "team_id": "T***-***-****",
  "response_time_ms": 245,
  "status": "success"
}
```

### Error Tracking

Failed commands include error details:

```json
{
  "timestamp": "2025-10-29T13:00:00Z",
  "level": "ERROR",
  "message": "Slack command failed",
  "command": "/rr forecast top 5",
  "error": "MCP API timeout",
  "error_code": "TIMEOUT",
  "user_id": "U***-***-****"
}
```

### Common Issues

#### Issue: Command Not Found

**Symptom:** `/rr` command doesn't work

**Causes:**
- Slash command not configured in Slack app
- Bot not installed to workspace
- Incorrect request URL

**Solution:**
1. Check Slack app "Slash Commands" configuration
2. Verify bot is installed in workspace
3. Test request URL with curl:
   ```bash
   curl https://your-domain.com/v1/slack/command
   ```

#### Issue: Permission Denied

**Symptom:** User gets permission denied error

**Causes:**
- User role not sufficient
- Bot lacks required OAuth scopes
- Permission model misconfigured

**Solution:**
1. Check user's workspace role
2. Verify bot has required scopes
3. Review permission model configuration

#### Issue: Timeout Error

**Symptom:** Command times out after 3 seconds

**Causes:**
- MCP API slow response
- Network latency
- Command processing too slow

**Solution:**
1. Implement async processing with `response_url`
2. Add caching for frequent queries
3. Optimize MCP API response time

---

## Best Practices

### Command Design

1. **Keep commands simple** - Single responsibility per command
2. **Provide helpful errors** - Guide users to correct usage
3. **Use consistent formatting** - Standard response templates
4. **Include context** - Timestamps, data freshness indicators
5. **Support defaults** - Sensible defaults for optional parameters

### Performance

1. **Cache frequently accessed data** - Forecast rankings, CV lists
2. **Implement timeouts** - Fail gracefully after 3 seconds
3. **Use async processing** - Long queries via response_url
4. **Batch requests** - Combine multiple API calls
5. **Monitor latency** - Track P50/P95/P99 response times

### Security

1. **Validate signatures** - Verify requests from Slack
2. **Implement rate limiting** - Prevent abuse
3. **Log all commands** - Audit trail for security
4. **Sanitize inputs** - Prevent injection attacks
5. **Use bot tokens** - Never user tokens for automation

---

## Future Enhancements

Planned for post-Sprint 11:

- **Interactive Components** - Buttons, modals, select menus
- **Scheduled Reports** - Daily/weekly pipeline summaries
- **Alerts & Notifications** - Real-time opportunity alerts
- **Advanced Permissions** - User-level ACLs
- **Multi-Workspace Support** - Enterprise deployment
- **Slack Bolt Migration** - Better framework support
- **Message Shortcuts** - Quick actions from messages
- **App Home Tab** - Personalized dashboard

---

## Support & Troubleshooting

For Slack bot issues:

1. Check application logs for errors
2. Verify environment variables are set
3. Test MCP API endpoints directly
4. Review Slack app configuration
5. Consult [RUNBOOK.md](../RUNBOOK.md) for operational procedures

**Related Documentation:**
- [Sprint 11 Plan](../docs/sprint_plan.md)
- [API Endpoints](../api/endpoints.md)
- [MCP Tools](../guides/README.md)