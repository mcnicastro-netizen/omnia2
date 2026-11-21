"""Mongo access for staging — requires RAILWAY_API_TOKEN; refuses non-canonical DB."""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

from pymongo import MongoClient
from pymongo.database import Database

from . import config
from .run_id import validate_run_id


def _gql(token: str, query: str, variables: dict | None = None) -> dict:
    req = urllib.request.Request(
        "https://backboard.railway.app/graphql/v2",
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "omnia-d7-e2e/1.0",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        payload = json.load(r)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]


def assert_staging_project(token: str) -> dict:
    """Validate against CANONICAL pins only (not env-overridable identity)."""
    proj = _gql(
        token,
        "query($id:String!){ project(id:$id){ id name } }",
        {"id": config.CANONICAL_RAILWAY_PROJECT_ID},
    )["project"]
    if (
        proj["id"] != config.CANONICAL_RAILWAY_PROJECT_ID
        or proj["name"] != config.CANONICAL_RAILWAY_PROJECT_NAME
    ):
        raise RuntimeError(f"railway_project_mismatch:{proj}")
    return proj


def fetch_api_service_variables(token: str) -> dict:
    """Read Railway API service env vars (values used only for gates; never logged)."""
    return _gql(
        token,
        """query($projectId:String!,$environmentId:String!,$serviceId:String!){
          variables(projectId:$projectId, environmentId:$environmentId, serviceId:$serviceId)
        }""",
        {
            "projectId": config.CANONICAL_RAILWAY_PROJECT_ID,
            "environmentId": config.CANONICAL_RAILWAY_ENV_ID,
            "serviceId": config.CANONICAL_RAILWAY_API_SERVICE_ID,
        },
    )["variables"]


def connect_staging_db(
    *,
    proxy_host: str | None = None,
    proxy_port: int | None = None,
) -> Database:
    token = os.environ.get("RAILWAY_API_TOKEN") or os.environ.get("RAILWAY_TOKEN")
    if not token:
        raise RuntimeError("missing_RAILWAY_API_TOKEN")
    assert_staging_project(token)

    api_vars = fetch_api_service_variables(token)
    db_name = api_vars.get("DB_NAME") or api_vars.get("MONGO_DATABASE")
    if db_name != config.CANONICAL_STAGING_DB_NAME:
        raise RuntimeError(f"db_name_not_staging:{db_name}")

    mongo_vars = _gql(
        token,
        """query($projectId:String!,$environmentId:String!,$serviceId:String!){
          variables(projectId:$projectId, environmentId:$environmentId, serviceId:$serviceId)
        }""",
        {
            "projectId": config.CANONICAL_RAILWAY_PROJECT_ID,
            "environmentId": config.CANONICAL_RAILWAY_ENV_ID,
            "serviceId": config.CANONICAL_RAILWAY_MONGO_SERVICE_ID,
        },
    )["variables"]
    host_internal = mongo_vars.get("MONGOHOST") or ""
    if config.CANONICAL_STAGING_MONGO_HOST_MARKER not in host_internal:
        raise RuntimeError(f"mongo_host_not_staging:{host_internal}")

    host = proxy_host or os.environ.get("OMNIA_D7_MONGO_PROXY_HOST") or config.DEFAULT_MONGO_PROXY_HOST
    port = int(
        proxy_port
        or os.environ.get("OMNIA_D7_MONGO_PROXY_PORT")
        or config.DEFAULT_MONGO_PROXY_PORT
    )
    user = mongo_vars["MONGOUSER"]
    pwd = mongo_vars["MONGOPASSWORD"]
    uri = f"mongodb://{user}:{pwd}@{host}:{port}/?authSource=admin"
    client = MongoClient(uri, serverSelectionTimeoutMS=20000)
    client.admin.command("ping")
    return client[db_name]


def scoped_filter(run_id: str) -> dict[str, Any]:
    """Cleanup/select ONLY documents tagged with this validated run_id."""
    rid = validate_run_id(run_id)
    return {config.RUN_TAG_FIELD: rid}
