"""Tests for the job application parser."""

from pathlib import Path

from src.parser.parser import (
    clean_line_for_parsing,
    convert_date_to_iso,
    extract_channel,
    extract_rejection,
    extract_salary,
    is_note_line,
    is_orphan_continuation,
    parse_application_line,
    parse_file,
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

    def test_channel_with_salary_after(self) -> None:
        line = "Data Engineer - KPMG - mediante Expo Bumeran Online 2026 - $1500000"
        channel = extract_channel(line)
        assert channel is not None
        assert "Expo Bumeran Online 2026" in channel
        assert "$" not in channel


class TestExtractSalary:
    def test_basic_salary(self) -> None:
        line = "Data Engineer - KPMG - mediante Bumeran - $1500000"
        salary = extract_salary(line)
        assert salary == "$1500000"

    def test_salary_with_dots(self) -> None:
        line = "Data Engineer - Telecom - $2.500.000"
        salary = extract_salary(line)
        assert salary == "$2.500.000"

    def test_salary_with_usd(self) -> None:
        line = "Data Engineer - Globant - $2800 USD"
        salary = extract_salary(line)
        assert salary == "$2800 USD"

    def test_no_salary(self) -> None:
        line = "Data Engineer - Telecom"
        salary = extract_salary(line)
        assert salary is None


class TestNoteDetection:
    def test_is_note_line(self) -> None:
        assert is_note_line("** ¿Por qué te interesa?") is True
        assert is_note_line("**Nota sin espacio") is True
        assert is_note_line("Data Engineer - Telecom") is False
        assert is_note_line("") is False

    def test_orphan_continuation(self) -> None:
        assert is_orphan_continuation("continuación del texto") is True
        assert is_orphan_continuation("Data Engineer - Telecom") is False
        assert is_orphan_continuation("24/06/2026") is False
        assert is_orphan_continuation("** nota") is False
        assert is_orphan_continuation("") is False


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

    def test_removes_salary(self) -> None:
        line = "Data Engineer - KPMG - mediante Bumeran - $1500000"
        cleaned = clean_line_for_parsing(line)
        assert "$" not in cleaned
        assert "1500000" not in cleaned


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


class TestParseApplicationLine:
    def test_basic_line(self) -> None:
        app = parse_application_line("Data Engineer - Telecom", "2025-06-07")
        assert app is not None
        assert app.position == "Data Engineer"
        assert app.company == "Telecom"
        assert app.status == "pendiente"
        assert app.channel is None
        assert app.salary is None

    def test_rejected_line(self) -> None:
        app = parse_application_line(
            "Data Scientist - Despegar - RECHAZADA el 29/04/2025", "2025-03-19"
        )
        assert app is not None
        assert app.status == "rechazada"
        assert app.rejection_date == "2025-04-29"

    def test_favorite_line(self) -> None:
        app = parse_application_line(
            "Data Engineer - Epidata - MARCADA COMO FAVORITA", "2025-05-30"
        )
        assert app is not None
        assert app.status == "favorita"
        assert app.is_favorite is True

    def test_with_channel(self) -> None:
        app = parse_application_line(
            "Data Engineer - Workia Solutions - Mediante Bumeran", "2025-06-15"
        )
        assert app is not None
        assert app.channel is not None
        assert "Bumeran" in app.channel

    def test_with_salary(self) -> None:
        app = parse_application_line(
            "Data Engineer - KPMG - mediante Bumeran - $1500000", "2026-08-22"
        )
        assert app is not None
        assert app.salary == "$1500000"
        assert app.channel is not None
        assert "Bumeran" in app.channel

    def test_empty_line(self) -> None:
        app = parse_application_line("", "2025-01-01")
        assert app is None

    def test_date_line_skipped(self) -> None:
        app = parse_application_line("24/06/2026", "2026-06-24")
        assert app is None

    def test_date_with_trailing_dash(self) -> None:
        app = parse_application_line("08/10/2024 - ", "2024-10-08")
        assert app is None


class TestParseFile:
    def test_parse_full_file(self) -> None:
        input_file = Path(__file__).resolve().parent.parent / "docs" / "CVs enviados.txt"
        if not input_file.exists():
            return  # Skip if file not available

        applications = parse_file(input_file)
        assert len(applications) > 400

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

        # Verify salary extraction works on known records
        salary_apps = [a for a in applications if a.salary]
        assert len(salary_apps) > 0

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

    def test_parse_notes(self, tmp_path: Path) -> None:
        sample = """25/08/2026
Data Engineer - Telecom - $2500000
** ¿Por qué te interesa? Me apasiona el procesamiento de datos
** ¿Disponibilidad? Sí, inmediata

Analista de Datos - YPF
"""
        sample_file = tmp_path / "sample.txt"
        sample_file.write_text(sample, encoding="utf-8")

        applications = parse_file(sample_file)
        assert len(applications) == 2

        assert applications[0].salary == "$2500000"
        assert len(applications[0].notes) == 2
        assert "Me apasiona" in applications[0].notes[0]
        assert "inmediata" in applications[0].notes[1]

        assert applications[1].notes == []
        assert applications[1].salary is None

    def test_parse_notes_with_continuation(self, tmp_path: Path) -> None:
        sample = """25/08/2026
Data Engineer - Telecom
** ¿Por qué te interesa? Me apasiona el procesamiento
de datos a escala y la arquitectura cloud
** ¿Disponibilidad? Sí
"""
        sample_file = tmp_path / "sample.txt"
        sample_file.write_text(sample, encoding="utf-8")

        applications = parse_file(sample_file)
        assert len(applications) == 1

        assert len(applications[0].notes) == 2
        assert "de datos a escala" in applications[0].notes[0]
        assert applications[0].notes[1] == "¿Disponibilidad? Sí"
