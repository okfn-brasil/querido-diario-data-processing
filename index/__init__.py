from .interfaces import IndexInterface
from .opensearch import create_index_interface, OpenSearchInterface

__all__ = [
    "create_index_interface",
    "IndexInterface",
    "OpenSearchInterface",
]
