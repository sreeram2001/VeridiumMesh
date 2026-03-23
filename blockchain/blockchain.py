from .block import Block
from .types import MINT_CREDIT, TRANSFER_CREDIT, RETIRE_CREDIT


class Blockchain:
    def __init__(self, difficulty: int = 2):
        self.difficulty           = difficulty
        self.chain                = []
        self.pending_transactions = []
        self.credits              = {}   # credit_id -> credit details dict
        self.ownership            = {}   # (credit_id, owner_id) -> units held
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis = Block(index=0, transactions=[], previous_hash="0")
        genesis.mine_block(self.difficulty)
        self.chain.append(genesis)

    def get_latest_block(self) -> Block:
        return self.chain[-1]

    def add_transaction(self, tx: dict):
        self.pending_transactions.append(tx)

    def apply_transaction(self, tx: dict):
        tx_type = tx["type"]

        if tx_type == MINT_CREDIT:
            credit_id    = tx["credit_id"]
            owner_id     = tx["owner_id"]
            tonnes       = tx["tonnes"]
            self.credits[credit_id] = {
                "tonnes":        tonnes,
                "project_type":  tx["project_type"],
                "vintage_year":  tx["vintage_year"],
                "ai_risk_score": tx["ai_risk_score"],
                "status":        "active",
            }
            self.ownership[(credit_id, owner_id)] = tonnes

        elif tx_type == TRANSFER_CREDIT:
            credit_id  = tx["credit_id"]
            from_owner = tx["from_owner"]
            to_owner   = tx["to_owner"]
            units      = tx["units"]
            if self.credits[credit_id]["status"] != "active":
                raise ValueError(f"Credit {credit_id} is already retired.")
            if self.ownership.get((credit_id, from_owner), 0) < units:
                raise ValueError(f"Insufficient units: {from_owner} does not hold {units} of {credit_id}.")
            self.ownership[(credit_id, from_owner)] -= units
            self.ownership[(credit_id, to_owner)]    = self.ownership.get((credit_id, to_owner), 0) + units

        elif tx_type == RETIRE_CREDIT:
            credit_id = tx["credit_id"]
            owner_id  = tx["owner_id"]
            if self.ownership.get((credit_id, owner_id), 0) <= 0:
                raise ValueError(f"No units to retire: {owner_id} holds 0 of {credit_id}.")
            self.credits[credit_id]["status"] = "retired"

    def mine_pending_transactions(self):
        if not self.pending_transactions:
            return None
        new_block = Block(
            index=len(self.chain),
            transactions=self.pending_transactions.copy(),
            previous_hash=self.get_latest_block().hash,
        )
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)
        for tx in new_block.transactions:
            self.apply_transaction(tx)
        self.pending_transactions = []
        return new_block

    def is_chain_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            current  = self.chain[i]
            previous = self.chain[i - 1]
            if current.hash != current.calculate_hash():
                return False
            if current.previous_hash != previous.hash:
                return False
        return True


if __name__ == "__main__":
    from blockchain.types import MINT_CREDIT, TRANSFER_CREDIT, RETIRE_CREDIT

    print("Initializing VeridiumAI Blockchain...")
    bc = Blockchain(difficulty=2)

    # 1. Mint a credit
    print("\nMinting a new carbon credit...")
    bc.add_transaction({
        "type":          MINT_CREDIT,
        "credit_id":     "CRED-001",
        "tonnes":        1000,
        "project_type":  "Cookstoves",
        "vintage_year":  2024,
        "ai_risk_score": 0.95,   # highly suspicious!
        "owner_id":      "Developer-Org",
    })
    bc.mine_pending_transactions()
    print("Credits State:", bc.credits)
    print("Ownership State:", dict(bc.ownership))

    # 2. Transfer 400 tonnes to Buyer-A
    print("\nTransferring 400 tonnes to Buyer-A...")
    bc.add_transaction({
        "type":       TRANSFER_CREDIT,
        "credit_id":  "CRED-001",
        "from_owner": "Developer-Org",
        "to_owner":   "Buyer-A",
        "units":      400,
    })
    bc.mine_pending_transactions()
    print("Ownership State:", dict(bc.ownership))

    # 3. Buyer-A retires the credit
    print("\nBuyer-A retires the credit...")
    bc.add_transaction({
        "type":      RETIRE_CREDIT,
        "credit_id": "CRED-001",
        "owner_id":  "Buyer-A",
    })
    bc.mine_pending_transactions()
    print("Credit Status:", bc.credits["CRED-001"]["status"])
    print(f"\nIs chain valid? {bc.is_chain_valid()}")
