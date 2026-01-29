from .base import BaseAdapter, SignalDict
from .contracts_finder import ContractsFinderAdapter
from .ukri_gtr import UKRIGtrAdapter
from .ons import ONSDataAdapter
from .registry import ADAPTER_REGISTRY, get_adapter_cls

__all__ = [
    "BaseAdapter",
    "SignalDict",
    "ContractsFinderAdapter",
    "UKRIGtrAdapter",
    "ONSDataAdapter",
    "ADAPTER_REGISTRY",
    "get_adapter_cls",
]
