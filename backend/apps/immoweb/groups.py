"""OMNIA — ImmoWeb / Agency Groups (M2.5.1 Franchising Layer, D-041).

Multi-branch / franchising layer on top of `agencies`:
  - An `AgencyGroup` is a holding/franchising entity that owns N branches.
  - A branch is a regular `AgencyInDB` document with `group_id` set.
  - `group_admin` users can read/write across all branches; they carry a `group_id` on their user record.
  - Standalone agencies (no `group_id`) keep working exactly as before (backward-compatible).
"""
import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException, Depends

from shared.db.connection import Database
from shared.auth.dependencies import get_current_user, require_roles
from shared.models.agency import (
    AgencyGroupInDB,
    AgencyGroupCreate,
    AgencyGroupUpdate,
    BranchAttachRequest,
    BranchSummary,
    GroupConsolidatedKPIs,
    make_slug,
)
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/groups", tags=["groups"])


# -------------------- helpers --------------------

def _public(doc: dict) -> dict:
    return {k: v for k, v in doc.items() if k != "_id"}


async def _ensure_unique_group_slug(db, base_slug: str) -> str:
    slug = base_slug
    counter = 2
    while await db.agency_groups.find_one({"slug": slug}):
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


async def _load_accessible_group(db, user: dict, group_id: str) -> dict:
    """Return the group doc if the user has access to it, otherwise raise 403/404."""
    group = await db.agency_groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="group_not_found")

    role = user.get("role")
    if role == "super_admin":
        return group
    if role == "group_admin" and user.get("group_id") == group_id:
        return group
    # branch_admin/agency_admin can *read* the group they belong to but not manage it
    # here we allow view; write endpoints use a stricter guard below
    if group_id in {ag for ag in (user.get("agency_ids") or [])}:
        return group  # rarely; user model stores agency_ids not group_id for branch users
    if user.get("group_id") == group_id:
        return group
    raise HTTPException(status_code=403, detail="group_forbidden")


def _require_group_write_access(user: dict, group_id: str) -> None:
    """Only super_admin or group_admin OF this group can mutate the group."""
    role = user.get("role")
    if role == "super_admin":
        return
    if role == "group_admin" and user.get("group_id") == group_id:
        return
    raise HTTPException(status_code=403, detail="group_write_forbidden")


# -------------------- CREATE --------------------

@router.post("", status_code=201)
async def create_group(
    payload: AgencyGroupCreate,
    user: dict = Depends(require_roles("super_admin", "group_admin", "agency_admin")),
):
    """Create a new AgencyGroup. Caller becomes owner and is promoted to group_admin.

    The caller's existing agency (if any) is **auto-attached** as the first branch
    of the group, so the creator lands on a working group with 1 branch — no extra
    manual step required.
    """
    db = Database.get()

    # A user can only own one group in MVP scope
    existing = await db.agency_groups.find_one({"owner_id": user["id"]})
    if existing:
        raise HTTPException(status_code=400, detail="group_already_exists")

    base_slug = make_slug(payload.name)
    slug = await _ensure_unique_group_slug(db, base_slug)

    group = AgencyGroupInDB(
        slug=slug,
        name=payload.name,
        franchise_name=payload.franchise_name,
        credits_mode=payload.credits_mode,
        notes=payload.notes,
        owner_id=user["id"],
    )
    doc = group.model_dump()
    await db.agency_groups.insert_one(doc)

    # Promote user to group_admin and store group_id on user
    # Exception: super_admin keeps their higher role (only set group_id)
    now = datetime.now(timezone.utc).isoformat()
    role_update = {"group_id": group.id, "updated_at": now}
    if user.get("role") != "super_admin":
        role_update["role"] = "group_admin"
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": role_update},
    )

    # Auto-attach the creator's existing agency as the first branch (P1-H fix)
    # Only if the creator has exactly one agency and it's not already in a group.
    creator_agencies = user.get("agency_ids") or []
    if len(creator_agencies) == 1:
        aid = creator_agencies[0]
        target_agency = await db.agencies.find_one(
            {"id": aid, "$or": [{"group_id": None}, {"group_id": {"$exists": False}}]},
            {"_id": 0, "id": 1, "name": 1},
        )
        if target_agency:
            await db.agencies.update_one(
                {"id": aid},
                {"$set": {"group_id": group.id, "updated_at": now}},
            )
            logger.info("AgencyGroup: auto-attached agency=%s as first branch of group=%s", aid, group.id)

    logger.info("AgencyGroup created: id=%s slug=%s owner=%s", group.id, slug, user["email"])
    return _public(doc)


# -------------------- LIST (super_admin) --------------------

@router.get("")
async def list_groups(user: dict = Depends(get_current_user)):
    """
    - super_admin: sees all groups
    - group_admin: sees own group (as a single-element list)
    - others: empty list
    """
    db = Database.get()
    role = user.get("role")
    if role == "super_admin":
        cursor = db.agency_groups.find({}, {"_id": 0}).sort("created_at", -1)
        items = await cursor.to_list(length=500)
    elif role == "group_admin" and user.get("group_id"):
        doc = await db.agency_groups.find_one({"id": user["group_id"]}, {"_id": 0})
        items = [doc] if doc else []
    else:
        items = []

    # Enrich with branches_count
    for it in items:
        it["branches_count"] = await db.agencies.count_documents({"group_id": it["id"]})
    return {"items": items, "total": len(items)}


# -------------------- GET MINE --------------------

@router.get("/me")
async def get_my_group(user: dict = Depends(get_current_user)):
    """Return the group the current user belongs to (group_admin only)."""
    db = Database.get()
    gid = user.get("group_id")
    if not gid:
        raise HTTPException(status_code=404, detail="no_group")
    doc = await db.agency_groups.find_one({"id": gid})
    if not doc:
        raise HTTPException(status_code=404, detail="group_not_found")
    out = _public(doc)
    out["branches_count"] = await db.agencies.count_documents({"group_id": gid})
    return out


# -------------------- GET one --------------------

@router.get("/{group_id}")
async def get_group(group_id: str, user: dict = Depends(get_current_user)):
    db = Database.get()
    group = await _load_accessible_group(db, user, group_id)
    out = _public(group)
    out["branches_count"] = await db.agencies.count_documents({"group_id": group_id})
    return out


# -------------------- PATCH --------------------

@router.patch("/{group_id}")
async def update_group(
    group_id: str,
    payload: AgencyGroupUpdate,
    user: dict = Depends(get_current_user),
):
    db = Database.get()
    _ = await _load_accessible_group(db, user, group_id)
    _require_group_write_access(user, group_id)

    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="empty_payload")
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.agency_groups.update_one({"id": group_id}, {"$set": data})
    updated = await db.agency_groups.find_one({"id": group_id})
    return _public(updated)


@router.delete("/{group_id}")
async def delete_group(group_id: str, user: dict = Depends(get_current_user)):
    """Delete a group. Detaches all branches (they become standalone) and clears group_id on the owner."""
    db = Database.get()
    _ = await _load_accessible_group(db, user, group_id)
    _require_group_write_access(user, group_id)

    now = datetime.now(timezone.utc).isoformat()
    # Detach all branches
    await db.agencies.update_many(
        {"group_id": group_id},
        {"$set": {"group_id": None, "branch_code": None, "updated_at": now}},
    )
    # Clear group_id on all users linked to this group (owner + any branch_admin)
    await db.users.update_many(
        {"group_id": group_id},
        {"$set": {"group_id": None, "updated_at": now}},
    )
    await db.agency_groups.delete_one({"id": group_id})
    logger.info("AgencyGroup deleted: id=%s by=%s", group_id, user["email"])
    return {"status": "ok", "group_id": group_id}


# -------------------- BRANCHES --------------------

@router.get("/{group_id}/branches")
async def list_branches(group_id: str, user: dict = Depends(get_current_user)):
    """List all branches (agencies) belonging to a group, with rollup counts."""
    db = Database.get()
    _ = await _load_accessible_group(db, user, group_id)

    cursor = db.agencies.find({"group_id": group_id}, {"_id": 0}).sort("created_at", 1)
    agencies = await cursor.to_list(length=500)

    summaries: List[dict] = []
    for a in agencies:
        aid = a["id"]
        props_active = await db.properties.count_documents({"agency_id": aid, "status": "active"})
        clients_total = await db.clients.count_documents({"agency_id": aid})
        leads_open = await db.leads.count_documents({"agency_id": aid, "status": "new"})
        summaries.append(
            BranchSummary(
                id=aid,
                slug=a.get("slug", ""),
                display_name=a.get("display_name", ""),
                branch_code=a.get("branch_code"),
                plan_type=a.get("plan_type", "hybrid"),
                plan=a.get("plan", "free"),
                is_active=a.get("is_active", True),
                city=(a.get("address") or {}).get("city"),
                properties_active=props_active,
                clients_total=clients_total,
                leads_open=leads_open,
            ).model_dump()
        )
    return {"items": summaries, "total": len(summaries)}


@router.post("/{group_id}/branches", status_code=201)
async def attach_branch(
    group_id: str,
    payload: BranchAttachRequest,
    user: dict = Depends(get_current_user),
):
    """Attach an existing agency as a branch of this group."""
    db = Database.get()
    _ = await _load_accessible_group(db, user, group_id)
    _require_group_write_access(user, group_id)

    agency = await db.agencies.find_one({"id": payload.agency_id})
    if not agency:
        raise HTTPException(status_code=404, detail="agency_not_found")
    if agency.get("group_id") and agency["group_id"] != group_id:
        raise HTTPException(status_code=409, detail="agency_already_in_another_group")

    # C6 — anti branch-hijacking: only super_admin can attach agencies not owned by the caller
    if user.get("role") != "super_admin":
        owned = (
            agency.get("owner_id") == user["id"]
            or agency["id"] in (user.get("agency_ids") or [])
        )
        if not owned:
            raise HTTPException(status_code=403, detail="agency_not_owned")

    now = datetime.now(timezone.utc).isoformat()
    update = {"group_id": group_id, "updated_at": now}
    if payload.branch_code:
        update["branch_code"] = payload.branch_code
    await db.agencies.update_one({"id": payload.agency_id}, {"$set": update})
    logger.info("Branch attached: group=%s agency=%s by=%s", group_id, payload.agency_id, user["email"])
    updated = await db.agencies.find_one({"id": payload.agency_id})
    return _public(updated)


@router.delete("/{group_id}/branches/{agency_id}", status_code=200)
async def detach_branch(
    group_id: str,
    agency_id: str,
    user: dict = Depends(get_current_user),
):
    """Detach an agency from the group (agency becomes standalone again)."""
    db = Database.get()
    _ = await _load_accessible_group(db, user, group_id)
    _require_group_write_access(user, group_id)

    agency = await db.agencies.find_one({"id": agency_id, "group_id": group_id})
    if not agency:
        raise HTTPException(status_code=404, detail="branch_not_found_in_group")

    now = datetime.now(timezone.utc).isoformat()
    await db.agencies.update_one(
        {"id": agency_id},
        {"$set": {"group_id": None, "branch_code": None, "updated_at": now}},
    )
    logger.info("Branch detached: group=%s agency=%s by=%s", group_id, agency_id, user["email"])
    return {"status": "ok", "agency_id": agency_id, "group_id": None}


# -------------------- CONSOLIDATED KPIs --------------------

@router.get("/{group_id}/consolidated", response_model=GroupConsolidatedKPIs)
async def group_consolidated_kpis(group_id: str, user: dict = Depends(get_current_user)):
    """Rollup KPIs across all branches of the group."""
    db = Database.get()
    _ = await _load_accessible_group(db, user, group_id)

    branch_ids: List[str] = [
        a["id"] async for a in db.agencies.find({"group_id": group_id}, {"id": 1})
    ]
    active_branch_ids: List[str] = [
        a["id"] async for a in db.agencies.find(
            {"group_id": group_id, "is_active": True}, {"id": 1}
        )
    ]

    if not branch_ids:
        return GroupConsolidatedKPIs(
            group_id=group_id, branches_count=0, branches_active=0,
        )

    aid_filter = {"$in": branch_ids}
    props_active = await db.properties.count_documents({"agency_id": aid_filter, "status": "active"})
    props_total = await db.properties.count_documents({"agency_id": aid_filter})
    clients_total = await db.clients.count_documents({"agency_id": aid_filter})
    leads_open = await db.leads.count_documents({"agency_id": aid_filter, "status": "new"})
    leads_total = await db.leads.count_documents({"agency_id": aid_filter})

    return GroupConsolidatedKPIs(
        group_id=group_id,
        branches_count=len(branch_ids),
        branches_active=len(active_branch_ids),
        properties_active=props_active,
        properties_total=props_total,
        clients_total=clients_total,
        leads_open=leads_open,
        leads_total=leads_total,
    )
