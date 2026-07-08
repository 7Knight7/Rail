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


selectors = PortalSelectors()
