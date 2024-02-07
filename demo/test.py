# import requests
# from fastapi import FastAPI

# app = FastAPI()

# # OAuth2 provider details (replace with your actual values)
# oauth2_token_url = "https://your-oauth-provider.com/token"
# client_id = "your-client-id"
# client_secret = "your-client-secret"
# scope = "your-scope"  # Optional: Specify the scopes you need

# # FastAPI route to obtain an access token using client credentials
# @app.get("/get_access_token")
# async def get_access_token():
#     headers = {
#         "Content-Type": "application/x-www-form-urlencoded",
#     }
#     data = {
#         "grant_type": "client_credentials",
#         "client_id": client_id,
#         "client_secret": client_secret,
#         "scope": scope,
#     }

#     response = requests.post(oauth2_token_url, headers=headers, data=data)
#     response_data = response.json()

#     if "access_token" in response_data:
#         access_token = response_data["access_token"]
#         return {"access_token": access_token}
#     else:
#         return {"error": "Unable to obtain access token"}

# # Example usage: Run FastAPI app and make a request to the /get_access_token endpoint


from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.security import OAuth2AuthorizationCodeBearer

app = FastAPI()

# Replace these with your actual OAuth2 provider details
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://your-oauth-provider.com/authorize",
    tokenUrl="https://your-oauth-provider.com/token",
    clientId="your-client-id",
    clientSecret="your-client-secret",
    scopes=["read", "write"],
    redirectUri="http://your-fastapi-app.com/login/callback",
)

# Mock user database
fake_users_db = {
    "mock_user": {
        "username": "mock_user",
        "password": "mock_password",
        "scopes": ["read", "write"],
    }
}

# FastAPI route to initiate the Authorization Code Grant flow
@app.get("/login")
async def login(request: Request, authorize: bool = Query(False)):
    if not authorize:
        return {"message": "Visit /login?authorize=True to initiate the OAuth2 Authorization Code flow"}

    # Redirect the user to the OAuth2 provider's authorization endpoint
    authorization_url = oauth2_scheme.get_authorization_url()
    return RedirectResponse(url=authorization_url)

# FastAPI route to handle the callback from the OAuth2 provider
@app.get("/login/callback")
async def login_callback(
    code: str = None,
    error: str = None,
    state: str = None,
    token: OAuth2AuthorizationCodeBearer = Depends(oauth2_scheme)
):
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

    # Exchange the authorization code for an access token
    token_data = token.__dict__
    
    # Validate the obtained token, you may want to store it securely or use it for further operations
    # For simplicity, we just print the token data here
    print("Access Token Data:", token_data)

    # Return a response with the access token
    return {"access_token": token_data["credentials"]["access_token"], "token_type": "bearer"}

# Example usage: Run FastAPI app and visit /login?authorize=True to initiate the OAuth2 flow
