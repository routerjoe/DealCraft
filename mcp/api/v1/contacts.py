"""Contacts export endpoints (CSV and vCard)."""

import csv
import io
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from mcp.core.store import read_json

router = APIRouter(prefix="/contacts", tags=["Contacts"])

logger = logging.getLogger(__name__)

# File path for state storage
STATE_FILE = "data/state.json"


class Contact(BaseModel):
    """Contact model."""

    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    phone: str = Field(default="", description="Phone number")
    organization: str = Field(default="", description="Organization")
    title: str = Field(default="", description="Job title")


def sanitize_csv_field(value: str) -> str:
    """Sanitize a field for CSV output by escaping problematic characters."""
    if not value:
        return ""
    # Replace newlines and carriage returns with spaces
    value = value.replace("\n", " ").replace("\r", " ")
    # If field contains comma, quote, or starts with special chars, it will be quoted by csv module
    return value


def generate_vcard(contact: Contact) -> str:
    """
    Generate a vCard 3.0 entry for a contact.

    Format:
    - FN: Full Name
    - N: Structured Name (Last;First;Middle;Prefix;Suffix)
    - EMAIL: Email address
    - TEL: Phone number
    - ORG: Organization
    - TITLE: Job title
    """
    lines = ["BEGIN:VCARD", "VERSION:3.0"]

    # FN (Full Name) - required
    lines.append(f"FN:{contact.name}")

    # N (Structured Name) - Last;First;Middle;Prefix;Suffix
    # For simplicity, assume single name or "First Last" format
    name_parts = contact.name.split(maxsplit=1)
    if len(name_parts) == 2:
        first, last = name_parts[0], name_parts[1]
    elif len(name_parts) == 1:
        first, last = name_parts[0], ""
    else:
        first, last = "", ""
    lines.append(f"N:{last};{first};;;")

    # EMAIL
    if contact.email:
        lines.append(f"EMAIL;TYPE=INTERNET:{contact.email}")

    # TEL
    if contact.phone:
        lines.append(f"TEL;TYPE=WORK,VOICE:{contact.phone}")

    # ORG
    if contact.organization:
        lines.append(f"ORG:{contact.organization}")

    # TITLE
    if contact.title:
        lines.append(f"TITLE:{contact.title}")

    lines.append("END:VCARD")

    return "\n".join(lines)


@router.get("/export.csv")
async def export_contacts_csv():
    """
    Export contacts as CSV (RFC 4180).

    Reads contacts from data/state.json and streams as CSV response.
    """
    try:
        # Read contacts from state
        state = read_json(STATE_FILE)
        contacts_data = state.get("contacts", [])

        # Convert to Contact objects
        contacts = [Contact(**c) for c in contacts_data]

        # Generate CSV in memory
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # Write header
        writer.writerow(["Name", "Email", "Phone", "Organization", "Title"])

        # Write data rows
        for contact in contacts:
            writer.writerow(
                [
                    sanitize_csv_field(contact.name),
                    sanitize_csv_field(contact.email),
                    sanitize_csv_field(contact.phone),
                    sanitize_csv_field(contact.organization),
                    sanitize_csv_field(contact.title),
                ]
            )

        # Get CSV content
        csv_content = output.getvalue()
        output.close()

        logger.info(f"Exported {len(contacts)} contacts as CSV")

        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(csv_content.encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=contacts.csv"},
        )

    except FileNotFoundError:
        logger.warning("State file not found, returning empty CSV")
        # Return empty CSV with headers
        csv_content = "Name,Email,Phone,Organization,Title\n"
        return StreamingResponse(
            io.BytesIO(csv_content.encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=contacts.csv"},
        )
    except Exception as e:
        logger.error(f"Failed to export contacts as CSV: {str(e)}")
        # Return empty CSV on error
        csv_content = "Name,Email,Phone,Organization,Title\n"
        return StreamingResponse(
            io.BytesIO(csv_content.encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=contacts.csv"},
        )


@router.get("/export.vcf")
async def export_contacts_vcf():
    """
    Export contacts as vCard 3.0 (VCF).

    Reads contacts from data/state.json and streams as VCF response.
    Compatible with macOS Contacts app.
    """
    try:
        # Read contacts from state
        state = read_json(STATE_FILE)
        contacts_data = state.get("contacts", [])

        # Convert to Contact objects
        contacts = [Contact(**c) for c in contacts_data]

        # Generate vCards
        vcards = []
        for contact in contacts:
            vcard = generate_vcard(contact)
            vcards.append(vcard)

        # Join with blank lines between vCards
        vcf_content = "\n\n".join(vcards)

        logger.info(f"Exported {len(contacts)} contacts as VCF")

        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(vcf_content.encode("utf-8")),
            media_type="text/vcard",
            headers={"Content-Disposition": "attachment; filename=contacts.vcf"},
        )

    except FileNotFoundError:
        logger.warning("State file not found, returning empty VCF")
        # Return empty VCF
        return StreamingResponse(
            io.BytesIO(b""),
            media_type="text/vcard",
            headers={"Content-Disposition": "attachment; filename=contacts.vcf"},
        )
    except Exception as e:
        logger.error(f"Failed to export contacts as VCF: {str(e)}")
        # Return empty VCF on error
        return StreamingResponse(
            io.BytesIO(b""),
            media_type="text/vcard",
            headers={"Content-Disposition": "attachment; filename=contacts.vcf"},
        )
