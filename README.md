# IPLens

IPLens provides hand-written IPv4/IPv6 validation, classification, and subnet utilities through a FastAPI backend and a small React interface.

## Tabs

- **Validate:** checks IPv4 or IPv6, shows its class/category, and displays binary, hexadecimal, and integer forms.
- **Subnet Calculator:** calculates network, broadcast, host range, mask, wildcard, and address counts from a prefix or mask.
- **Same Network:** checks whether two IPv4 addresses share a subnet.
- **Split Subnet:** divides a CIDR network into a power-of-two number of subnets (up to 1024).
- **IP Range:** lists the inclusive IPv4 range, capped at 1024 addresses.

## Run

In PowerShell from the project root, create and install the backend environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Start the backend from the project root:

```powershell
python -m uvicorn backend.main:app --reload
```

In a second terminal, start the frontend:

```powershell
cd frontend
npm install
npm run dev
```

Run backend tests from the project root:

```powershell
python -m pytest backend\test_core.py -q
```

## API endpoints

All endpoints accept JSON via `POST`:

- `/api/validate` â€” `{ "ip": "..." }`
- `/api/subnet` â€” `{ "ip": "...", "mask": "/24" }`
- `/api/same-network` â€” `{ "ip1": "...", "ip2": "...", "mask": "/24" }`
- `/api/split-subnet` â€” `{ "network": "192.168.1.0/24", "n": 4 }`
- `/api/ip-range` â€” `{ "start": "192.168.1.1", "end": "192.168.1.10" }`
