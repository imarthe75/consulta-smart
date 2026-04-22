import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from typing import Optional, List
from app.core.config import settings
from app.core.logger import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

class KeycloakUser(dict):
    def __init__(self, sub: str, email: str, username: str, roles: List[str]):
        super().__init__(
            id=sub,
            sub=sub,
            email=email,
            username=username,
            roles=roles
        )
        self.id = sub
        self.email = email
        self.username = username
        self.roles = roles

async def get_current_user(token: str = Depends(oauth2_scheme)) -> KeycloakUser:
    """
    Validate Keycloak JWT token.
    """
    try:
        # 1. Fetch JWKS from Keycloak (cached in production)
        # For simplicity in this demo, we validate using the server URL and realm
        # In a real production environment, we should fetch the public key from:
        # {settings.KEYCLOAK_SERVER_URL}realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/certs
        
        # For now, we will decode with options to skip full cert verification 
        # unless we want to implement the JWKS fetching logic right here.
        
        # Let's do it properly: fetch JWKS.
        jwks_url = f"{settings.KEYCLOAK_SERVER_URL}realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/certs"
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_url)
            jwks = response.json()
        
        # Decode token
        # Note: In a real app, use the kid from header to find the right key
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience="account", # Default Keycloak audience for user info
            options={"verify_aud": False} # Relaxing for the demo
        )
        
        sub: str = payload.get("sub")
        email: str = payload.get("email")
        username: str = payload.get("preferred_username")
        roles: List[str] = payload.get("realm_access", {}).get("roles", [])
        
        if sub is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return KeycloakUser(sub=sub, email=email, username=username, roles=roles)
        
    except (JWTError, Exception) as e:
        logger.error(f"JWT Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
