/*
 * Carbon credit lifecycle chaincode for the VeridiumMesh Fabric network.
 *
 * It handles everything from issuing new
 * credits to transferring ownership and permanently retiring them. Every
 * credit gets an AI risk score baked in at mint time, and that score lives
 * on the ledger forever.
 *
 *   MintCredit      - Creates a new credit with metadata + risk score
 *   TransferCredit  - Moves units between owners (blocks retired credits)
 *   RetireCredit    - Burns a credit permanently, no going back
 *   QueryCredit     - Reads credit metadata from world state
 *   QueryOwnership  - Checks how many units someone holds
 *   GetCreditHistory - Pulls the full change log via Fabric's history API
 *
 * The endorsement policy requires both DeveloperOrg and RegulatorOrg to
 * sign off on mints. That's handled at the network level, not here.
 *
 * World state keys in CouchDB:
 *   "credit:<id>"               -> credit metadata (tonnes, type, score, etc.)
 *   "ownership:<id>:<owner>"    -> how many units that owner holds
 */

package main

import (
	"encoding/json"
	"fmt"
	"log"
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

type CarbonCreditContract struct {
	contractapi.Contract
}

type Credit struct {
	Tonnes       int     `json:"tonnes"`
	ProjectType  string  `json:"project_type"`
	VintageYear  int     `json:"vintage_year"`
	AIRiskScore  float64 `json:"ai_risk_score"`
	Status       string  `json:"status"`
}

// Ownership tracks how many units of a credit a participant holds.
type Ownership struct {
	Units int `json:"units"`
}

// MintCredit creates a new carbon credit on the ledger.
func (c *CarbonCreditContract) MintCredit(
	ctx contractapi.TransactionContextInterface,
	creditID string, projectType string, tonnes int,
	vintageYear int, aiRiskScore float64, ownerID string,
) error {
	existing, err := ctx.GetStub().GetState("credit:" + creditID)
	if err != nil {
		return fmt.Errorf("failed to read ledger: %v", err)
	}
	if existing != nil {
		return fmt.Errorf("credit %s already exists", creditID)
	}

	credit := Credit{
		Tonnes:      tonnes,
		ProjectType: projectType,
		VintageYear: vintageYear,
		AIRiskScore: aiRiskScore,
		Status:      "active",
	}
	creditJSON, _ := json.Marshal(credit)
	if err := ctx.GetStub().PutState("credit:"+creditID, creditJSON); err != nil {
		return err
	}

	ownership := Ownership{Units: tonnes}
	ownerJSON, _ := json.Marshal(ownership)
	return ctx.GetStub().PutState("ownership:"+creditID+":"+ownerID, ownerJSON)
}

// TransferCredit moves units from one owner to another.
func (c *CarbonCreditContract) TransferCredit(
	ctx contractapi.TransactionContextInterface,
	creditID string, fromOwner string, toOwner string, units int,
) error {
	// Pull the credit and make sure it's still active
	creditJSON, err := ctx.GetStub().GetState("credit:" + creditID)
	if err != nil || creditJSON == nil {
		return fmt.Errorf("credit %s not found", creditID)
	}
	var credit Credit
	json.Unmarshal(creditJSON, &credit)
	if credit.Status != "active" {
		return fmt.Errorf("credit %s is already retired", creditID)
	}

	fromJSON, _ := ctx.GetStub().GetState("ownership:" + creditID + ":" + fromOwner)
	var fromOwnership Ownership
	if fromJSON != nil {
		json.Unmarshal(fromJSON, &fromOwnership)
	}
	if fromOwnership.Units < units {
		return fmt.Errorf("insufficient units: %s holds %d of %s", fromOwner, fromOwnership.Units, creditID)
	}

	// Take from sender
	fromOwnership.Units -= units
	updatedFrom, _ := json.Marshal(fromOwnership)
	ctx.GetStub().PutState("ownership:"+creditID+":"+fromOwner, updatedFrom)

	// Give to receiver
	toJSON, _ := ctx.GetStub().GetState("ownership:" + creditID + ":" + toOwner)
	var toOwnership Ownership
	if toJSON != nil {
		json.Unmarshal(toJSON, &toOwnership)
	}
	toOwnership.Units += units
	updatedTo, _ := json.Marshal(toOwnership)
	return ctx.GetStub().PutState("ownership:"+creditID+":"+toOwner, updatedTo)
}

// RetireCredit permanently burns a credit. Once retired, it's done.
func (c *CarbonCreditContract) RetireCredit(
	ctx contractapi.TransactionContextInterface,
	creditID string, ownerID string,
) error {
	creditJSON, err := ctx.GetStub().GetState("credit:" + creditID)
	if err != nil || creditJSON == nil {
		return fmt.Errorf("credit %s not found", creditID)
	}
	var credit Credit
	json.Unmarshal(creditJSON, &credit)

	ownerJSON, _ := ctx.GetStub().GetState("ownership:" + creditID + ":" + ownerID)
	var ownership Ownership
	if ownerJSON != nil {
		json.Unmarshal(ownerJSON, &ownership)
	}
	if ownership.Units <= 0 {
		return fmt.Errorf("no units to retire: %s holds 0 of %s", ownerID, creditID)
	}

	credit.Status = "retired"
	updated, _ := json.Marshal(credit)
	return ctx.GetStub().PutState("credit:"+creditID, updated)
}

// QueryCredit looks up a credit's metadata by ID.
func (c *CarbonCreditContract) QueryCredit(
	ctx contractapi.TransactionContextInterface,
	creditID string,
) (*Credit, error) {
	creditJSON, err := ctx.GetStub().GetState("credit:" + creditID)
	if err != nil || creditJSON == nil {
		return nil, fmt.Errorf("credit %s not found", creditID)
	}
	var credit Credit
	json.Unmarshal(creditJSON, &credit)
	return &credit, nil
}

// QueryOwnership returns how many units a specific owner holds for a credit.
func (c *CarbonCreditContract) QueryOwnership(
	ctx contractapi.TransactionContextInterface,
	creditID string, ownerID string,
) (*Ownership, error) {
	ownerJSON, err := ctx.GetStub().GetState("ownership:" + creditID + ":" + ownerID)
	if err != nil || ownerJSON == nil {
		return nil, fmt.Errorf("no ownership record for %s:%s", creditID, ownerID)
	}
	var ownership Ownership
	json.Unmarshal(ownerJSON, &ownership)
	return &ownership, nil
}

// GetCreditHistory walks through every change ever made to a credit.
func (c *CarbonCreditContract) GetCreditHistory(
	ctx contractapi.TransactionContextInterface,
	creditID string,
) ([]map[string]interface{}, error) {
	iter, err := ctx.GetStub().GetHistoryForKey("credit:" + creditID)
	if err != nil {
		return nil, err
	}
	defer iter.Close()

	var history []map[string]interface{}
	for iter.HasNext() {
		mod, err := iter.Next()
		if err != nil {
			return nil, err
		}
		entry := map[string]interface{}{
			"tx_id":     mod.TxId,
			"timestamp": mod.Timestamp.AsTime().String(),
			"is_delete": mod.IsDelete,
			"value":     string(mod.Value),
		}
		history = append(history, entry)
	}
	return history, nil
}

func main() {
	chaincode, err := contractapi.NewChaincode(&CarbonCreditContract{})
	if err != nil {
		log.Fatalf("Error creating chaincode: %v", err)
	}
	if err := chaincode.Start(); err != nil {
		log.Fatalf("Error starting chaincode: %v", err)
	}
}