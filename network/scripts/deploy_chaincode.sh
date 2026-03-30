#!/bin/bash
# Deploys the carbon_credit chaincode using the Fabric 2.x lifecycle.
#
# Steps: package -> install on both peers -> approve for both orgs -> commit
#
# The endorsement policy requires both DeveloperOrg and RegulatorOrg to sign.
# Make sure the network is already running (start_network.sh).
#
# Usage: cd network && ./scripts/deploy_chaincode.sh

set -e

CHANNEL_NAME="veridium-channel"
CC_NAME="carbon_credit"
CC_VERSION="1.0"
CC_SEQUENCE=1
CC_SRC_PATH="/opt/gopath/src/github.com/veridium-mesh/chaincode/carbon_credit"
ENDORSEMENT_POLICY="AND('DeveloperOrgMSP.peer','RegulatorOrgMSP.peer')"

echo "=== Deploying Chaincode ==="

# Package it up
echo "--- Packaging chaincode ---"
docker exec peer0.developer.veridium.com peer lifecycle chaincode package \
  "${CC_NAME}.tar.gz" \
  --path "${CC_SRC_PATH}" \
  --lang golang \
  --label "${CC_NAME}_${CC_VERSION}"

# Install on both peers
echo "--- Installing on DeveloperOrg peer ---"
docker exec peer0.developer.veridium.com peer lifecycle chaincode install \
  "${CC_NAME}.tar.gz"

echo "--- Installing on RegulatorOrg peer ---"
docker exec peer0.regulator.veridium.com peer lifecycle chaincode install \
  "${CC_NAME}.tar.gz"

# Grab the package ID
echo "--- Querying installed chaincode ---"
PACKAGE_ID=$(docker exec peer0.developer.veridium.com \
  peer lifecycle chaincode queryinstalled \
  --output json | jq -r ".installed_chaincodes[0].package_id")
echo "Package ID: ${PACKAGE_ID}"

# Approve for both orgs
echo "--- Approving for DeveloperOrg ---"
docker exec peer0.developer.veridium.com peer lifecycle chaincode approveformyorg \
  -o orderer.veridium.com:7050 \
  --channelID "${CHANNEL_NAME}" \
  --name "${CC_NAME}" \
  --version "${CC_VERSION}" \
  --package-id "${PACKAGE_ID}" \
  --sequence ${CC_SEQUENCE} \
  --signature-policy "${ENDORSEMENT_POLICY}" \
  --tls --cafile /etc/hyperledger/fabric/tls/ca.crt

echo "--- Approving for RegulatorOrg ---"
docker exec peer0.regulator.veridium.com peer lifecycle chaincode approveformyorg \
  -o orderer.veridium.com:7050 \
  --channelID "${CHANNEL_NAME}" \
  --name "${CC_NAME}" \
  --version "${CC_VERSION}" \
  --package-id "${PACKAGE_ID}" \
  --sequence ${CC_SEQUENCE} \
  --signature-policy "${ENDORSEMENT_POLICY}" \
  --tls --cafile /etc/hyperledger/fabric/tls/ca.crt

# Commit to the channel
echo "--- Committing chaincode ---"
docker exec peer0.developer.veridium.com peer lifecycle chaincode commit \
  -o orderer.veridium.com:7050 \
  --channelID "${CHANNEL_NAME}" \
  --name "${CC_NAME}" \
  --version "${CC_VERSION}" \
  --sequence ${CC_SEQUENCE} \
  --signature-policy "${ENDORSEMENT_POLICY}" \
  --tls --cafile /etc/hyperledger/fabric/tls/ca.crt \
  --peerAddresses peer0.developer.veridium.com:7051 \
  --peerAddresses peer0.regulator.veridium.com:9051

# Make sure it worked
echo "--- Verifying deployment ---"
docker exec peer0.developer.veridium.com peer lifecycle chaincode querycommitted \
  --channelID "${CHANNEL_NAME}" \
  --name "${CC_NAME}"

echo "=== Chaincode deployed successfully ==="
