# Sprint 11: Slack Bot + MCP Bridge

**Start:** Wednesday, October 29, 2025 EDT  
**Target Merge Window:** Monday, November 10, 2025 EDT

## Objectives

- Implement Slack bot integration for Red River Sales automation
- Bridge MCP tools to Slack slash commands
- Enable real-time sales team notifications and queries
- Support key workflows: forecast queries, CV recommendations, recent activity
- Establish permission model for command authorization
- Provide dry-run mode for testing without side effects

## Scope (In)

- Slash command handlers:
  - `/rr forecast top` - Top forecasted opportunities
  - `/rr cv recommend` - CV/contract vehicle recommendations
  - `/rr recent` - Recent system activity
- Command parsing and validation
- Queue management for async processing
- Dry-run mode for testing
- Permission model (role-based access)
- Slack workspace integration guide
- Environment variable configuration
- TypeScript stub implementation
- Python integration tests

## Scope (Out)

- Interactive Slack components (buttons, modals)
- Slack Events API subscriptions
- Real-time webhook notifications
- Multi-workspace support
- Advanced permission granularity (user-level ACLs)
- Slack app distribution to marketplace
- Historical message analysis
- Direct message (DM) support (channels only initially)

## Interfaces & Contracts

### Slack Slash Commands

**Command: `/rr forecast top`**
```
Usage: /rr forecast top [count]
Description: Show top N forecasted opportunities
Parameters:
  - count (optional): Number of opportunities (default: 5, max: 20)
Response: Formatted list with opportunity names, amounts, close dates
```

**Command: `/rr cv recommend`**
```
Usage: /rr cv recommend [agency]
Description: Get contract vehicle recommendations
Parameters:
  - agency (optional): Filter by federal agency
Response: Recommended CVs with rationale and eligibility
```

**Command: `/rr recent`**
```
Usage: /rr recent [hours]
Description: Show recent system activity
Parameters:
  - hours (optional): Lookback window (default: 24, max: 168)
Response: Recent actions, webhook events, opportunities created
```

### MCP Tools Integration

Commands bridge to existing MCP tools:
- `/rr forecast top` → `GET /v1/forecast/top`
- `/rr cv recommend` → `GET /v1/cv/recommend`
- `/rr recent` → `GET /v1/system/recent`

### TypeScript Module

**Location:** `src/tools/slack/index.ts`

**Exports:**
```typescript
interface SlackCommand {
  command: string;
  text: string;
  user_id: string;
  channel_id: string;
  team_id: string;
}

interface SlackResponse {
  response_type: 'in_channel' | 'ephemeral';
  text: string;
  attachments?: any[];
}

export async function handleSlackCommand(
  payload: SlackCommand,
  dryRun?: boolean
): Promise<SlackResponse>;

export function parseCommandArgs(text: string): Record<string, any>;
```

### Environment Variables

Required configuration in `.env`:
```bash
SLACK_BOT_TOKEN=xox*-***
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_ENABLED=true
SLACK_DEFAULT_CHANNEL=#sales-automation
```

## Deliverables

### 1. Code
- 🆕 `src/tools/slack/index.ts` - Command handler stub
  - Command parsing logic
  - Permission checks (placeholder)
  - Dry-run support
  - Queue management (stub)
  - Response formatting
- Environment variable validation
- TypeScript interfaces and types

### 2. Tests
- 🆕 `tests/test_slack_stub.py` - Integration tests
  - Module import verification
  - Command parsing tests
  - Dry-run handler returns 200 JSON
  - Permission model stubs
  - Error handling validation

### 3. Docs
- 🆕 `/docs/sprint_plan.md` - This sprint plan
- 🆕 `/docs/integrations/slack_bot.md` - Complete Slack integration guide
  - Slash command reference
  - Permission model documentation
  - Installation guide for Slack workspace
  - Configuration examples
  - Troubleshooting guide
- `.env.example` updates with Slack variables

### 4. Ops/Runbooks
- Slack app installation procedure
- Token rotation process
- Permission management guide
- Monitoring and alerting setup

## Success Criteria / DEPARTMENT-ALPHA

- [ ] Sprint plan created (docs/sprint_plan.md)
- [ ] Slack bot documentation complete (docs/integrations/slack_bot.md)
- [ ] TypeScript stub created (src/tools/slack/index.ts)
- [ ] Stub compiles without errors (`npm run build`)
- [ ] Python tests created (tests/test_slack_stub.py)
- [ ] All tests passing (import checks, dry-run validation)
- [ ] Environment variables documented in .env.example
- [ ] Permission model documented
- [ ] Installation guide complete
- [ ] Code committed with message "docs(sprint11): add sprint plan + stubs"
- [ ] Branch pushed to origin
- [ ] Draft PR opened with labels: sprint, 11, seed, draft
- [ ] No breaking changes to existing functionality

## Risks & Mitigations

### Risk: Slack Token Security
**Impact:** Critical - Token compromise allows unauthorized access  
**Probability:** Medium  
**Mitigation:**
- Store tokens in environment variables only
- Never commit tokens to version control
- Document token rotation procedures
- Use scoped bot tokens (not user tokens)
- Implement rate limiting per user

### Risk: Command Permission Bypass
**Impact:** High - Unauthorized access to sensitive data  
**Probability:** Low  
**Mitigation:**
- Document role-based permission model
- Default deny for unknown users
- Log all command attempts
- Support workspace-level restrictions
- Implement admin override capability

### Risk: MCP API Availability
**Impact:** Medium - Commands fail if API down  
**Probability:** Low  
**Mitigation:**
- Implement timeout handling
- Provide graceful error messages
- Support async queue for long-running queries
- Add health check before command processing
- Cache recent results for quick responses

### Risk: TypeScript/Python Integration Complexity
**Impact:** Low - Harder to maintain cross-language code  
**Probability:** Medium  
**Mitigation:**
- Keep TypeScript stub minimal
- Python tests focus on interface contracts
- Document integration points clearly
- Use standard HTTP/JSON for communication
- Consider future consolidation to single language

## Validation Steps

### 1. Local TypeScript Build

```bash
# Verify TypeScript compiles
npm run build

# Check for type errors
npx tsc --noEmit

# Verify stub exists
ls -la src/tools/slack/index.ts
```

### 2. Python Tests

```bash
# Run Slack stub tests
pytest tests/test_slack_stub.py -v

# Verify imports work
python -c "from src.tools.slack import index"
```

### 3. Documentation Review

```bash
# Verify all docs exist
cat docs/sprint_plan.md
cat docs/integrations/slack_bot.md
grep SLACK .env.example
```

### 4. Dry-Run Testing

```bash
# Test command parsing (when implemented)
curl -X POST http://localhost:8000/v1/slack/command \
  -H "Content-Type: application/json" \
  -d '{
    "command": "/rr",
    "text": "forecast top 5",
    "dry_run": true
  }'
```

## Checklist

- [x] Design reviewed
- [ ] Sprint plan created (docs/sprint_plan.md)
- [ ] Slack bot documentation created (docs/integrations/slack_bot.md)
- [ ] TypeScript stub created (src/tools/slack/index.ts)
- [ ] Python tests created (tests/test_slack_stub.py)
- [ ] Environment variables added to .env.example
- [ ] TypeScript compiles without errors
- [ ] All tests passing
- [ ] Documentation complete and reviewed
- [ ] Code committed with message "docs(sprint11): add sprint plan + stubs"
- [ ] Branch pushed to origin
- [ ] Draft PR opened with labels: sprint, 11, seed, draft
- [ ] Ready for development phase

## Notes

- Slack bot token format: `xoxb-` prefix for bot tokens, `xoxp-` for user tokens (use bot)
- Slash commands require public endpoint or ngrok for local development
- Command responses must be sent within 3 seconds or use response_url for async
- Permission model initially based on Slack workspace roles (owner, admin, member)
- Consider upgrading to Slack Bolt framework in future sprints for better DX
- Keep stub minimal - full implementation in development phase

---

**Next Steps After Sprint:**
1. Set up Slack app in workspace
2. Configure slash commands in Slack app settings
3. Implement full command handlers with MCP integration
4. Add interactive components (buttons, modals)
5. Set up monitoring for command usage and errors