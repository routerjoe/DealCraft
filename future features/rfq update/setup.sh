#!/bin/bash
#
# Red River Sales Automation - Configuration Setup Script
# This script applies the RFQ filtering configuration to your database
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Red River Sales Automation Configuration Setup${NC}"
echo -e "${BLUE}================================================${NC}"
echo

# Check for required files
if [ ! -f "rfq_config.sql" ]; then
    echo -e "${RED}Error: rfq_config.sql not found!${NC}"
    exit 1
fi

# Prompt for database location
echo -e "${YELLOW}Please enter the path to your sales_automation.db file:${NC}"
read -e -p "Database path: " DB_PATH

# Expand ~ to home directory
DB_PATH="${DB_PATH/#\~/$HOME}"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo -e "${RED}Error: Database not found at: $DB_PATH${NC}"
    echo -e "${YELLOW}Would you like to create a new database? (y/n):${NC}"
    read -p "> " CREATE_DB
    if [ "$CREATE_DB" != "y" ] && [ "$CREATE_DB" != "Y" ]; then
        echo "Setup cancelled."
        exit 1
    fi
fi

# Apply the SQL schema
echo
echo -e "${BLUE}Applying database schema...${NC}"
if sqlite3 "$DB_PATH" < rfq_config.sql; then
    echo -e "${GREEN}✓ Database schema applied successfully${NC}"
else
    echo -e "${RED}✗ Error applying database schema${NC}"
    exit 1
fi

# Verify tables were created
echo
echo -e "${BLUE}Verifying configuration tables...${NC}"
TABLE_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name LIKE 'config_%';")

if [ "$TABLE_COUNT" -ge 4 ]; then
    echo -e "${GREEN}✓ Found $TABLE_COUNT configuration tables${NC}"
    
    # List the tables
    echo -e "\n${BLUE}Configuration tables created:${NC}"
    sqlite3 "$DB_PATH" "SELECT '  - ' || name FROM sqlite_master WHERE type='table' AND (name LIKE 'config_%' OR name LIKE '%_tracking' OR name LIKE '%_log');"
    
else
    echo -e "${YELLOW}⚠ Warning: Expected at least 4 configuration tables, found $TABLE_COUNT${NC}"
fi

# Check strategic customers count
CUSTOMER_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM config_strategic_customers;")
echo -e "\n${GREEN}✓ Loaded $CUSTOMER_COUNT strategic customers${NC}"

# Check OEM tracking count
OEM_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM config_oem_tracking;")
echo -e "${GREEN}✓ Configured $OEM_COUNT OEMs for tracking${NC}"

# Check value thresholds
THRESHOLD_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM config_value_thresholds;")
echo -e "${GREEN}✓ Configured $THRESHOLD_COUNT value tier thresholds${NC}"

# Success summary
echo
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}✓ Configuration setup complete!${NC}"
echo -e "${BLUE}================================================${NC}"
echo
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Copy rfq_filtering_config.py to your MCP server directory"
echo "2. Update your MCP tools to import the configuration"
echo "3. Review CONFIGURATION_SETUP.md for usage examples"
echo "4. Test the configuration with a sample RFQ"
echo
echo -e "${BLUE}Database location:${NC} $DB_PATH"
echo

# Offer to show strategic customers
echo -e "${YELLOW}Would you like to see the strategic customer list? (y/n):${NC}"
read -p "> " SHOW_CUSTOMERS

if [ "$SHOW_CUSTOMERS" = "y" ] || [ "$SHOW_CUSTOMERS" = "Y" ]; then
    echo
    echo -e "${BLUE}Strategic Customers:${NC}"
    sqlite3 -column -header "$DB_PATH" "SELECT customer_name, priority_level, notes FROM config_strategic_customers ORDER BY priority_level, customer_name;"
fi

echo
echo -e "${GREEN}Setup complete! Happy selling! 🎯${NC}"
