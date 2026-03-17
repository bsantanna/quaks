from pydantic import BaseModel


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str


class LoginRequest(BaseModel):
    username: str
    password: str


class RenewRequest(BaseModel):
    refresh_token: str


class ExchangeRequest(BaseModel):
    code: str
    code_verifier: str
    redirect_uri: str
