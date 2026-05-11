from __future__ import annotations

from datetime import datetime

from . import meta_api
from .config import FB_ACCESS_TOKEN
from .models import MetaConnection


def list_connections(db):
    return db.query(MetaConnection).order_by(MetaConnection.created_at.desc()).all()


def get_active_connection(db):
    active = db.query(MetaConnection).filter(MetaConnection.is_active == True).first()
    if active:
        return active
    connections = list_connections(db)
    if len(connections) == 1:
        connections[0].is_active = True
        db.commit()
        return connections[0]
    return None


def get_active_token(db):
    connection = get_active_connection(db)
    if connection and connection.token:
        return connection.token
    return FB_ACCESS_TOKEN or None


def has_any_token(db) -> bool:
    return bool(get_active_token(db))


def set_active_connection(db, connection_id: int):
    connections = db.query(MetaConnection).all()
    selected = None
    for connection in connections:
        is_target = connection.id == connection_id
        connection.is_active = is_target
        if is_target:
            selected = connection
    db.commit()
    return selected


def test_connection_token(token: str):
    businesses = meta_api.list_businesses(token=token)
    accounts = meta_api.list_ad_accounts(token=token)
    pages = meta_api.list_pages(token=token)
    return {
        "businesses": businesses,
        "accounts": accounts,
        "pages": pages,
    }


def upsert_env_connection(db):
    if not FB_ACCESS_TOKEN or db.query(MetaConnection).count() > 0:
        return None
    connection = MetaConnection(
        name="Default ENV Token",
        token=FB_ACCESS_TOKEN,
        token_last4=FB_ACCESS_TOKEN[-4:],
        is_active=True,
        is_valid=False,
        created_at=datetime.utcnow(),
    )
    db.add(connection)
    db.commit()
    return connection
