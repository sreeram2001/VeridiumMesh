# VeridiumMesh

## Introduction

VeridiumMesh is a carbon credit integrity platform that catches fraudulent credits before they ever make it onto the blockchain. It pairs a machine learning model (Isolation Forest) with a Hyperledger Fabric network so that every credit gets a risk score, and that score lives permanently on an immutable ledger.

The idea is simple: carbon credit markets have a fraud problem — inflated volumes, double-counting, fake project types. We tackle that by making sure no credit gets minted unless it passes through an AI screening step *and* gets signed off by two separate organizations (a project developer and a government regulator).

## How it works

Here's the flow when someone wants to issue a new carbon credit:
1. A user fills out the project details in the frontend (project type, tonnes, vintage year, etc.)
2. The FastAPI backend auto-computes risk features from the raw data
3. The Isolation Forest model scores the project — anything above 0.8 gets flagged as high risk
4. The backend submits a `MintCredit` transaction to the Fabric network
5. Both the DeveloperOrg peer and the RegulatorOrg peer must endorse the transaction (this is Fabric's endorsement policy doing the work, not custom code)
6. The orderer packages it into a block, both peers commit it
7. The credit now lives on the ledger with its AI risk score baked in permanently
After that, credits can be transferred between owners or permanently retired (burned). The chaincode enforces all the rules — you can't transfer a retired credit, you can't spend more units than you hold, and you can't retire something you don't own.

## Project structure

```
VeridiumMesh/
├── api/                          # Python backend (FastAPI)
│   ├── app.py                    # REST endpoints — talks to Fabric through the gateway
│   └── fabric_gateway.py         # gRPC client that connects to Fabric peers
├── chaincode/                    # The smart contract (this is the core)
│   └── carbon_credit/
│       ├── carbon_credit.go      # Go chaincode — Mint, Transfer, Retire, Query, History
│       └── go.mod                # Go module with Fabric SDK dependency
├── network/                      # Everything needed to run the Fabric network
│   ├── docker-compose.yaml       # Containers: orderer, 2 peers, 2 CouchDB instances
│   ├── configtx.yaml             # Channel config, org definitions, endorsement policy
│   ├── crypto-config.yaml        # Certificate generation config (cryptogen)
│   └── scripts/
│       ├── start_network.sh      # Spin up the network, create channel, join peers
│       └── deploy_chaincode.sh   # Package, install, approve, commit the chaincode
├── ml/                           # Machine learning layer
│   ├── model.py                  # score_project() — runs the trained Isolation Forest
│   └── train_isoforest.py        # Training script (re-train if you update the dataset)
├── data/                         # Datasets, EDA plots, feature CSVs
├── notebooks/                    # Jupyter notebooks for exploration
├── scripts/                      # Utility scripts (feature engineering, EDA)
├── frontend/                     # Next.js web app (developer console + explorer)
└── requirements.txt              # Python dependencies
```

## The Fabric network

We run a two-org network:
| Organization | MSP ID | What they do |
|---|---|---|
| DeveloperOrg | `DeveloperOrgMSP` | Project developers who submit credit issuance requests |
| RegulatorOrg | `RegulatorOrgMSP` | Government regulators who approve or reject credits |
| OrdererOrg | `OrdererOrgMSP` | Runs the Raft ordering service (handles block creation) |
The endorsement policy is:

```
AND('DeveloperOrgMSP.peer', 'RegulatorOrgMSP.peer')
```

In plain English: both a developer peer and a regulator peer have to sign off on a mint transaction before it gets committed.

Both orgs share a single channel called `veridium-channel`.

## The smart contract (chaincode)

The chaincode lives at `chaincode/carbon_credit/carbon_credit.go`. It's written in Go using the `fabric-contract-api-go` SDK. Here's what each function does:

| Function | What it does |
|---|---|
| `MintCredit` | Creates a new carbon credit on the ledger. Stores the AI risk score, project metadata, and assigns all tonnes to the issuing owner. Won't let you mint a duplicate. |
| `TransferCredit` | Moves units from one owner to another. Blocks transfers on retired credits and rejects if the sender doesn't have enough units (no double-spending). |
| `RetireCredit` | Permanently burns a credit by setting its status to "retired." Can't be undone. You have to actually hold units to retire it. |
| `QueryCredit` | Looks up a credit's metadata (tonnes, project type, vintage year, risk score, status). |
| `QueryOwnership` | Returns how many units a specific owner holds for a given credit. |
| `GetCreditHistory` | Pulls the full modification history for a credit using Fabric's built-in `GetHistoryForKey` — every state change with its transaction ID and timestamp. |

The world state stores two types of records in CouchDB:

| Key pattern | What's stored |
|---|---|
| `credit:<credit_id>` | `{tonnes, project_type, vintage_year, ai_risk_score, status}` |
| `ownership:<credit_id>:<owner_id>` | `{units}` |

## AI scoring

The ML layer uses an Isolation Forest trained on the Berkeley Voluntary Registry Offsets Database (~5,700 real carbon credit projects).

Before any credit hits the blockchain, the API computes four features from the raw project data:

- **R_ratio** — how big is this issuance compared to the average for its project type?
- **Vintage_Age** — how old is the project? (current year minus vintage year)
- **M_flag** — is this project type one that's historically associated with fraud? (Solar, REDD+, Hydro, etc.)
- **T_flag** — is the issuance volume spiking way above normal? (R_ratio > 3.0)

The model returns a score between 0 and 1. Anything at or above 0.8 gets flagged as high risk on the ledger.

## API endpoints

| Method | Endpoint | What it does |
|---|---|---|
| POST | `/credits/issue` | Computes features, runs AI scoring, submits MintCredit to Fabric |
| POST | `/credits/transfer` | Submits a TransferCredit transaction |
| POST | `/credits/retire` | Submits a RetireCredit transaction |
| GET | `/credits/{credit_id}` | Returns credit metadata and current ownership from world state |
| GET | `/credits/{credit_id}/history` | Returns the full audit trail from Fabric's key history |
| GET | `/chain/stats` | Returns live stats (total credits, active, retired, flagged, etc.) |
| GET | `/chain/validate` | Health check — verifies the gateway can reach the Fabric network |
| GET | `/chain` | Returns a summary of blocks on the ledger |

## Getting started

### Prerequisites

- Docker and Docker Compose
- Go 1.21+
- Python 3.11+
- Node.js 18+
- Hyperledger Fabric binaries on your PATH (`peer`, `orderer`, `cryptogen`, `configtxgen`)

### 1. Start the Fabric network and deploy chaincode

```bash
cd network
./scripts/start_network.sh
./scripts/deploy_chaincode.sh
```

This generates crypto material, spins up Docker containers (orderer, peers, CouchDB), creates the channel, joins both peers, and deploys the chaincode.

### 2. Start the backend

```bash
pip install -r requirements.txt
PYTHONPATH=. python -m uvicorn api.app:app --reload --port 8000
```

API docs at `http://localhost:8000/docs`.

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Opens at `http://localhost:3000`.

### Tear down

```bash
cd network
docker-compose down -v
rm -rf crypto-config channel-artifacts
```

### Environment variables

| Variable | Default | What it controls |
|---|---|---|
| `FABRIC_PEER_ENDPOINT` | `localhost:7051` | gRPC endpoint for the Fabric peer |
| `FABRIC_CRYPTO_PATH` | `network/crypto-config/peerOrganizations/developer.veridium.com` | Path to MSP crypto material |

### Production considerations

- **TLS** — local setup uses self-signed certs from cryptogen. In production, use Fabric CA for proper certificates.
- **Multiple orderers** — we run a single Raft node locally. Production should have 3 or 5 across different hosts.
- **Separate hosts** — each org's peer, CouchDB, and CA should run on its own infrastructure.
- **CouchDB credentials** — rotate the default admin/adminpw and store securely.
- **Persistent storage** — map Docker volumes to real disk paths so ledger data survives restarts.
- **API authentication** — add JWT or API key middleware before exposing the backend.
- **Model retraining** — re-run `ml/train_isoforest.py` after updating the dataset. The API picks up new artifacts on restart.
- **Monitoring** — add Prometheus metrics and use Fabric's built-in operations endpoints for peer/orderer health.

## Usage

Once the network and backend are running, you can interact with the API directly or through the frontend.

### Issue a new carbon credit

```bash
curl -X POST http://localhost:8000/credits/issue \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "PROJ-001",
    "project_type": "Solar",
    "tonnes": 5000,
    "vintage_year": 2023,
    "owner_id": "developer-org-1"
  }'
```

The backend auto-computes the risk features (R_ratio, M_flag, T_flag), runs the Isolation Forest model, and submits a `MintCredit` transaction to Fabric. The response includes the credit ID and the AI risk score.

### Transfer ownership

```bash
curl -X POST http://localhost:8000/credits/transfer \
  -H "Content-Type: application/json" \
  -d '{
    "credit_id": "PROJ-001",
    "from_owner": "developer-org-1",
    "to_owner": "buyer-org-2",
    "units": 2000
  }'
```

### Retire a credit

```bash
curl -X POST http://localhost:8000/credits/retire \
  -H "Content-Type: application/json" \
  -d '{
    "credit_id": "PROJ-001",
    "owner_id": "developer-org-1"
  }'
```

Once retired, the credit is permanently burned. No more transfers allowed.

### Query a credit

```bash
curl http://localhost:8000/credits/PROJ-001
```

Returns the credit metadata (tonnes, project type, vintage year, risk score, status) and current ownership breakdown.

### View audit history

```bash
curl http://localhost:8000/credits/PROJ-001/history
```

Returns every state change for that credit — each with a transaction ID and timestamp from the Fabric ledger.

### Check network health

```bash
curl http://localhost:8000/chain/validate
```

## Team Members

| # | Name | 
|---|---|
| 1 | Harpreet Kaur Brar |
| 2 | Sreeram Saravana Prasad |
| 3 | Asmi Umesh Pulgam |
| 4 | Brijesh Kumar | 
| 5 | Vandhana Vemuri |