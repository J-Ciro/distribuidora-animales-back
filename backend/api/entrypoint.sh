#!/bin/bash
#
# Entrypoint Script for Distribuidora Perros y Gatos Backend
# Orchestrates:
#   1. Database migrations
#   2. Admin user seeding
#   3. FastAPI startup
#
# Exit immediately if any command fails
set -e

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                 BACKEND INITIALIZATION SCRIPT                  ║"
echo "║           Distribuidora Perros y Gatos - FastAPI               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==============================================================
# STEP 1: Execute Database Migrations
# ==============================================================
echo -e "${BLUE}[STEP 1/3]${NC} Executing database migrations..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if python /app/app/scripts/migrate.py; then
    echo -e "${GREEN}✅ Migrations completed successfully${NC}"
else
    echo -e "${RED}❌ Migration failed!${NC}"
    echo "   Please check the logs above for details."
    exit 1
fi

echo ""

# ==============================================================
# STEP 2: Execute Admin User Seeding
# ==============================================================
echo -e "${BLUE}[STEP 2/3]${NC} Seeding admin user..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if python /app/app/scripts/seed_admin.py; then
    echo -e "${GREEN}✅ Admin seeding completed successfully${NC}"
else
    echo -e "${RED}❌ Admin seeding failed!${NC}"
    echo "   Please check the logs above for details."
    exit 1
fi

echo ""

# ==============================================================
# STEP 3: Start FastAPI Server
# ==============================================================
echo -e "${BLUE}[STEP 3/3]${NC} Starting FastAPI server..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}═════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  🚀 Backend is starting on http://0.0.0.0:8000${NC}"
echo -e "${GREEN}  📚 API Documentation: http://localhost:8000/docs${NC}"
echo -e "${GREEN}═════════════════════════════════════════════════════════════════${NC}"
echo ""

# Execute uvicorn and pass all signals through (--reload is optional, disabled for production)
exec uvicorn main:app --host 0.0.0.0 --port 8000
