#!/bin/bash
set -e

echo ""
echo "===================================================================="
echo "                 BACKEND INITIALIZATION SCRIPT                      "
echo "           Distribuidora Perros y Gatos - FastAPI                   "
echo "===================================================================="
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}[STEP 1/3]${NC} Executing database migrations..."
echo "===================================================================="

if python /app/app/scripts/migrate.py; then
    echo -e "${GREEN}OK - Migrations completed successfully${NC}"
else
    echo -e "${RED}FAILED - Migration failed!${NC}"
    exit 1
fi

echo ""

echo -e "${BLUE}[STEP 2/3]${NC} Seeding admin user..."
echo "===================================================================="

if python /app/app/scripts/seed_admin.py; then
    echo -e "${GREEN}OK - Admin seeding completed successfully${NC}"
else
    echo -e "${RED}FAILED - Admin seeding failed!${NC}"
    exit 1
fi

echo ""

echo -e "${BLUE}[STEP 3/3]${NC} Starting FastAPI server..."
echo "===================================================================="
echo ""
echo -e "${GREEN}Backend is starting on http://0.0.0.0:8000${NC}"
echo -e "${GREEN}API Documentation: http://localhost:8000/docs${NC}"
echo ""

exec uvicorn main:app --host 0.0.0.0 --port 8000
