from __future__ import annotations

from typing import Dict, Type

from .contracts_finder import ContractsFinderAdapter
from .ons import ONSDataAdapter
from .ukri_gtr import UKRIGtrAdapter
from .base import BaseAdapter

ADAPTER_REGISTRY: Dict[str, Type[BaseAdapter]] = {
    "contracts_finder": ContractsFinderAdapter,
    "ukri_gtr": UKRIGtrAdapter,
    "ons": ONSDataAdapter,
}


def get_adapter_cls(name: str) -> Type[BaseAdapter] | None:
    """Return adapter class by source name."""
    return ADAPTER_REGISTRY.get(name)
