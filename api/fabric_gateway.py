import os
import json

PEER_ENDPOINT = os.getenv("FABRIC_PEER_ENDPOINT", "localhost:7051")

CRYPTO_PATH = os.getenv(
    "FABRIC_CRYPTO_PATH",
    os.path.join(os.path.dirname(__file__), "..", "network", "crypto-config",
                 "peerOrganizations", "developer.veridium.com")
)
CERT_PATH = os.path.join(CRYPTO_PATH, "users", "Admin@developer.veridium.com",
                         "msp", "signcerts", "cert.pem")
KEY_PATH = os.path.join(CRYPTO_PATH, "users", "Admin@developer.veridium.com",
                        "msp", "keystore")
TLS_CERT_PATH = os.path.join(CRYPTO_PATH, "peers",
                             "peer0.developer.veridium.com", "tls", "ca.crt")

MSP_ID = "DeveloperOrgMSP"
CHANNEL_NAME = "veridium-channel"
CHAINCODE_NAME = "carbon_credit"


class FabricGateway:

    def __init__(self):
        """Set up the gRPC connection with TLS and load the client identity."""
        self.channel_name = CHANNEL_NAME
        self.chaincode_name = CHAINCODE_NAME

    def submit_transaction(self, function_name: str, *args: str) -> str:
        """
        Submit a transaction that changes state (mint, transfer, retire).

        Goes through the full endorse -> order -> commit flow.
        Returns the result payload as a JSON string.
        Raises if endorsement fails or the orderer rejects it.
        """

    def evaluate_transaction(self, function_name: str, *args: str) -> str:
        """
        Run a read-only query against the chaincode.

        Hits a single peer, no transaction gets created.
        Used for QueryCredit, QueryOwnership, GetCreditHistory.
        """

    def close(self):

    def evaluate_transaction(self, function_name: str, *args: str) -> str: