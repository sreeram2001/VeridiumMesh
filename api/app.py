"""
Request flow for minting a credit:
  1. Validate input (Pydantic models)
  2. Auto-compute risk features (R_ratio, Vintage_Age, M_flag, T_flag)
  3. Run Isolation Forest model → get AI risk score
  4. Submit MintCredit transaction to Fabric (endorsed by both orgs)
  5. Return credit ID, risk score, and block metadata

"""

import uuid
import time
import json
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from api.fabric_gateway import FabricGateway

app = FastAPI(
    title="VeridiumMesh API",
    version="1.0.0",
    description="AI-powered carbon credit fraud detection on Hyperledger Fabric.",
)
gateway = FabricGateway()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MintRequest(BaseModel):
    """Request body for issuing (minting) a new carbon credit."""
    project_id: str
    project_type: str
    tonnes: int
    vintage_year: int
    owner_id: str
    developer_id: Optional[str] = None
    regulator_id: Optional[str] = None
    r_ratio: Optional[float] = None
    m_flag: Optional[int] = None
    t_flag: Optional[int] = None

class TransferRequest(BaseModel):
    """Request body for transferring credit ownership units."""

class RetireRequest(BaseModel):
    """Request body for retiring (burning) a carbon credit."""
    credit_id: str
    owner_id: str

_HIGH_RISK_TYPES = {
    "Renewable Energy", "Hydro", "Hydropower", "Wind", "Biomass",
    "Fossil fuel replacement", "Solar", "Landfill Gas", "REDD+",
}
_PEER_AVERAGE_TONNES = 50_000


def auto_compute_features(project_type: str, tonnes: int) -> tuple[float, int, int]:
    """
    Compute ML input features from raw project data.
    Returns:
        r_ratio: Issuance volume relative to peer average
        m_flag:  1 if project type is historically high-risk
        t_flag:  1 if issuance volume spikes (r_ratio > 3.0)
    """

@app.post("/credits/issue", status_code=201)
def issue_credit(req: MintRequest):
    """
    Issue a new carbon credit:
      1. Auto-compute risk features
      2. Run AI scoring model
      3. Submit MintCredit to Fabric (requires dual-org endorsement)
    """


@app.post("/credits/transfer")
def transfer_credit(req: TransferRequest):
    """Transfer ownership units between participants via Fabric."""
    
@app.post("/credits/retire")
def retire_credit(req: RetireRequest):
    """Permanently retire a carbon credit via Fabric."""
    
@app.get("/credits/{credit_id}")
def get_credit(credit_id: str):
    """Query credit metadata and ownership from Fabric world state."""
    
@app.get("/credits/{credit_id}/history")
def get_credit_history(credit_id: str):
    """Retrieve full audit trail from Fabric's key history."""

@app.get("/chain/stats")
def get_chain_stats():
    """Return live statistics from the Fabric network."""
    
@app.get("/chain/validate")
def validate_chain():
    """Check Fabric network health and peer connectivity."""
    
@app.get("/chain")
def get_chain():
    """Return a summary of blocks from the Fabric ledger."""