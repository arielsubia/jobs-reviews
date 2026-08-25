"""Parser for converting job application notepad file to structured JSON."""

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from src.parser.config import INPUT_FILE, OUTPUT_FILE

# Regex patterns
DATE_PATTERN = re.compile(r"^(\d{2}/\d{2}/\d{4})\s*-?\s*$")

REJECTION_PATTERNS = [
    re.compile(
        r"[-–]\s*RECHAZ\w+\s+(?:el\s+)?(\d{2}/\d{2}/\d{4})", re.IGNORECASE
    ),
    re.compile(
        r"RECHAZ\w+\s+(?:el\s+)?(\d{2}/\d{2}/\d{4})", re.IGNORECASE
    ),
    re.compile(
        r"RECHAZ\w+\s*\((\d{2}/\d{2}/\d{4})\)", re.IGNORECASE
    ),
]

FAVORITE_PATTERN = re.compile(r"MARCADA COMO FAVORITA", re.IGNORECASE)

CHANNEL_PATTERNS = [
    re.compile(r"[-–]\s*(?:M|m)ediante\s+(.+?)(?:\s*[-–]\s*(?:RECHAZ|MARCADA)|$)"),
    re.compile(r"[-–]\s*(?:E|e)nviado\s+(.+?)(?:\s*[-–]\s*(?:RECHAZ|MARCADA)|$)"),
    re.compile(r"[-–]\s*(?:V|v)(?:ia|ía)\s+(.+?)(?:\s*[-–]\s*(?:RECHAZ|MARCADA)|$)"),
    re.compile(
        r"[-–]\s*(?:A|a)\s+trav[eé]s\s+de\s+(.+?)(?:\s*[-–]\s*(?:RECHAZ|MARCADA)|$)"
    ),
    re.compile(r"[Mm]ediante\s+(.+?)(?:\s*[-–]\s*(?:RECHAZ|MARCADA)|$)"),
    re.compile(r"[Ee]nviado\s+(.+?)(?:\s*[-–]\s*(?:RECHAZ|MARCADA)|$)"),
    re.compile(r"[Vv](?:ia|ía)\s+(.+?)(?:\s*[-–]\s*(?:RECHAZ|MARCADA)|$)"),
    re.compile(
        r"[Aa]\s+trav[eé]s\s+de\s+(.+?)(?:\s*[-–]\s*(?:RECHAZ|MARCADA)|$)"
    ),
]


@dataclass
class JobApplication:
    """Represents a single job application record."""

    date: str
    position: str
    company: str
    channel: str | None
    status: str
    rejection_date: str | None
    is_favorite: bool
    raw_line: str


def convert_date_to_iso(date_str: str) -> str:
    """Convert DD/MM/YYYY to YYYY-MM-DD format."""
    day, month, year = date_str.split("/")
    return f"{year}-{month}-{day}"


def extract_rejection(line: str) -> tuple[bool, str | None]:
    """Extract rejection status and date from a line."""
    for pattern in REJECTION_PATTERNS:
        match = pattern.search(line)
        if match:
            return True, convert_date_to_iso(match.group(1))

    # Check for rejection without date
    if re.search(r"RECHAZ\w+", line, re.IGNORECASE):
        return True, None

    return False, None


def extract_channel(line: str) -> str | None:
    """Extract the application channel from a line."""
    for pattern in CHANNEL_PATTERNS:
        match = pattern.search(line)
        if match:
            channel = match.group(1).strip()
            # Clean trailing punctuation and status markers
            channel = re.sub(
                r"\s*[-–]?\s*(?:RECHAZ|MARCADA).*$", "", channel, flags=re.IGNORECASE
            )
            channel = channel.rstrip(" .-–")
            if channel:
                return channel
    return None


def clean_line_for_parsing(line: str) -> str:
    """Remove status markers and channel info to isolate position and company."""
    cleaned = line

    # Remove rejection markers with dates
    for pattern in REJECTION_PATTERNS:
        cleaned = pattern.sub("", cleaned)

    # Remove standalone rejection words
    cleaned = re.sub(
        r"\s*[-–]?\s*RECHAZ\w+(?:\s+(?:el\s+)?\d{2}/\d{2}/\d{4})?",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Remove favorite marker
    cleaned = re.sub(
        r"\s*[-–.]?\s*MARCADA COMO FAVORITA\.?", "", cleaned, flags=re.IGNORECASE
    )

    # Remove channel info patterns
    channel_removal_patterns = [
        re.compile(
            r"\s*[-–]\s*(?:mediante|enviado|via|vía|a\s+trav[eé]s\s+de)\s+.*$",
            re.IGNORECASE,
        ),
        re.compile(
            r"\s*(?:mediante|enviado|via|vía|a\s+trav[eé]s\s+de)\s+.*$",
            re.IGNORECASE,
        ),
    ]

    for pattern in channel_removal_patterns:
        cleaned = pattern.sub("", cleaned)

    return cleaned.strip().rstrip(" .-–")


def parse_position_and_company(cleaned_line: str) -> tuple[str, str]:
    """Extract position and company from a cleaned line."""
    # Split by " - " to separate position from company
    parts = cleaned_line.split(" - ")

    if len(parts) >= 2:
        position = parts[0].strip()
        company = parts[1].strip()
        return position, company
    elif len(parts) == 1:
        # No clear separator — treat entire line as position with unknown company
        return parts[0].strip(), "Desconocida"

    return cleaned_line.strip(), "Desconocida"


def parse_line(line: str, current_date: str) -> JobApplication | None:
    """Parse a single application line into a JobApplication."""
    stripped = line.strip()

    # Skip empty lines and date lines
    if not stripped:
        return None
    if DATE_PATTERN.match(stripped):
        return None

    # Extract status info
    is_rejected, rejection_date = extract_rejection(stripped)
    is_favorite = bool(FAVORITE_PATTERN.search(stripped))

    # Determine status
    if is_rejected:
        status = "rechazada"
    elif is_favorite:
        status = "favorita"
    else:
        status = "pendiente"

    # Extract channel
    channel = extract_channel(stripped)

    # Clean line and extract position/company
    cleaned = clean_line_for_parsing(stripped)
    position, company = parse_position_and_company(cleaned)

    # Skip lines that don't look like valid applications
    if not position or position.isspace():
        return None

    return JobApplication(
        date=current_date,
        position=position,
        company=company,
        channel=channel,
        status=status,
        rejection_date=rejection_date,
        is_favorite=is_favorite,
        raw_line=stripped,
    )


def parse_file(file_path: Path) -> list[JobApplication]:
    """Parse the entire notepad file into a list of JobApplications."""
    applications: list[JobApplication] = []
    current_date = ""

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()

            # Check if this is a date line
            date_match = DATE_PATTERN.match(stripped)
            if date_match:
                current_date = convert_date_to_iso(date_match.group(1))
                continue

            # Skip if no date context yet
            if not current_date:
                continue

            # Try to parse as application
            app = parse_line(line, current_date)
            if app:
                applications.append(app)

    return applications


def main() -> None:
    """Main entry point: parse input file and write JSON output."""
    if not INPUT_FILE.exists():
        print(f"Error: Input file not found at {INPUT_FILE}")
        print("Place your 'CVs enviados.txt' file in the docs/ directory.")
        return

    print(f"Parsing: {INPUT_FILE}")
    applications = parse_file(INPUT_FILE)

    # Write JSON output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    output_data = [asdict(app) for app in applications]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"Generated: {OUTPUT_FILE}")
    print(f"Total records: {len(applications)}")

    # Summary stats
    rejected = sum(1 for a in applications if a.status == "rechazada")
    favorites = sum(1 for a in applications if a.status == "favorita")
    pending = sum(1 for a in applications if a.status == "pendiente")
    print(f"  Rejected: {rejected}")
    print(f"  Favorites: {favorites}")
    print(f"  Pending: {pending}")


if __name__ == "__main__":
    main()
