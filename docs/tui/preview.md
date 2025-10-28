# Red River Sales MCP - Terminal UI

Interactive Textual-based TUI for managing OEMs, Contract Vehicles, and AI-powered RFQ guidance.

## Quick Start

### Prerequisites

Ensure the API server is running:

```bash
# In one terminal
kc run:dev
```

### Launch TUI

```bash
# In another terminal
kc run:tui
```

## Interface Layout

The TUI is divided into three main panels:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Red River Sales MCP                          │
├──────────────┬──────────────────┬────────────────────────────┤
│ OEM Panel    │ Contract Panel   │ AI Guidance Panel          │
│              │                  │                            │
│ [Table]      │ [Table]          │ [Text Output]              │
│              │                  │                            │
│              │                  │                            │
└──────────────┴──────────────────┴────────────────────────────┘
│ Q: Quit | ?: Help                                              │
└─────────────────────────────────────────────────────────────────┘
```

## Keyboard Shortcuts

### Global Commands
- **Q** - Quit application
- **?** - Show help dialog

### OEM Authorization Panel

| Key | Action | Description |
|-----|--------|-------------|
| **A** | Add | Add a new OEM |
| **T** | Toggle | Toggle authorized status for selected OEM |
| **↑** | Threshold + | Increase threshold by 100 |
| **↓** | Threshold - | Decrease threshold by 100 |
| **D** | Delete | Delete selected OEM |
| **R** | Refresh | Reload OEM data from API |

### Contract Vehicles Panel

| Key | Action | Description |
|-----|--------|-------------|
| **C** | Add | Add a new Contract Vehicle |
| **S** | Toggle | Toggle supported status for selected contract |
| **E** | Edit Notes | Edit notes for selected contract |
| **X** | Delete | Delete selected contract |
| **R** | Refresh | Reload contract data from API |

### AI Guidance Panel

| Key | Action | Description |
|-----|--------|-------------|
| **G** | Generate | Generate AI guidance using current OEMs/contracts |
| **I** | Switch Model | Cycle through available AI models |

## Features

### Non-Blocking Operations
All API calls are asynchronous and won't freeze the UI. Success/error notifications appear as toasts.

### Request Tracking
The footer displays the last API request ID for debugging and tracing.

### Error Handling
- **409 Conflict** - Attempting to create duplicate OEM/Contract shows error notification
- **404 Not Found** - Attempting to modify/delete non-existent item shows error notification
- **Network Errors** - Connection issues are gracefully handled with error messages

## Workflow Examples

### Adding and Configuring an OEM

1. Navigate to OEM panel
2. Press **A** to add new OEM
3. Enter OEM name and threshold
4. Press **T** to toggle authorization status
5. Use **↑** or **↓** to adjust threshold values

### Managing Contract Vehicles

1. Navigate to Contract panel
2. Press **C** to add new contract
3. Enter contract name and notes
4. Press **S** to toggle supported status
5. Press **E** to edit detailed notes

### Generating AI Guidance

1. Configure OEMs and Contracts as needed
2. Navigate to AI panel
3. Press **I** to select desired AI model
4. Press **G** to generate guidance
5. Review summary, actions, and risks in the output

## Theme

The TUI uses Red River's light theme with:
- **Primary Red** (#CC0000) - Headers and OEM panel
- **Professional Blue** (#2C5F8D) - Contract panel
- **Accent Blue** (#0277BD) - AI panel
- **Light backgrounds** for accessibility

## Troubleshooting

### TUI won't start
- Ensure API is running at http://localhost:8000
- Check that `textual` is installed: `pip install -r requirements.txt`

### "Failed to load" errors
- Verify API server is accessible
- Check that `data/state.json` exists and is valid JSON
- Review API logs for request errors

### Key bindings not working
- Ensure the relevant panel has focus
- Some keys are case-sensitive (use lowercase)

## Development

To modify the TUI:

1. Edit panel files in `tui/panels/`
2. Update theme in `tui/theme.py`
3. Modify main layout in `tui/app.py`
4. Test changes: `kc run:tui`

## Screenshots

_TODO: Add screenshots showing:_
- Main interface with all three panels
- OEM Add modal
- Contract Edit modal  
- AI Guidance output display