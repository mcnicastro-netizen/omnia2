"""OMNIA · Shared object storage helpers."""
from .objstore import init_storage, put_object, get_object, delete_object, ObjStoreError

__all__ = ["init_storage", "put_object", "get_object", "delete_object", "ObjStoreError"]
