from .base import BaseAdapter, SignalDict
from .contracts_finder import ContractsFinderAdapter
from .ukri_gtr import UKRIGtrAdapter
from .ons import ONSDataAdapter

__all__ = [
    "BaseAdapter",
    "SignalDict",
    "ContractsFinderAdapter",
    "UKRIGtrAdapter",
    "ONSDataAdapter",
]
