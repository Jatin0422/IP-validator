from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from .core import classify_ipv4, subnet_info, validate_ipv4, validate_ipv6
except ImportError:  # supports `uvicorn main:app` from backend/
    from core import classify_ipv4, subnet_info, validate_ipv4, validate_ipv6

app = FastAPI(title="IPLens")
app.add_middleware(
    CORSMiddleware, allow_origins=["http://localhost:5173"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)


class AddressRequest(BaseModel):
    ip: str


class SubnetRequest(BaseModel):
    ip: str
    mask: str


@app.post("/api/validate")
def validate(request: AddressRequest):
    if ":" in request.ip:
        result = validate_ipv6(request.ip)
        version = 6
    else:
        result = validate_ipv4(request.ip)
        version = 4
    response = {"ip": request.ip, "version": version, **result}
    if result["valid"] and version == 4:
        response["classification"] = classify_ipv4(request.ip)
    return response


@app.post("/api/subnet")
def subnet(request: SubnetRequest):
    try:
        return subnet_info(request.ip, request.mask)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
