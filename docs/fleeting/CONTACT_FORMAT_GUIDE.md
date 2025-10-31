# Fleeting Notes Contact Format - Quick Reference

## ✅ Correct Format

```markdown
N: Full Name
T: Job Title
C: Company Name
O: Organization/Customer (e.g., Customer Alpha A63)
E: email@domain.com
M: 555-123-4567
Office: 555-987-6543
W: https://example.com
L: https://linkedin.com/in/username
X: @username
A: Street Address
   City, State ZIP
```

## Flexible Parsing Support

The parser now supports both **strict format** (with N:/T:/E: prefixes) and **flexible format** (freeform text).

### Strict Format (Recommended)
Use the field prefixes for guaranteed parsing:
- Markdown formatting is automatically stripped (bold, italics, links, code)
- Prefixes can use `:`, `-`, `—`, or `|` separators

### Flexible Format (Auto-detected)
If no strict format is found, the parser will automatically detect:
- Email addresses (by @ pattern)
- Phone numbers (various formats)
- Names (by capitalization)
- Common job titles
- Company/organization names
- URLs for websites, LinkedIn, Twitter

## Required Fields
- **N:** (Name) - REQUIRED for strict format
- **At least one contact method:** E: or M: or Office:
- For flexible format: email is used as anchor

## Field Reference

| Prefix | Field | Example | Notes |
|--------|-------|---------|-------|
| **N:** | Name | `N: John Smith` | Required to start contact block |
| **T:** | Title | `T: IT Director` | Optional, appears in filename |
| **C:** | Company | `C: Cisco` | Optional, creates company folder |
| **O:** | Organization/Customer | `O: Customer Alpha A63` | Government/customer org (not phone) |
| **Office:** | Office Phone | `Office: 803-666-6580` | Use full word for phone |
| **E:** | Email | `E: jsmith@company.com` | Multiple: separate with commas |
| **M:** | Mobile | `M: 571-265-3865` | Any phone format |
| **W:** | Website | `W: https://example.com` | Company or personal website |
| **L:** | LinkedIn | `L: https://linkedin.com/in/user` | LinkedIn profile URL |
| **X:** | Twitter/X | `X: @username` | Twitter/X handle or URL |
| **A:** | Address | `A: 123 Main St` | Multi-line continues until next field |

## Examples

### Strict Format - Government Contact
```markdown
N: Bruno Mosqueira
T: Shipping and Receiving
O: Customer Alpha A63
Office: 803-666-6580
E: bruno.mosqueira.1.ctr@us.af.mil
```

### Strict Format - Vendor Contact with Social
```markdown
N: Sean Jeffers
T: Regional Sales Manager, USAF
C: Palo Alto Networks
E: sjeffers@paloaltonetworks.com
M: 571-265-3865
L: https://linkedin.com/in/seanjeffers
W: https://paloaltonetworks.com
A: 12110 Sunset Hills Road, Suite 200
   Reston, VA 20190
```

### Strict Format - No Company (Goes to Triage)
```markdown
N: John Smith
T: IT Director
E: jsmith@example.com
```

### Flexible Format - Auto-detected Contact
```markdown
**Bruno Mosqueira**
Shipping and Receiving at Customer Alpha A63
bruno.mosqueira.1.ctr@us.af.mil
803-666-6580
```
This will be automatically parsed even with markdown formatting and no N:/T:/E: prefixes!

### Flexible Format - Contact with Links
```markdown
Met with [Sean Jeffers](https://linkedin.com/in/seanjeffers) from Palo Alto Networks
Email: sjeffers@paloaltonetworks.com
Mobile: (571) 265-3865
```
The parser will extract name, email, phone, LinkedIn, and company automatically.

## ❌ Common Mistakes (Now Fixed!)

These used to break the parser, but now work automatically:

| ❌ Previously Broken | ✅ Now Works |
|---------------------|-------------|
| `N: **John Doe**` | Markdown stripped automatically |
| `**Email:** jdoe@company.com` | Email detected by @ pattern |
| `Regional Sales Manager` (no T:) | Auto-detected by job title pattern |
| Palo Alto Networks \| 123 Main St | Company detected by pattern |
| `[John Doe](mailto:john@example.com)` | Link text extracted |

## Where Files Are Created

- **With Company:** `30 Hubs/People/{Company Name}/{Name} ({Title}).md`
- **Without Company:** `30 Hubs/People/_Triage/{Name} ({Title}).md`

## See Also
- Full guide: `AI_Extended_Memory/05_Automations/fleeting_notes_contact_format.md`
- README: `docs/fleeting/README_FINAL.md`
