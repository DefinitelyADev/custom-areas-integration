"""Home Assistant data entry flow stubs."""

from typing import Any, Dict, Optional


class FlowResult:
    """Result of a data entry flow step."""

    def __init__(
        self,
        type: str,
        flow_id: Optional[str] = None,
        handler: Optional[str] = None,
        step_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, str]] = None,
        description_placeholders: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize flow result."""
        ...
