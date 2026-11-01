from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
try:
    from .core import (address_formats, classify_ipv4, classify_ipv6, ip_range,
                       same_network, split_subnet, subnet_info,
                       validate_ipv4, validate_ipv6)
except ImportError:  # supports `uvicorn main:app` from backend/
    from core import (address_formats, classify_ipv4, classify_ipv6, ip_range,
                      same_network, split_subnet, subnet_info,
                      validate_ipv4, validate_ipv6)

app = FastAPI(title="IPLens")
app.add_middleware(
    CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)


class AddressRequest(BaseModel):
    ip: str


class SubnetRequest(BaseModel):
    ip: str
    mask: str


class SameNetworkRequest(BaseModel):
    ip1: str
    ip2: str
    mask: str


class SplitRequest(BaseModel):
    network: str
    n: int


class RangeRequest(BaseModel):
    start: str
    end: str


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
        response.update(address_formats(request.ip))
    elif result["valid"]:
        response["classification"] = classify_ipv6(request.ip)
        response.update(address_formats(request.ip))
    return response


@app.post("/api/subnet")
def subnet(request: SubnetRequest):
    try:
        return subnet_info(request.ip, request.mask)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/same-network")
def check_same_network(request: SameNetworkRequest):
    try:
        return {"same_network": same_network(request.ip1, request.ip2, request.mask)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/split-subnet")
def split(request: SplitRequest):
    try:
        return {"subnets": split_subnet(request.network, request.n)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/ip-range")
def range_addresses(request: RangeRequest):
    try:
        return {"addresses": ip_range(request.start, request.end)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
