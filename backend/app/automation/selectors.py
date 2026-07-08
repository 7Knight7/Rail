"""CSS/XPath selectors for RailMadad portal automation (populated in later phases)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PortalSelectors:
    """Placeholder selector registry for portal UI elements."""

    login_username: str = ""
    login_password: str = ""
    login_submit: str = ""
    reports_menu: str = ""
    reports_table: str = ""
    report1_frame: str = "iframe[name='main'], iframe#main, iframe"
    report1_generate: str = (
        "input[type='submit'][value*='Submit'], button:has-text('Submit'), "
        "input[type='submit'][value*='Generate'], button:has-text('Generate'), "
        "input[type='submit'][value*='View'], button:has-text('View Report'), "
        "button:has-text('Show Report'), button:has-text('Search'), "
        "input[type='submit']"
    )
    report1_table: str = "table:has(tbody tr), table.dataTable, .report-table, #reportData"
    report1_grid: str = ".dataTables_wrapper table, .grid-table, [role='grid']"
    report1_from_date: str = ""
    report1_to_date: str = ""


selectors = PortalSelectors()
