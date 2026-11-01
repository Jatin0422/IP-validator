# IPLens

IPLens provides hand-written IPv4/IPv6 validation, classification, and subnet utilities through a FastAPI backend and a small React interface.

## Tabs

- **Validate:** address validation, class/category, and binary, hexadecimal, and integer forms.
- **Subnet:** mask, network, broadcast, host range, role, bit visualizer, and optional same-network comparison and subnet split.

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

- `/api/validate` - `{ "ip": "..." }`
- `/api/subnet` - `{ "ip": "...", "mask": "/24" }`
- `/api/same-network` - `{ "ip1": "...", "ip2": "...", "mask": "/24" }`
- `/api/split-subnet` - `{ "network": "192.168.1.0/24", "n": 4 }`
- `/api/ip-range` - API only: `{ "start": "192.168.1.1", "end": "192.168.1.10" }`
