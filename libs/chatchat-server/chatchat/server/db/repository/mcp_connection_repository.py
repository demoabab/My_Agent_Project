import uuid
from typing import Dict, List, Optional

from chatchat.server.db.models.mcp_connection_model import MCPConnectionModel, MCPProfileModel
from chatchat.server.db.session import with_session


def _apply_tenant_filter(query, model, tenant_id):
    if tenant_id is not None:
        return query.filter(model.tenant_id == tenant_id)
    return query


@with_session
def add_mcp_connection(
    session,
    server_name: str,
    args: List[str] = None,
    env: Dict[str, str] = None,
    cwd: str = None,
    transport: str = "stdio",
    timeout: int = 30,
    enabled: bool = True,
    description: str = "",
    config: Dict = None,
    connection_id: str = None,
    tenant_id: Optional[str] = None,
):
    if not connection_id:
        connection_id = uuid.uuid4().hex

    if args is None:
        args = []
    if env is None:
        env = {}
    if config is None:
        config = {}

    mcp_connection = MCPConnectionModel(
        id=connection_id,
        server_name=server_name,
        args=args,
        env=env,
        cwd=cwd,
        transport=transport,
        timeout=timeout,
        enabled=enabled,
        description=description,
        config=config,
        tenant_id=tenant_id,
    )
    session.add(mcp_connection)
    session.commit()
    return mcp_connection.id


@with_session
def update_mcp_connection(
    session,
    connection_id: str,
    server_name: str = None,
    args: List[str] = None,
    env: Dict[str, str] = None,
    cwd: str = None,
    transport: str = None,
    timeout: int = None,
    enabled: bool = None,
    description: str = None,
    config: Dict = None,
    tenant_id: Optional[str] = None,
):
    query = session.query(MCPConnectionModel).filter_by(id=connection_id)
    query = _apply_tenant_filter(query, MCPConnectionModel, tenant_id)
    mcp_connection = query.first()

    if mcp_connection is not None:
        if server_name is not None:
            mcp_connection.server_name = server_name
        if args is not None:
            mcp_connection.args = args
        if env is not None:
            mcp_connection.env = env
        if cwd is not None:
            mcp_connection.cwd = cwd
        if transport is not None:
            mcp_connection.transport = transport
        if timeout is not None:
            mcp_connection.timeout = timeout
        if enabled is not None:
            mcp_connection.enabled = enabled
        if description is not None:
            mcp_connection.description = description
        if config is not None:
            mcp_connection.config = config

        session.add(mcp_connection)
        session.commit()
        return mcp_connection.id
    return None


@with_session
def get_mcp_connection_by_id(session, connection_id: str, tenant_id: Optional[str] = None) -> Optional[dict]:
    query = session.query(MCPConnectionModel).filter_by(id=connection_id)
    query = _apply_tenant_filter(query, MCPConnectionModel, tenant_id)
    mcp_connection = query.first()
    if mcp_connection:
        return {
            "id": mcp_connection.id,
            "server_name": mcp_connection.server_name,
            "args": mcp_connection.args,
            "env": mcp_connection.env,
            "cwd": mcp_connection.cwd,
            "transport": mcp_connection.transport,
            "timeout": mcp_connection.timeout,
            "enabled": mcp_connection.enabled,
            "description": mcp_connection.description,
            "config": mcp_connection.config,
            "create_time": mcp_connection.create_time.isoformat() if mcp_connection.create_time else None,
            "update_time": mcp_connection.update_time.isoformat() if mcp_connection.update_time else None,
        }
    return None


@with_session
def get_mcp_connections_by_server_name(session, server_name: str, tenant_id: Optional[str] = None) -> List[dict]:
    query = session.query(MCPConnectionModel).filter_by(server_name=server_name)
    query = _apply_tenant_filter(query, MCPConnectionModel, tenant_id)
    connections = query.all()
    return [
        {
            "id": conn.id,
            "server_name": conn.server_name,
            "args": conn.args,
            "env": conn.env,
            "cwd": conn.cwd,
            "transport": conn.transport,
            "timeout": conn.timeout,
            "enabled": conn.enabled,
            "description": conn.description,
            "config": conn.config,
            "create_time": conn.create_time.isoformat() if conn.create_time else None,
            "update_time": conn.update_time.isoformat() if conn.update_time else None,
        }
        for conn in connections
    ]


@with_session
def get_all_mcp_connections(session, enabled_only: bool = False, tenant_id: Optional[str] = None) -> List[dict]:
    query = session.query(MCPConnectionModel)
    query = _apply_tenant_filter(query, MCPConnectionModel, tenant_id)
    if enabled_only:
        query = query.filter_by(enabled=True)

    connections = query.order_by(MCPConnectionModel.create_time.desc()).all()
    return [
        {
            "id": conn.id,
            "server_name": conn.server_name,
            "args": conn.args,
            "env": conn.env,
            "cwd": conn.cwd,
            "transport": conn.transport,
            "timeout": conn.timeout,
            "enabled": conn.enabled,
            "description": conn.description,
            "config": conn.config,
            "create_time": conn.create_time.isoformat() if conn.create_time else None,
            "update_time": conn.update_time.isoformat() if conn.update_time else None,
        }
        for conn in connections
    ]


@with_session
def get_enabled_mcp_connections(session, tenant_id: Optional[str] = None) -> List[dict]:
    query = session.query(MCPConnectionModel).filter_by(enabled=True)
    query = _apply_tenant_filter(query, MCPConnectionModel, tenant_id)
    connections = query.order_by(MCPConnectionModel.create_time.desc()).all()
    return [
        {
            "id": conn.id,
            "server_name": conn.server_name,
            "args": conn.args,
            "env": conn.env,
            "cwd": conn.cwd,
            "transport": conn.transport,
            "timeout": conn.timeout,
            "enabled": conn.enabled,
            "description": conn.description,
            "config": conn.config,
            "create_time": conn.create_time.isoformat() if conn.create_time else None,
            "update_time": conn.update_time.isoformat() if conn.update_time else None,
        }
        for conn in connections
    ]


@with_session
def delete_mcp_connection(session, connection_id: str, tenant_id: Optional[str] = None) -> bool:
    query = session.query(MCPConnectionModel).filter_by(id=connection_id)
    query = _apply_tenant_filter(query, MCPConnectionModel, tenant_id)
    mcp_connection = query.first()
    if mcp_connection is not None:
        session.delete(mcp_connection)
        session.commit()
        return True
    return False


@with_session
def enable_mcp_connection(session, connection_id: str, tenant_id: Optional[str] = None) -> bool:
    query = session.query(MCPConnectionModel).filter_by(id=connection_id)
    query = _apply_tenant_filter(query, MCPConnectionModel, tenant_id)
    mcp_connection = query.first()
    if mcp_connection is not None:
        mcp_connection.enabled = True
        session.add(mcp_connection)
        session.commit()
        return True
    return False


@with_session
def disable_mcp_connection(session, connection_id: str, tenant_id: Optional[str] = None) -> bool:
    query = session.query(MCPConnectionModel).filter_by(id=connection_id)
    query = _apply_tenant_filter(query, MCPConnectionModel, tenant_id)
    mcp_connection = query.first()
    if mcp_connection is not None:
        mcp_connection.enabled = False
        session.add(mcp_connection)
        session.commit()
        return True
    return False


@with_session
def search_mcp_connections(
    session,
    keyword: str = None,
    enabled: bool = None,
    limit: int = 50,
    tenant_id: Optional[str] = None,
) -> List[dict]:
    query = session.query(MCPConnectionModel)
    query = _apply_tenant_filter(query, MCPConnectionModel, tenant_id)

    if keyword:
        keyword = f"%{keyword}%"
        query = query.filter(
            MCPConnectionModel.server_name.like(keyword) |
            MCPConnectionModel.description.like(keyword)
        )

    if enabled is not None:
        query = query.filter_by(enabled=enabled)

    connections = query.order_by(MCPConnectionModel.create_time.desc()).limit(limit).all()
    return [
        {
            "id": conn.id,
            "server_name": conn.server_name,
            "args": conn.args,
            "env": conn.env,
            "cwd": conn.cwd,
            "transport": conn.transport,
            "timeout": conn.timeout,
            "enabled": conn.enabled,
            "description": conn.description,
            "config": conn.config,
            "create_time": conn.create_time.isoformat() if conn.create_time else None,
            "update_time": conn.update_time.isoformat() if conn.update_time else None,
        }
        for conn in connections
    ]


# MCP Profile 相关操作
@with_session
def get_mcp_profile(session, tenant_id: Optional[str] = None) -> Optional[dict]:
    query = session.query(MCPProfileModel)
    query = _apply_tenant_filter(query, MCPProfileModel, tenant_id)
    profile = query.first()
    if profile:
        return {
            "id": profile.id,
            "timeout": profile.timeout,
            "working_dir": profile.working_dir,
            "env_vars": profile.env_vars,
            "update_time": profile.update_time.isoformat() if profile.update_time else None
        }
    return None


@with_session
def create_mcp_profile(
    session,
    timeout: int = 30,
    working_dir: str = "/tmp",
    env_vars: Dict[str, str] = None,
    tenant_id: Optional[str] = None,
):
    if env_vars is None:
        env_vars = {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "PYTHONPATH": "/app",
            "HOME": "/tmp"
        }

    query = session.query(MCPProfileModel)
    query = _apply_tenant_filter(query, MCPProfileModel, tenant_id)
    existing_profile = query.first()
    if existing_profile:
        return update_mcp_profile(
            session,
            timeout=timeout,
            working_dir=working_dir,
            env_vars=env_vars,
            tenant_id=tenant_id,
        )

    profile = MCPProfileModel(
        timeout=timeout,
        working_dir=working_dir,
        env_vars=env_vars,
        tenant_id=tenant_id,
    )
    session.add(profile)
    session.commit()
    return profile.id


@with_session
def update_mcp_profile(
    session,
    timeout: int = None,
    working_dir: str = None,
    env_vars: Dict[str, str] = None,
    tenant_id: Optional[str] = None,
):
    query = session.query(MCPProfileModel)
    query = _apply_tenant_filter(query, MCPProfileModel, tenant_id)
    profile = query.first()
    if profile is not None:
        if timeout is not None:
            profile.timeout = timeout
        if working_dir is not None:
            profile.working_dir = working_dir
        if env_vars is not None:
            profile.env_vars = env_vars

        session.add(profile)
        session.commit()
        return profile.id
    else:
        return create_mcp_profile(
            session,
            timeout=timeout or 30,
            working_dir=working_dir or "/tmp",
            env_vars=env_vars,
            tenant_id=tenant_id,
        )


@with_session
def reset_mcp_profile(session, tenant_id: Optional[str] = None):
    query = session.query(MCPProfileModel)
    query = _apply_tenant_filter(query, MCPProfileModel, tenant_id)
    profile = query.first()
    if profile is not None:
        profile.timeout = 30
        profile.working_dir = "/tmp"
        profile.env_vars = {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "PYTHONPATH": "/app",
            "HOME": "/tmp"
        }

        session.add(profile)
        session.commit()
        return True
    return False


@with_session
def delete_mcp_profile(session, tenant_id: Optional[str] = None):
    query = session.query(MCPProfileModel)
    query = _apply_tenant_filter(query, MCPProfileModel, tenant_id)
    profile = query.first()
    if profile is not None:
        session.delete(profile)
        session.commit()
        return True
    return False
