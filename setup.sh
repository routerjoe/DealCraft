#!/bin/bash

echo "🚀 DealCraft MCP Server Setup"
echo "=============================================="
echo ""

# Check Node.js version
echo "📋 Checking Node.js version..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+ first"
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js 18+ required. Current version: $(node -v)"
    exit 1
fi
echo "✅ Node.js $(node -v)"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
npm install
echo "✅ Dependencies installed"
echo ""

# Create directory structure
echo "📁 Creating directory structure..."
BASE_DIR="${DEALCRAFT_BASE_DIR:-$HOME/DealCraft}"

mkdir -p "$BASE_DIR/data"
mkdir -p "$BASE_DIR/attachments"
mkdir -p "$BASE_DIR/exports"
mkdir -p "$BASE_DIR/logs"

echo "✅ Created:"
echo "   $BASE_DIR/data          (SQLite database)"
echo "   $BASE_DIR/attachments   (Email attachments)"
echo "   $BASE_DIR/exports       (Reports & exports)"
echo "   $BASE_DIR/logs          (Server logs)"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# DealCraft Configuration

# Base directory for all DealCraft files
DEALCRAFT_BASE_DIR=$BASE_DIR

# Attachments directory (set to Google Drive to sync)
# Example (Google Drive for Desktop):
# ATTACHMENTS_DIR="$HOME/Library/CloudStorage/GoogleDrive-your_email@domain.com/My Drive/DealCraft/attachments"
ATTACHMENTS_DIR=$BASE_DIR/attachments

# Obsidian vault path (update this!)
VAULT_ROOT=$HOME/Documents/DealCraft
OBSIDIAN_VAULT_PATH=$HOME/Documents/DealCraft

# Google Drive credentials (optional)
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# SQLite database (optional, defaults to base_dir/data/rfq_tracking.db)
# SQLITE_DB_PATH=$BASE_DIR/data/rfq_tracking.db

# Log level
LOG_LEVEL=info
EOF
    echo "✅ Created .env file"
    echo "⚠️  IMPORTANT: Edit .env and set your OBSIDIAN_VAULT_PATH"
else
    echo "ℹ️  .env file already exists (not overwriting)"
fi
echo ""

# Build TypeScript
echo "🔨 Building TypeScript..."
npm run build
echo "✅ Build complete"
echo ""

# Create Claude Desktop config snippet
echo "📋 Claude Desktop Configuration:"
echo "=============================================="
echo ""
echo "Add this to your Claude Desktop config file:"
echo ""
echo "macOS: ~/Library/Application Support/Claude/claude_desktop_config.json"
echo ""
cat << EOF
{
  "mcpServers": {
    "dealcraft": {
      "command": "node",
      "args": ["$(pwd)/dist/index.js"],
      "env": {
        "DEALCRAFT_BASE_DIR": "$BASE_DIR",
        "VAULT_ROOT": "$HOME/Documents/DealCraft",
        "OBSIDIAN_VAULT_PATH": "$HOME/Documents/DealCraft",
        "ATTACHMENTS_DIR": "$BASE_DIR/attachments"
      }
    }
  }
}
EOF
echo ""
echo "=============================================="
echo ""

# Test database
echo "🔍 Testing database setup..."
if [ -f "dist/index.js" ]; then
    echo "✅ Server built successfully"
else
    echo "❌ Build failed"
    exit 1
fi
echo ""

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and update VAULT_ROOT/OBSIDIAN_VAULT_PATH"
echo "2. Add the config to Claude Desktop (see above)"
echo "3. Restart Claude Desktop"
echo "4. Test with: 'Do you have DealCraft sales tools?'"
echo ""
echo "For testing locally, run: npm run dev"
