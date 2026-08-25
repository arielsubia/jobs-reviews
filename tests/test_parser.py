"""Tests for the job application parser."""

from pathlib import Path

from src.parser.parser import (
    clean_line_for_parsing,
    convert_date_to_iso,
    extract_channel,
    extract_rejection,
    parse_file,
    parse_line,
    parse_position_and_company,
)


class TestConvertDate:
    def test_basic_date(self) -> None:
        assert convert_date_to_iso("24/06/2026") == "2026-06-24"

    def test_leading_zeros(self) -> None:
        assert convert_date_to_iso("01/01/2025") == "2025-01-01"


class TestExtractRejection:
    def test_rejected_with_date(self) -> None:
        line = "Data Scientist - Despegar - RECHAZADA el 29/04/2025"
        is_rejected, date = extract_rejection(line)
        assert is_rejected is True
        assert date == "2025-04-29"

    def test_rejected_with_date_variant(self) -> None:
        line = "Machine Learning Expert - Accenture - Rechaza el 12/06/2026"
        is_rejected, date = extract_rejection(line)
        assert is_rejected is True
        assert date == "2026-06-12"

    def test_rejected_typo(self) -> None:
        line = "Programa Jóvenes Profesionales - Axion - RECHAZASA el 17/07/2026"
        is_rejected, date = extract_rejection(line)
        assert is_rejected is True
        assert date == "2026-07-17"

    def test_rejected_with_parentheses(self) -> None:
        line = "Data Engineer - Assist Card - RECHAZADA (07/08/2025)"
        is_rejected, date = extract_rejection(line)
        assert is_rejected is True
        assert date == "2025-08-07"

    def test_not_rejected(self) -> None:
        line = "Data Engineer - Telecom"
        is_rejected, date = extract_rejection(line)
        assert is_rejected is False
        assert date is None


class TestExtractChannel:
    def test_mediante(self) -> None:
        line = "Data Engineer - Workia Solutions - Mediante Bumeran"
        channel = extract_channel(line)
        assert channel is not None
        assert "Bumeran" in channel

    def test_enviado_por_correo(self) -> None:
        line = "Data Engineer - Epidata - enviado por correo a postulaciones@epidata.net"
        channel = extract_channel(line)
        assert channel is not None
        assert "correo" in channel

    def test_via(self) -> None:
        line = "Ingeniero de Datos - Farmacias Central Oeste (Via Bumeran y LinkedIn)"
        channel = extract_channel(line)
        assert channel is not None
        assert "Bumeran" in channel

    def test_a_traves_de(self) -> None:
        line = "Talentos Tech - AyiGroup - a través de su plataforma"
        channel = extract_channel(line)
        assert channel is not None
        assert "plataforma" in channel

    def test_no_channel(self) -> None:
        line = "Data Engineer - Telecom"
        channel = extract_channel(line)
        assert channel is None


class TestCleanLine:
    def test_removes_rejection(self) -> None:
        line = "Data Scientist - Despegar - RECHAZADA el 29/04/2025"
        cleaned = clean_line_for_parsing(line)
        assert "RECHAZADA" not in cleaned
        assert "Despegar" in cleaned

    def test_removes_favorite(self) -> None:
        line = "Data Engineer - Epidata - MARCADA COMO FAVORITA"
        cleaned = clean_line_for_parsing(line)
        assert "MARCADA" not in cleaned
        assert "Epidata" in cleaned

    def test_removes_channel(self) -> None:
        line = "Data Engineer - Workia Solutions - Mediante Bumeran"
        cleaned = clean_line_for_parsing(line)
        assert "Bumeran" not in cleaned
        assert "Workia Solutions" in cleaned


class TestParsePositionAndCompany:
    def test_basic_split(self) -> None:
        position, company = parse_position_and_company("Data Engineer - Telecom")
        assert position == "Data Engineer"
        assert company == "Telecom"

    def test_multiple_separators(self) -> None:
        position, company = parse_position_and_company(
            "Data Engineer Senior - Grupo Mariposa"
        )
        assert position == "Data Engineer Senior"
        assert company == "Grupo Mariposa"

    def test_no_separator(self) -> None:
        position, company = parse_position_and_company("INVAP")
        assert position == "INVAP"
        assert company == "Desconocida"


class TestParseLine:
    def test_basic_line(self) -> None:
        app = parse_line("Data Engineer - Telecom", "2025-06-07")
        assert app is not None
        assert app.position == "Data Engineer"
        assert app.company == "Telecom"
        assert app.status == "pendiente"
        assert app.channel is None

    def test_rejected_line(self) -> None:
        app = parse_line(
            "Data Scientist - Despegar - RECHAZADA el 29/04/2025", "2025-03-19"
        )
        assert app is not None
        assert app.status == "rechazada"
        assert app.rejection_date == "2025-04-29"

    def test_favorite_line(self) -> None:
        app = parse_line(
            "Data Engineer - Epidata - MARCADA COMO FAVORITA", "2025-05-30"
        )
        assert app is not None
        assert app.status == "favorita"
        assert app.is_favorite is True

    def test_with_channel(self) -> None:
        app = parse_line(
            "Data Engineer - Workia Solutions - Mediante Bumeran", "2025-06-15"
        )
        assert app is not None
        assert app.channel is not None
        assert "Bumeran" in app.channel

    def test_empty_line(self) -> None:
        app = parse_line("", "2025-01-01")
        assert app is None

    def test_date_line_skipped(self) -> None:
        app = parse_line("24/06/2026", "2026-06-24")
        assert app is None

    def test_date_with_trailing_dash(self) -> None:
        app = parse_line("08/10/2024 - ", "2024-10-08")
        assert app is None


class TestParseFile:
    def test_parse_full_file(self) -> None:
        input_file = Path(__file__).resolve().parent.parent / "docs" / "CVs enviados.txt"
        if not input_file.exists():
            return  # Skip if file not available

        applications = parse_file(input_file)
        assert len(applications) > 400  # We expect 500+ records

        # Verify some known records exist
        companies = [app.company for app in applications]
        assert "Telecom" in companies
        assert "Despegar" in companies

        # Verify statuses are valid
        valid_statuses = {"rechazada", "favorita", "pendiente"}
        for app in applications:
            assert app.status in valid_statuses

        # Verify dates are in ISO format
        for app in applications:
            assert len(app.date) == 10
            assert app.date[4] == "-"
            assert app.date[7] == "-"

    def test_parse_sample_content(self, tmp_path: Path) -> None:
        sample = """09/09/2024
Developers Trainee Junior - IT Patagonia

08/10/2024 -
Analista de Growth Marketing Sr - Flybondi

14/10/2024
Data Engineer - Prex Argentina Remote
Data Engineer Jr. - Google Cloud Academy - Argentina
"""
        sample_file = tmp_path / "sample.txt"
        sample_file.write_text(sample, encoding="utf-8")

        applications = parse_file(sample_file)
        assert len(applications) == 4

        assert applications[0].date == "2024-09-09"
        assert applications[0].position == "Developers Trainee Junior"
        assert applications[0].company == "IT Patagonia"

        assert applications[1].date == "2024-10-08"
        assert applications[1].company == "Flybondi"

        assert applications[2].date == "2024-10-14"
        assert applications[2].position == "Data Engineer"
        assert applications[2].company == "Prex Argentina Remote"
