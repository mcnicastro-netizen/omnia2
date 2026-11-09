"""OMNIA · Shared object storage helpers."""
from .objstore import (
    ObjStoreError,
    delete_object,
    get_object,
    init_storage,
    list_object_keys,
    put_object,
)

__all__ = [
    "init_storage",
    "put_object",
    "get_object",
    "delete_object",
    "list_object_keys",
    "ObjStoreError",
]
