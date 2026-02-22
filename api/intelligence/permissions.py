"""
Permission management — deny-by-default access control
"""
from sqlalchemy.orm import Session
from intelligence.retrieval import grant_permission, check_permission


def setup_agent_permissions(db: Session, agent_id: str, spec: dict):
    """Set up permissions based on agent spec data_permissions field"""
    data_perms = spec.get("data_permissions", {})

    # Grant namespace permissions
    for ns in data_perms.get("vector_namespaces", []):
        grant_permission(db, agent_id, "vector_namespace", ns)

    # Grant table permissions
    for table in data_perms.get("tables", []):
        grant_permission(db, agent_id, "table", table)

    # Grant file permissions
    for file_id in data_perms.get("files", []):
        grant_permission(db, agent_id, "file", file_id)

    # Grant dataset permissions
    for ds in data_perms.get("datasets", []):
        grant_permission(db, agent_id, "dataset", ds)
