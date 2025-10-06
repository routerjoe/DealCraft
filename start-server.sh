#!/bin/bash

# Set environment variables directly
export RED_RIVER_BASE_DIR="/Users/jonolan/RedRiver"
export OBSIDIAN_VAULT_PATH="/Users/jonolan/Documents/Obsidian Documents/Red River Sales"
export LOG_LEVEL="info"

# Start the MCP server
node dist/index.js
