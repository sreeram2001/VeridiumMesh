#!/bin/bash
# Starts the VeridiumMesh Fabric network from scratch.
#
# What it does:
#   1. Generates crypto material (cryptogen)
#   2. Creates the genesis block and channel tx (configtxgen)
#   3. Spins up Docker containers (orderer, peers, CouchDB)
#   4. Creates veridium-channel and joins both org peers
#
# You'll need Docker, Docker Compose, and the Fabric binaries on your PATH.
#
# Usage: cd network && ./scripts/start_network.sh

set -e

CHANNEL_NAME="veridium-channel"
NETWORK_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== Starting Fabric Network ==="

# Generate certs and keys for all orgs
echo "--- Generating crypto material ---"
cryptogen generate --config="${NETWORK_DIR}/crypto-config.yaml" \
  --output="${NETWORK_DIR}/crypto-config"

# Build the genesis block and channel transaction
echo "--- Generating genesis block ---"
mkdir -p "${NETWORK_DIR}/channel-artifacts"
configtxgen -profile VeridiumGenesis \
  -channelID system-channel \
  -outputBlock "${NETWORK_DIR}/channel-artifacts/genesis.block" \
  -configPath "${NETWORK_DIR}"

echo "--- Generating channel transaction ---"
configtxgen -profile VeridiumChannel \
  -outputCreateChannelTx "${NETWORK_DIR}/channel-artifacts/channel.tx" \
  -channelID "${CHANNEL_NAME}" \
  -configPath "${NETWORK_DIR}"

# Fire up the containers
echo "--- Starting Docker containers ---"
docker-compose -f "${NETWORK_DIR}/docker-compose.yaml" up -d
sleep 5

# Create the channel and get both peers on it
echo "--- Creating channel: ${CHANNEL_NAME} ---"
docker exec peer0.developer.veridium.com peer channel create \
  -o orderer.veridium.com:7050 \
  -c "${CHANNEL_NAME}" \
  -f /etc/hyperledger/configtx/channel.tx \
  --tls --cafile /etc/hyperledger/fabric/tls/ca.crt

echo "--- Joining DeveloperOrg peer ---"
docker exec peer0.developer.veridium.com peer channel join \
  -b "${CHANNEL_NAME}.block"

echo "--- Joining RegulatorOrg peer ---"
docker exec peer0.regulator.veridium.com peer channel join \
  -b "${CHANNEL_NAME}.block"

echo "=== Network is up and running ==="
