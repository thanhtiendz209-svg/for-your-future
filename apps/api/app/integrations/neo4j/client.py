"""
Neo4j Graph Database Client and Connection Manager.
Handles synchronous and asynchronous Cypher execution with connection pooling and health checks.
"""

import os
import logging
from typing import Any, Dict, List, Optional
import asyncio
from neo4j import GraphDatabase, AsyncGraphDatabase, AsyncDriver, Driver
from neo4j.exceptions import ServiceUnavailable, AuthError
from app.core.config import settings

logger = logging.getLogger("foryourfuture.neo4j")

_sync_driver: Optional[Driver] = None
_async_driver: Optional[AsyncDriver] = None


def get_sync_driver() -> Optional[Driver]:
    """Khởi tạo hoặc tái sử dụng Synchronous Neo4j Driver"""
    global _sync_driver
    if _sync_driver is None:
        try:
            _sync_driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
            )
        except Exception as e:
            logger.warning(f"Neo4j sync driver initialization warning: {e}")
            return None
    return _sync_driver


def get_async_driver() -> Optional[AsyncDriver]:
    """Khởi tạo hoặc tái sử dụng Asynchronous Neo4j Driver"""
    global _async_driver
    if _async_driver is None:
        try:
            _async_driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
            )
        except Exception as e:
            logger.warning(f"Neo4j async driver initialization warning: {e}")
            return None
    return _async_driver


async def close_driver():
    """Đóng an toàn kết nối Neo4j khi ứng dụng shutdown"""
    global _async_driver, _sync_driver
    if _async_driver is not None:
        await _async_driver.close()
        _async_driver = None
    if _sync_driver is not None:
        _sync_driver.close()
        _sync_driver = None
    logger.info("Neo4j drivers closed.")


def execute_query_sync(query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Thực thi câu lệnh Cypher đồng bộ trên Neo4j"""
    driver = get_sync_driver()
    if driver is None:
        raise ConnectionError("Neo4j driver is not available.")
    with driver.session(database=settings.NEO4J_DATABASE) as session:
        result = session.run(query, parameters or {})
        return [record.data() for record in result]


async def execute_query_async(query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Thực thi câu lệnh Cypher bất đồng bộ (chạy trên threadpool để an toàn với event loop)"""
    return await asyncio.to_thread(execute_query_sync, query, parameters)


async def check_health() -> Dict[str, Any]:
    """Kiểm tra trạng thái kết nối tới Neo4j Graph Database"""
    try:
        def _ping():
            driver = get_sync_driver()
            if not driver:
                return 0
            with driver.session(database=settings.NEO4J_DATABASE) as session:
                record = session.run("RETURN 1 AS status").single()
                return record["status"] if record else 0

        status_val = await asyncio.to_thread(_ping)
        if status_val == 1:
            return {"status": "healthy", "database": "neo4j", "uri": settings.NEO4J_URI}
        return {"status": "unhealthy", "error": "Unexpected ping response"}
    except (ServiceUnavailable, AuthError, Exception) as e:
        logger.warning(f"Neo4j health check: {e}")
        return {"status": "unhealthy", "error": str(e), "uri": settings.NEO4J_URI}

