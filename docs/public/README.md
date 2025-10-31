# DealCraft — Public Documentation (PII & Agency-Safe)

This public documentation set has been sanitized for public distribution:
- **PII Redacted:** Email addresses, phone numbers, API keys, and secrets removed
- **Agency Names Masked:** Customer/agency names replaced with generic identifiers
- **Vendor Context Preserved:** OEM names (Cisco, Nutanix, NetApp, etc.) and contract vehicles (SEWP, CHESS, Federal Agency A, etc.) retained

## Masking Configuration

The masking rules are defined in `config/public_terms.yml` → `mask_map`:
- Federal agencies and commands → Generic agency identifiers (AGENCY-ALPHA, CCMD-ALPHA, etc.)
- Customer organizations → Masked while preserving technical context
- Vendor/contractor names → **Preserved** (Cisco, Nutanix, SEWP, CHESS, etc.)

## Regenerating Public Docs

To regenerate this public documentation set:

```bash
python3 scripts/publicize_docs.py
```

This will:
1. Read masking configuration from `config/public_terms.yml`
2. Process all documentation files in `docs/`
3. Apply PII redaction and agency masking
4. Output sanitized files to `docs/public/`

## Customizing Masking Rules

Edit `config/public_terms.yml` to:
- Add new terms to mask
- Modify generic replacement names
- Adjust file patterns for processing
- Update whitelist of terms to preserve

After editing the config, re-run the publicizer script to regenerate.

## Documentation Structure

```
docs/public/
├── README.md (this file)
├── api/ - API endpoint documentation
├── architecture/ - System architecture
├── guides/ - Technical guides
├── integrations/ - Integration docs
├── obsidian/ - Obsidian vault integration
├── ops/ - Operations and runbooks
├── releases/ - Release notes
├── rfq/ - RFQ processing
└── webhooks/ - Webhook integration
```

## Original Repository

This is the sanitized public documentation for **DealCraft**, a sales automation and intelligence platform.

For internal documentation with full context, see the private repository.

---

_Last updated: Friday, October 31, 2025 (EDT)_  
_Generated via: `scripts/publicize_docs.py`_  
_Config: `config/public_terms.yml`_
