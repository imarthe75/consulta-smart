#!/bin/bash

###############################################################################
# Load Testing Script using k6
# Usage: bash scripts/load-test.sh [baseline|spike|soak|all]
###############################################################################

set -e

TEST_TYPE="${1:-baseline}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[✓]${NC} $1"
}

error() {
    echo -e "${RED}[✗]${NC} $1"
    exit 1
}

warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

echo "======================================================================"
echo "ConsultaRPP Load Testing"
echo "Test Type: $TEST_TYPE"
echo "Timestamp: $TIMESTAMP"
echo "======================================================================"
echo ""

# Check prerequisites
command -v k6 >/dev/null 2>&1 || error "k6 not installed. Install: https://k6.io/docs/getting-started/installation"

# Create output directory
mkdir -p load-testing/results

# Run tests
case $TEST_TYPE in
    baseline)
        log "Running baseline load test (50 users, 20 min)..."
        k6 run \
            --vus 0 \
            --stage "5m:50" \
            --stage "10m:50" \
            --stage "5m:0" \
            --out csv=load-testing/results/baseline_${TIMESTAMP}.csv \
            load-testing/load-test.js
        ;;

    spike)
        log "Running spike test (0 → 500 users)..."
        k6 run \
            --vus 0 \
            --stage "2m:100" \
            --stage "2m:500" \
            --stage "3m:0" \
            --out csv=load-testing/results/spike_${TIMESTAMP}.csv \
            load-testing/load-test.js
        ;;

    soak)
        log "Running soak test (50 users for 23 hours)..."
        warn "This will run for 23 hours. Press Ctrl+C to stop."
        k6 run \
            --vus 50 \
            --duration 82800s \
            --out csv=load-testing/results/soak_${TIMESTAMP}.csv \
            load-testing/load-test.js
        ;;

    all)
        log "Running all tests sequentially..."
        for test in baseline spike soak; do
            bash scripts/load-test.sh $test
            sleep 5
        done
        ;;

    *)
        error "Invalid test type. Use: baseline, spike, soak, or all"
        ;;
esac

echo ""
echo "======================================================================"
log "Load test completed!"
echo ""
echo "Results saved to: load-testing/results/"
echo ""
echo "Analysis:"
echo "  - Export to JSON: k6 run --out=json load-testing/load-test.js"
echo "  - Export to HTML: k6 run --out=html=results.html load-testing/load-test.js"
echo "  - Upload to k6 Cloud: k6 cloud load-testing/load-test.js"
echo ""

exit 0
