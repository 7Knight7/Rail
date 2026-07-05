"""Default application setting definitions — bootstrap only; extend via import."""

import json

SETTING_CATEGORIES = [
    {"slug": "general", "label": "General Settings", "description": "Organization-wide defaults"},
    {"slug": "report", "label": "Report Settings", "description": "Report generation behavior"},
    {"slug": "upload", "label": "Upload Settings", "description": "File upload constraints"},
    {"slug": "export", "label": "Export Settings", "description": "Output formatting and naming"},
    {"slug": "summary", "label": "Summary Settings", "description": "AI summary preferences"},
    {"slug": "automation", "label": "Automation Settings", "description": "Scheduled runs and retries"},
    {"slug": "security", "label": "Security Settings", "description": "Authentication and audit policy"},
    {"slug": "system", "label": "System Settings", "description": "Application identity and locale"},
]


def _def(
    category: str,
    key: str,
    label: str,
    value_type: str,
    default,
    *,
    description: str | None = None,
    validation: dict | None = None,
    options: list[dict] | None = None,
    sort_order: int = 0,
) -> dict:
    return {
        "category": category,
        "key": key,
        "label": label,
        "description": description,
        "value_type": value_type,
        "default_value": json.dumps(default),
        "validation_json": json.dumps(validation) if validation else None,
        "options_json": json.dumps(options) if options else None,
        "sort_order": sort_order,
        "is_editable": True,
    }


DEFAULT_SETTING_DEFINITIONS: list[dict] = [
    # General
    _def("general", "organization_name", "Organization Name", "string", "South Central Railway", sort_order=1),
    _def("general", "support_email", "Support Email", "string", "support@scr.railway.in", sort_order=2),
    _def("general", "default_page_size", "Default Page Size", "enum", 25, options=[
        {"label": "10", "value": 10},
        {"label": "25", "value": 25},
        {"label": "50", "value": 50},
        {"label": "100", "value": 100},
    ], sort_order=3),
    _def("general", "enable_notifications", "Enable Notifications", "boolean", True, sort_order=4),
    # Report
    _def("report", "default_template_id", "Default Report Template", "string", "", description="Template ID or empty for workflow default", sort_order=1),
    _def("report", "top_values", "Top Values (N)", "json", {
        "division": 25,
        "train": 20,
        "types": 10,
        "scr_train": 20,
        "scr_station": 15,
    }, description="Row limits per report type", sort_order=2),
    _def("report", "default_sorting", "Default Sorting", "json", {
        "field": "complaint_count",
        "direction": "desc",
    }, sort_order=3),
    _def("report", "default_filtering", "Default Filtering", "json", {
        "exclude_empty": True,
        "min_complaints": 0,
    }, sort_order=4),
    _def("report", "highlight_rules_enabled", "Enable Highlight Rules", "boolean", True, sort_order=5),
    _def("report", "export_formats", "Export Formats", "multiselect", ["excel", "pdf"], options=[
        {"label": "Excel", "value": "excel"},
        {"label": "PDF", "value": "pdf"},
        {"label": "CSV", "value": "csv"},
    ], sort_order=6),
    # Upload
    _def("upload", "allowed_file_types", "Allowed File Types", "multiselect", [".xlsx", ".xls", ".csv"], options=[
        {"label": "Excel (.xlsx)", "value": ".xlsx"},
        {"label": "Excel Legacy (.xls)", "value": ".xls"},
        {"label": "CSV", "value": ".csv"},
    ], sort_order=1),
    _def("upload", "max_upload_size_mb", "Maximum Upload Size (MB)", "number", 50, validation={"min": 1, "max": 500}, sort_order=2),
    _def("upload", "max_rows", "Maximum Rows", "number", 100000, validation={"min": 100, "max": 1000000}, sort_order=3),
    _def("upload", "max_columns", "Maximum Columns", "number", 200, validation={"min": 1, "max": 1000}, sort_order=4),
    _def("upload", "allow_multiple_uploads", "Allow Multiple Uploads", "boolean", True, sort_order=5),
    # Export
    _def("export", "excel_formatting", "Excel Formatting", "json", {
        "header_bold": True,
        "freeze_header": True,
        "auto_filter": True,
        "date_format": "DD/MM/YYYY",
    }, sort_order=1),
    _def("export", "pdf_formatting", "PDF Formatting", "json", {
        "page_size": "A4",
        "orientation": "landscape",
        "include_header": True,
        "include_footer": True,
    }, sort_order=2),
    _def("export", "file_naming_pattern", "File Naming Pattern", "string", "{report_name}_{date}_{division}", description="Tokens: {report_name}, {date}, {division}, {workflow}", sort_order=3),
    _def("export", "output_folder", "Output Folder", "string", "exports", sort_order=4),
    # Summary
    _def("summary", "default_prompt_template_id", "Default Prompt Template", "string", "", description="AI prompt template ID", sort_order=1),
    _def("summary", "default_summary_type", "Default Summary Type", "enum", "executive", options=[
        {"label": "Executive Summary", "value": "executive"},
        {"label": "WhatsApp", "value": "whatsapp"},
        {"label": "Email", "value": "email"},
        {"label": "Daily Highlights", "value": "daily_highlights"},
        {"label": "Key Observations", "value": "key_observations"},
    ], sort_order=2),
    _def("summary", "summary_style", "Summary Style", "enum", "formal", options=[
        {"label": "Formal", "value": "formal"},
        {"label": "Concise", "value": "concise"},
        {"label": "Detailed", "value": "detailed"},
    ], sort_order=3),
    _def("summary", "official_language", "Official Language", "enum", "en", options=[
        {"label": "English", "value": "en"},
        {"label": "Hindi", "value": "hi"},
        {"label": "Bilingual (EN + HI)", "value": "bilingual"},
    ], sort_order=4),
    _def("summary", "whatsapp_formatting", "WhatsApp Formatting", "json", {
        "use_bullets": True,
        "max_length": 500,
        "use_bold_markers": True,
    }, sort_order=5),
    # Automation
    _def("automation", "download_folder", "Download Folder", "string", "downloads", sort_order=1),
    _def("automation", "retry_count", "Retry Count", "number", 3, validation={"min": 0, "max": 10}, sort_order=2),
    _def("automation", "timeout_seconds", "Timeout (seconds)", "number", 300, validation={"min": 30, "max": 3600}, sort_order=3),
    _def("automation", "run_schedule", "Run Schedule (cron)", "string", "0 6 * * *", description="Cron expression for scheduled runs", sort_order=4),
    _def("automation", "auto_run_enabled", "Enable Scheduled Runs", "boolean", False, sort_order=5),
    # Security
    _def("security", "session_timeout_minutes", "Session Timeout (minutes)", "number", 30, validation={"min": 5, "max": 480}, sort_order=1),
    _def("security", "password_policy", "Password Policy", "json", {
        "min_length": 8,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_digit": True,
        "require_special": False,
    }, sort_order=2),
    _def("security", "max_login_attempts", "Max Login Attempts", "number", 5, validation={"min": 3, "max": 20}, sort_order=3),
    _def("security", "lockout_duration_minutes", "Lockout Duration (minutes)", "number", 15, validation={"min": 1, "max": 120}, sort_order=4),
    _def("security", "audit_enabled", "Enable Audit Logging", "boolean", True, sort_order=5),
    _def("security", "audit_retention_days", "Audit Retention (days)", "number", 90, validation={"min": 7, "max": 365}, sort_order=6),
    # System
    _def("system", "application_name", "Application Name", "string", "Railway Report Automation Platform", sort_order=1),
    _def("system", "timezone", "Timezone", "enum", "Asia/Kolkata", options=[
        {"label": "India Standard Time (IST)", "value": "Asia/Kolkata"},
        {"label": "UTC", "value": "UTC"},
    ], sort_order=2),
    _def("system", "default_language", "Default Language", "enum", "en", options=[
        {"label": "English", "value": "en"},
        {"label": "Hindi", "value": "hi"},
    ], sort_order=3),
    _def("system", "date_format", "Date Format", "enum", "DD/MM/YYYY", options=[
        {"label": "DD/MM/YYYY", "value": "DD/MM/YYYY"},
        {"label": "MM/DD/YYYY", "value": "MM/DD/YYYY"},
        {"label": "YYYY-MM-DD", "value": "YYYY-MM-DD"},
    ], sort_order=4),
    _def("system", "theme", "Theme", "enum", "light", options=[
        {"label": "Light", "value": "light"},
        {"label": "Dark", "value": "dark"},
        {"label": "System", "value": "system"},
    ], sort_order=5),
]
