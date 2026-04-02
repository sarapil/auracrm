#!/bin/bash
# auracrm/scripts/safe_migrate.sh
# Safe migration wrapper: snapshot → migrate → rollback on error
# Usage: bash apps/auracrm/auracrm/scripts/safe_migrate.sh [site_name]

set -euo pipefail

SITE="${1:-dev.localhost}"
BENCH_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BENCH_DIR}/archived/migrations"
LOG_FILE="${BACKUP_DIR}/migrate_${TIMESTAMP}.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

mkdir -p "$BACKUP_DIR"

echo -e "${YELLOW}═══════════════════════════════════════════════${NC}"
echo -e "${YELLOW}  AuraCRM Safe Migration — ${SITE}${NC}"
echo -e "${YELLOW}  Timestamp: ${TIMESTAMP}${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════${NC}"

# Step 1: Pre-migration backup
echo -e "\n${YELLOW}[1/5] Creating database snapshot...${NC}"
cd "$BENCH_DIR"
if bench --site "$SITE" backup --with-files 2>&1 | tee -a "$LOG_FILE"; then
    echo -e "${GREEN}  ✓ Backup created successfully${NC}"
else
    echo -e "${RED}  ✗ Backup failed — aborting migration${NC}"
    exit 1
fi

# Step 2: Health check
echo -e "\n${YELLOW}[2/5] Running pre-migration health check...${NC}"
if bench --site "$SITE" execute auracrm.scripts.bench_health_check.run_full_check 2>&1 | tee -a "$LOG_FILE"; then
    echo -e "${GREEN}  ✓ Health check passed${NC}"
else
    echo -e "${YELLOW}  ⚠ Health check had warnings (continuing)${NC}"
fi

# Step 3: Run migration
echo -e "\n${YELLOW}[3/5] Running bench migrate...${NC}"
if bench --site "$SITE" migrate 2>&1 | tee -a "$LOG_FILE"; then
    echo -e "${GREEN}  ✓ Migration completed successfully${NC}"
else
    echo -e "${RED}  ✗ Migration FAILED${NC}"

    # Step 3a: Auto-rollback
    echo -e "\n${RED}[ROLLBACK] Restoring from backup...${NC}"
    LATEST_BACKUP=$(ls -t "${BENCH_DIR}/sites/${SITE}/private/backups/"*database* 2>/dev/null | head -1)

    if [ -n "$LATEST_BACKUP" ]; then
        echo -e "${YELLOW}  Restoring: ${LATEST_BACKUP}${NC}"
        bench --site "$SITE" restore "$LATEST_BACKUP" 2>&1 | tee -a "$LOG_FILE"
        echo -e "${GREEN}  ✓ Database restored from backup${NC}"
    else
        echo -e "${RED}  ✗ No backup found for rollback! Manual intervention required.${NC}"
    fi

    echo -e "${RED}  Migration log saved to: ${LOG_FILE}${NC}"
    exit 1
fi

# Step 4: Clear cache
echo -e "\n${YELLOW}[4/5] Clearing cache...${NC}"
bench --site "$SITE" clear-cache 2>&1 | tee -a "$LOG_FILE"
echo -e "${GREEN}  ✓ Cache cleared${NC}"

# Step 5: Post-migration health check
echo -e "\n${YELLOW}[5/5] Running post-migration health check...${NC}"
bench --site "$SITE" execute auracrm.scripts.bench_health_check.run_full_check 2>&1 | tee -a "$LOG_FILE"

echo -e "\n${GREEN}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✓ Migration completed successfully!${NC}"
echo -e "${GREEN}  Log: ${LOG_FILE}${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
