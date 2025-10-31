#!/bin/bash
# Script to sanitize sensitive customer and organization data from DealCraft
# Replaces specific customer names with generic placeholders

set -e

echo "🔒 Sanitizing sensitive data from DealCraft repository..."
echo "=============================================="

# Define replacement mappings
declare -A replacements=(
    # Customer Names
    ["AFCENT"]="Customer Alpha"
    ["Air Forces Central Command"]="Customer Alpha Command"
    ["AETC"]="Customer Beta"
    ["Air Education and Training Command"]="Customer Beta Command"

    # Organization Names (keep federal context but genericize)
    ["DEPARTMENT-ALPHA"]="Federal Department A"
    ["GSA"]="Federal Agency A"
    ["SPAWAR"]="Federal Agency B"
    ["NAVAIR"]="Federal Agency C"

    # Vault paths - Red River Sales vault
    ["Red River Sales vault"]="DealCraft vault"
    ["Red River Sales"]="DealCraft"

    # Email domain (keep redriver.com as it's the actual company)
    # Don't replace @redriver.com emails - those are real company emails

    # Specific plan IDs
    ["plan-afcent"]="plan-customer-alpha"
    ["plan-aetc"]="plan-customer-beta"
)

# File extensions to process
file_types="*.md *.py *.ts *.tsx *.json *.txt *.yml *.yaml"

# Count total replacements
total_replacements=0

# Function to replace in file
replace_in_file() {
    local file="$1"
    local old="$2"
    local new="$3"

    if grep -q "$old" "$file" 2>/dev/null; then
        # Case-sensitive replacement
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS sed
            sed -i '' "s/$old/$new/g" "$file"
        else
            # Linux sed
            sed -i "s/$old/$new/g" "$file"
        fi
        echo "  ✓ Replaced '$old' in $file"
        ((total_replacements++))
    fi
}

# Process each replacement
for old in "${!replacements[@]}"; do
    new="${replacements[$old]}"
    echo ""
    echo "Replacing: '$old' → '$new'"

    # Find and replace in all markdown files (most critical)
    while IFS= read -r file; do
        replace_in_file "$file" "$old" "$new"
    done < <(find . -name "*.md" -type f ! -path "./node_modules/*" ! -path "./.git/*" ! -path "./dist/*")

    # Find and replace in Python files
    while IFS= read -r file; do
        replace_in_file "$file" "$old" "$new"
    done < <(find . -name "*.py" -type f ! -path "./node_modules/*" ! -path "./.git/*" ! -path "./dist/*" ! -path "./.venv/*")

    # Find and replace in TypeScript files
    while IFS= read -r file; do
        replace_in_file "$file" "$old" "$new"
    done < <(find . -name "*.ts" -type f ! -path "./node_modules/*" ! -path "./.git/*" ! -path "./dist/*")

    # Find and replace in JSON/YAML config files
    while IFS= read -r file; do
        replace_in_file "$file" "$old" "$new"
    done < <(find . \( -name "*.json" -o -name "*.yml" -o -name "*.yaml" \) -type f ! -path "./node_modules/*" ! -path "./.git/*" ! -path "./dist/*" ! -path "./package-lock.json")
done

echo ""
echo "=============================================="
echo "✅ Sanitization complete!"
echo "Total file replacements: $total_replacements"
echo ""
echo "⚠️  Important: Review the changes before committing!"
echo "Run: git diff | head -200"
echo ""
