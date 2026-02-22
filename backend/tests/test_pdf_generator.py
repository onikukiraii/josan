import datetime

from entity.enums import ShiftType
from pdf.generator import generate_schedule_pdf


class TestGenerateSchedulePdf:
    def test_generates_valid_pdf(self) -> None:
        assignments: list[dict[str, object]] = [
            {"member_name": "田中太郎", "date": datetime.date(2025, 1, 6), "shift_type": ShiftType.ward},
            {"member_name": "鈴木花子", "date": datetime.date(2025, 1, 6), "shift_type": ShiftType.night},
        ]
        buf = generate_schedule_pdf("2025-01", assignments)
        data = buf.read()
        assert data[:5] == b"%PDF-"
        assert len(data) > 100

    def test_empty_assignments(self) -> None:
        buf = generate_schedule_pdf("2025-01", [])
        data = buf.read()
        assert data[:5] == b"%PDF-"

    def test_all_shift_types(self) -> None:
        assignments: list[dict[str, object]] = [
            {"member_name": f"メンバー{i}", "date": datetime.date(2025, 1, 6), "shift_type": st}
            for i, st in enumerate(ShiftType)
            if st != ShiftType.day_off
        ]
        buf = generate_schedule_pdf("2025-01", assignments)
        data = buf.read()
        assert data[:5] == b"%PDF-"

    def test_february_28_days(self) -> None:
        assignments: list[dict[str, object]] = [
            {"member_name": "田中", "date": datetime.date(2025, 2, 1), "shift_type": ShiftType.ward},
            {"member_name": "田中", "date": datetime.date(2025, 2, 28), "shift_type": ShiftType.night},
        ]
        buf = generate_schedule_pdf("2025-02", assignments)
        data = buf.read()
        assert data[:5] == b"%PDF-"
