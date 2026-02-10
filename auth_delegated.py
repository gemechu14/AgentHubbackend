import os
import json
import requests
import msal
from dotenv import load_dotenv

# -----------------------------
# Load env
# -----------------------------
load_dotenv()

TENANT_ID = os.environ["PBI_TENANT_ID"]
CLIENT_ID = os.environ["PBI_CLIENT_ID"]
GROUP_ID = os.environ["PBI_GROUP_ID"]
DATASET_ID = os.environ["PBI_DATASET_ID"]

# Delegated scopes (NO client secret)
SCOPES = [
    "https://analysis.windows.net/powerbi/api/Dataset.Read.All",
]

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
CACHE_FILE = ".msal_token_cache.json"
APP_SCOPES = ["https://analysis.windows.net/powerbi/api/.default"]


def load_cache() -> msal.SerializableTokenCache:
    cache = msal.SerializableTokenCache()
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache.deserialize(f.read())
    return cache


def save_cache(cache: msal.SerializableTokenCache) -> None:
    if cache.has_state_changed:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(cache.serialize())


def get_delegated_token() -> str:
    """
    Delegated device-code flow only.
    Requires your Entra app to allow public client flows:
    App Registration -> Authentication -> Allow public client flows = Yes
    """

    cache = load_cache()

    # If a client secret is provided, use confidential client (app flow)
    client_secret = os.environ.get("PBI_CLIENT_SECRET")
    if client_secret:
        app = msal.ConfidentialClientApplication(
            client_id=CLIENT_ID,
            client_credential=client_secret,
            authority=AUTHORITY,
            token_cache=cache,
        )

        result = app.acquire_token_silent(APP_SCOPES, account=None)
        if not result:
            result = app.acquire_token_for_client(scopes=APP_SCOPES)

        if not result or "access_token" not in result:
            raise RuntimeError("Failed to obtain app token:\n" + json.dumps(result or {}, indent=2))

        save_cache(cache)
        return result["access_token"]

    # Otherwise use public client device-code flow
    # app = msal.PublicClientApplication(
    #     client_id=CLIENT_ID,
    #     authority=AUTHORITY,
    #     token_cache=cache,
    # )

    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            save_cache(cache)
            return result["access_token"]

    flow = app.initiate_device_flow(scopes=SCOPES)
    if "message" not in flow:
        raise RuntimeError(f"Could not initiate device flow. Details: {flow}")

    print("\n=== Microsoft Login Required ===")
    print(flow["message"])  # contains URL + code
    print("================================\n")

    result = app.acquire_token_by_device_flow(flow)

    if "access_token" not in result:
        raise RuntimeError("Failed to obtain token:\n" + json.dumps(result, indent=2))

    save_cache(cache)
    return result["access_token"]


def execute_queries(token: str, dax: str) -> requests.Response:
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{GROUP_ID}/datasets/{DATASET_ID}/executeQueries"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"queries": [{"query": dax}], "serializerSettings": {"includeNulls": True}}
    return requests.post(url, headers=headers, json=payload, timeout=60)


def main():
    print("Testing delegated auth (NO secret) + executeQueries...\n")
    print("Tenant:", TENANT_ID)
    print("Client:", CLIENT_ID)
    print("Workspace:", GROUP_ID)
    print("Dataset:", DATASET_ID)

    token = get_delegated_token()
    print("\n✅ Got delegated access token.")

    dax = """
EVALUATE
TOPN(
  20,
  SUMMARIZECOLUMNS(
    '_Location'[Club_ID],
    "NewAccountRows", COUNTROWS('_Daily New Account')
  ),
  [NewAccountRows], DESC
)
"""


    print("\n--- Executing DAX ---")
    print(dax)
    print("--- End DAX ---\n")

    resp = execute_queries(token, dax)
    print("HTTP Status:", resp.status_code)
    print("Response Headers Content-Type:", resp.headers.get("Content-Type"))

    try:
        print(json.dumps(resp.json(), indent=2))
    except Exception:
        print(resp.text)


if __name__ == "__main__":
    main()
