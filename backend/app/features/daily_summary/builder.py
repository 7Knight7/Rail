"""Deterministic text builders for Daily Summary sections (R3–R6)."""

from __future__ import annotations

from collections import Counter, defaultdict

from app.automation.report4_filters import COMPLAINT_TYPES_ORDERED
from app.automation.formatting.text_safe import normalize_report_text
from app.features.daily_summary.scr import row_dict_is_scr
from app.features.daily_summary.sources import ReportSource, RunSources


def _is_total_row(row: dict[str, str], *keys: str) -> bool:
    for key in keys:
        val = (row.get(key) or "").strip().lower()
        if "total" in val:
            return True
    joined = " ".join((row.get(k) or "") for k in row).lower()
    return "total" in joined and any(
        (row.get(k) or "").strip().lower().startswith("total")
        or (row.get(k) or "").strip().lower() == "total"
        for k in ("Train No.", "Train Name", "Owning Zone", "Organisation", "Division")
        if k in row
    )


def _top_n(rows: list[dict[str, str]], n: int) -> list[dict[str, str]]:
    data = [r for r in rows if not _is_total_row(r, "Train No.", "Train Name", "Owning Zone")]
    return data[:n]


def build_report3_section(source: ReportSource | None, report_date: str) -> tuple[str, int]:
    if source is None or not source.available:
        return (
            f"[Report 3 unavailable — Top 20 trains data missing for this run as on {report_date}.]",
            0,
        )
    top20 = _top_n(source.rows, 20)
    scr_rows = [
        r
        for r in top20
        if row_dict_is_scr(r, "Owning Zone", "Owning Division")
    ]
    if not scr_rows:
        text = (
            "Good morning Sir/Madam,\n\n"
            f"In Bottom 20 trains w.r.to maximum Grievances, No SCR based train had come "
            f"as on {report_date}."
        )
        return text, len(top20)

    lines = [
        "Good morning Sir/Madam,",
        "",
        f"In Bottom 20 trains w.r.to maximum Grievances, the following SCR based trains "
        f"were reported as on {report_date}:",
        "",
    ]
    for row in scr_rows:
        train_no = (row.get("Train No.") or row.get("Train No") or "").strip()
        train_name = (row.get("Train Name") or "").strip()
        received = (row.get("Received") or "").strip() or "0"
        lines.append(f"{train_no} {train_name} with {received} complaints")
    return "\n".join(lines), len(top20)


def build_report4_section(source: ReportSource | None, report_date: str) -> tuple[str, int]:
    if source is None or not source.available:
        return (
            f"[Report 4 unavailable — Cause-wise type datasets missing for this run as on {report_date}.]",
            0,
        )

    blocks: list[str] = [
        "Sir,",
        "",
        "In cause wise train wise in bottom 10 trains [w.r.to Report 10: Zone wise train wise]",
        "",
    ]
    total_rows = 0
    any_scr = False

    for type_name in COMPLAINT_TYPES_ORDERED:
        raw = source.type_datasets.get(type_name) or []
        top10 = _top_n(raw, 10)
        total_rows += len(top10)
        scr = [r for r in top10 if row_dict_is_scr(r, "Owning Zone", "Owning Division")]
        if not scr:
            continue
        any_scr = True
        # Dedupe by train no + name + received
        seen: set[tuple[str, str, str]] = set()
        by_div: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in scr:
            train_no = (row.get("Train No.") or row.get("Train No") or "").strip()
            train_name = (row.get("Train Name") or "").strip()
            received = (row.get("Received") or "").strip()
            key = (train_no, train_name, received)
            if key in seen:
                continue
            seen.add(key)
            div = (row.get("Owning Division") or "").strip() or "Unknown Division"
            by_div[div].append(row)

        blocks.append(type_name)
        for div_name, trains in by_div.items():
            blocks.append(div_name)
            for row in trains:
                train_no = (row.get("Train No.") or row.get("Train No") or "").strip()
                train_name = (row.get("Train Name") or "").strip()
                received = (row.get("Received") or "").strip() or "0"
                blocks.append(f"{train_no} {train_name} {received} complaints")
        blocks.append("")

    if not any_scr:
        blocks.append(
            f"No SCR based trains were reported in cause-wise bottom 10 as on {report_date}."
        )
        blocks.append("")

    return "\n".join(blocks).rstrip() + "\n", total_rows


def build_report5_section(source: ReportSource | None, report_date: str) -> tuple[str, int, list[str]]:
    notes: list[str] = []
    if source is None or not source.available:
        return (
            f"[Report 5 unavailable — SCR Train unsatisfactory data missing for this run as on {report_date}.]",
            0,
            notes,
        )

    counts = source.row_counts or {}
    total = counts.get("expected")
    if total is None:
        total = counts.get("unsatisfactory")
    if total is None:
        total = len(source.rows)
    try:
        total_i = int(total)
    except (TypeError, ValueError):
        total_i = len(source.rows)

    if total_i == 0 and not source.rows:
        text = (
            "Total unsatisfactory feed-back of trains are 0.\n\n"
            f"No unsatisfactory train feedback cases were reported as on {report_date}."
        )
        return text, 0, notes

    percent = counts.get("unsatisfactory_percent")
    percent_str: str | None = None
    if percent is not None:
        try:
            percent_f = float(percent)
            percent_str = f"{percent_f:.2f}".rstrip("0").rstrip(".")
            if "." not in percent_str:
                percent_str = f"{percent_f:.2f}"
            else:
                # Keep two decimals when present in source-like form
                percent_str = f"{percent_f:.2f}"
        except (TypeError, ValueError):
            notes.append("scr-train: unsatisfactory_percent unparseable")
    else:
        notes.append("scr-train: unsatisfactory_percent missing from run metadata")

    if percent_str is not None:
        header = f"Total unsatisfactory feed-back of trains are {total_i}, {percent_str}%"
    else:
        header = f"Total unsatisfactory feed-back of trains are {total_i}"

    type_counts: Counter[str] = Counter()
    div_counts: Counter[str] = Counter()
    for row in source.rows:
        t = (row.get("Type") or "").strip() or "Unknown"
        type_counts[t] += 1
        div = (
            (row.get("Div") or "").strip()
            or (row.get("Owning Div") or "").strip()
            or (row.get("Owning Division") or "").strip()
            or "Unknown"
        )
        div_counts[div] += 1

    lines = [header, ""]
    for name, count in sorted(type_counts.items(), key=lambda x: (-x[1], x[0])):
        if count <= 0:
            continue
        lines.append(f"{name}    {count}")
    lines.append("")
    lines.append("DIVISION Wise")
    div_parts = [
        f"{name} {count}"
        for name, count in sorted(div_counts.items(), key=lambda x: (-x[1], x[0]))
        if count > 0
    ]
    lines.append("[" + " ".join(div_parts) + "]" if div_parts else "[]")
    lines.append("")
    lines.append(
        "All concerned for information & N.A. w.r.to unsatisfactory feed-back "
        "in REPORT NO.5 on case to case basis."
    )
    return "\n".join(lines), len(source.rows), notes


def _safe_complaint_desc(row: dict[str, str]) -> str:
    for key in ("complaintDesc", "Complaint Description", "complaint_desc", "Remarks"):
        val = (row.get(key) or "").strip()
        if val:
            return normalize_report_text(val, field_kind="text", column_name=key)
    return ""


def _station_label(row: dict[str, str]) -> str:
    for key in (
        "Train/Station",
        "trainNameForReport/Station Name",
        "Station",
        "Station Name",
    ):
        val = (row.get(key) or "").strip()
        if val:
            return normalize_report_text(val, field_kind="text", column_name=key)
    return "Unknown Station"


def _dept_div_tag(row: dict[str, str]) -> str:
    dept = (row.get("Dept") or row.get("Department") or "").strip()
    div = (
        (row.get("Div") or "").strip()
        or (row.get("Owning Div") or "").strip()
        or (row.get("Zone") or "").strip()
        or (row.get("Owning Zone") or "").strip()
    )
    if dept and div:
        return f"[{dept}-{div}]"
    if dept:
        return f"[{dept}]"
    if div:
        return f"[{div}]"
    return "[]"


def build_report6_section(source: ReportSource | None, report_date: str) -> tuple[str, int]:
    if source is None or not source.available:
        return (
            f"[Report 6 unavailable — SCR Station unsatisfactory data missing for this run as on {report_date}.]",
            0,
        )

    counts = source.row_counts or {}
    total = counts.get("expected")
    if total is None:
        total = counts.get("unsatisfactory")
    if total is None:
        total = len(source.rows)
    try:
        total_i = int(total)
    except (TypeError, ValueError):
        total_i = len(source.rows)

    if total_i == 0 and not source.rows:
        text = (
            "Unsatisfactory feedback at station are 0.\n\n"
            f"No unsatisfactory station feedback cases were reported as on {report_date}."
        )
        return text, 0

    lines = [f"Unsatisfactory feedback at station are {total_i}", ""]
    for row in source.rows:
        # Never include sensitive fields
        station = _station_label(row)
        desc = _safe_complaint_desc(row)
        tag = _dept_div_tag(row)
        lines.append(station)
        if desc:
            lines.append(desc)
        lines.append(tag)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n", len(source.rows)


def join_summary_sections(*sections: str) -> str:
    parts = [s.rstrip() for s in sections if s and s.strip()]
    return "\n\n".join(parts) + "\n"


def build_full_summary(
    sources: RunSources,
    report_date: str,
) -> tuple[str, dict[str, int], list[str], list[str]]:
    """Return (text, source_row_counts, missing_reports, validation_notes)."""
    r3 = sources.reports.get("train-no")
    r4 = sources.reports.get("types")
    r5 = sources.reports.get("scr-train")
    r6 = sources.reports.get("scr-station")

    text3, count3 = build_report3_section(r3 if r3 and r3.available else None, report_date)
    text4, count4 = build_report4_section(r4 if r4 and r4.available else None, report_date)
    text5, count5, notes5 = build_report5_section(
        r5 if r5 and r5.available else None, report_date
    )
    text6, count6 = build_report6_section(r6 if r6 and r6.available else None, report_date)

    row_counts = {
        "train-no": count3,
        "types": count4,
        "scr-train": count5,
        "scr-station": count6,
    }
    notes = list(sources.validation_notes) + notes5
    missing = list(dict.fromkeys(sources.missing_reports))
    text = join_summary_sections(text3, text4, text5, text6)
    return text, row_counts, missing, notes
