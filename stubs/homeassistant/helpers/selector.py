"""Home Assistant selector helpers stubs."""

from typing import Any, Dict, List, Optional, Union


class Selector:
    """Base selector class."""

    def __init__(
        self,
        config: Union[Dict[str, Any], "EntitySelectorConfig", "TextSelectorConfig"],
    ) -> None:
        """Initialize selector."""
        ...


class EntitySelectorConfig:
    """Configuration for entity selector."""

    def __init__(
        self,
        *,
        domain: Optional[str] = None,
        device_class: Optional[str] = None,
        multiple: bool = False,
    ) -> None:
        """Initialize entity selector config."""
        ...


class TextSelectorConfig:
    """Configuration for text selector."""

    def __init__(
        self,
        *,
        multiline: bool = False,
        type: Optional[str] = None,
    ) -> None:
        """Initialize text selector config."""
        ...


class EntitySelector(Selector):
    """Entity selector."""

    def __init__(
        self,
        config: Optional[Union[Dict[str, Any], EntitySelectorConfig]] = None,
        *,
        domain: Optional[str] = None,
        device_class: Optional[str] = None,
        multiple: bool = False,
    ) -> None:
        """Initialize entity selector."""
        ...


class TextSelector(Selector):
    """Text selector."""

    def __init__(
        self,
        config: Optional[Union[Dict[str, Any], TextSelectorConfig]] = None,
        *,
        multiline: bool = False,
        type: Optional[str] = None,
    ) -> None:
        """Initialize text selector."""
        ...
