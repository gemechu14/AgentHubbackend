"""
Power BI service module for authentication and DAX execution.
Uses the same authentication logic as final.py
"""
import os
import json
import requests
import msal
from typing import Dict, Any, Optional
from pathlib import Path

# Scopes for Power BI API
SCOPES = ["https://analysis.windows.net/powerbi/api/Dataset.Read.All"]
APP_SCOPES = ["https://analysis.windows.net/powerbi/api/.default"]


def load_cache(cache_file: str) -> msal.SerializableTokenCache:
    """Load MSAL token cache from file."""
    cache = msal.SerializableTokenCache()
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            cache.deserialize(f.read())
    return cache


def save_cache(cache: msal.SerializableTokenCache, cache_file: str) -> None:
    """Save MSAL token cache to file."""
    if cache.has_state_changed:
        # Ensure directory exists
        Path(cache_file).parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(cache.serialize())


def get_powerbi_token(
    tenant_id: str,
    client_id: str,
    client_secret: Optional[str] = None,
    cache_file: Optional[str] = None,
) -> str:
    """
    Get Power BI access token using the same logic as final.py.
    
    Args:
        tenant_id: Azure AD tenant ID
        client_id: Azure AD client/application ID
        client_secret: Optional client secret for app-only auth
        cache_file: Optional path to token cache file
        
    Returns:
        Access token string
        
    Raises:
        RuntimeError: If token acquisition fails
    """
    if cache_file is None:
        cache_file = ".msal_token_cache.json"
    
    cache = load_cache(cache_file)
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    
    # App-only authentication (if client_secret is provided)
    if client_secret:
        app = msal.ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=authority,
            token_cache=cache,
        )
        
        result = app.acquire_token_silent(APP_SCOPES, account=None)
        if not result:
            result = app.acquire_token_for_client(scopes=APP_SCOPES)
        
        if not result or "access_token" not in result:
            raise RuntimeError("Failed to obtain app token:\n" + json.dumps(result or {}, indent=2))
        
        save_cache(cache, cache_file)
        return result["access_token"]
    
    # Delegated authentication (device code flow)
    app = msal.PublicClientApplication(
        client_id=client_id,
        authority=authority,
        token_cache=cache,
    )
    
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            save_cache(cache, cache_file)
            return result["access_token"]
    
    # Device code flow (for interactive scenarios)
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "message" not in flow:
        raise RuntimeError(f"Could not initiate device flow. Details: {flow}")
    
    # Note: In API context, device flow is not ideal. Consider requiring client_secret.
    raise RuntimeError(
        "Device code flow initiated. This requires interactive authentication. "
        "Please provide client_secret for app-only authentication."
    )


def execute_dax(
    token: str,
    workspace_id: str,
    dataset_id: str,
    dax_query: str,
    timeout: int = 60,
) -> Dict[str, Any]:
    """
    Execute a DAX query against Power BI dataset.
    
    Args:
        token: Power BI access token
        workspace_id: Power BI workspace/group ID
        dataset_id: Power BI dataset ID
        dax_query: DAX query string (should start with EVALUATE)
        timeout: Request timeout in seconds
        
    Returns:
        Response JSON from executeQueries API
        
    Raises:
        RuntimeError: If query execution fails
    """
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/executeQueries"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "queries": [{"query": dax_query}],
        "serializerSettings": {"includeNulls": True},
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    
    try:
        data = response.json()
    except Exception:
        data = {"raw": response.text}
    
    if response.status_code >= 400:
        raise RuntimeError(
            f"executeQueries failed ({response.status_code}):\n{json.dumps(data, indent=2)}"
        )
    
    return data


def get_schema_dax(workspace_id: str, dataset_id: str) -> Dict[str, str]:
    """
    Get DAX queries for schema information.
    
    Returns:
        Dictionary with keys: tables, columns, relationships, measures
    """
    return {
        "tables": "EVALUATE INFO.VIEW.TABLES()",
        "columns": "EVALUATE INFO.VIEW.COLUMNS()",
        "relationships": "EVALUATE INFO.VIEW.RELATIONSHIPS()",
        "measures": "EVALUATE INFO.VIEW.MEASURES()",
    }


def check_connection(
    tenant_id: str,
    client_id: str,
    workspace_id: str,
    dataset_id: str,
    client_secret: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Check Power BI connection by attempting to get a token and execute a simple query.
    
    Args:
        tenant_id: Azure AD tenant ID
        client_id: Azure AD client ID
        workspace_id: Power BI workspace ID
        dataset_id: Power BI dataset ID
        client_secret: Optional client secret for app-only auth
        
    Returns:
        Dictionary with connection status and details
        
    Raises:
        RuntimeError: If connection check fails
    """
    try:
        # Get token
        token = get_powerbi_token(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
        )
        
        # Execute a simple schema query to verify connection
        dax = "EVALUATE INFO.VIEW.TABLES()"
        result = execute_dax(
            token=token,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            dax_query=dax,
        )
        
        # Extract table count from result
        tables = result.get("results", [{}])[0].get("tables", [{}])[0].get("rows", [])
        table_count = len(tables)
        
        return {
            "connected": True,
            "message": "Successfully connected to Power BI",
            "workspace_id": workspace_id,
            "dataset_id": dataset_id,
            "table_count": table_count,
        }
    except Exception as e:
        return {
            "connected": False,
            "message": f"Connection failed: {str(e)}",
            "error": str(e),
        }

