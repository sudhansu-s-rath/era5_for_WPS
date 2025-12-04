#!/bin/bash

# ==============================================================================
# Helper script to submit ERA5 RDA download jobs to SLURM
# ==============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Default values
YEAR="2014"
MONTH="5"
START_DAY=1
END_DAY=31
HOURS="0,6,12,18"
OUT_DIR="/data/mgeorge7/sudhansu_WORK/grb_files/era5_rda_data"
VARS=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --year)
            YEAR="$2"
            shift 2
            ;;
        --month)
            MONTH="$2"
            shift 2
            ;;
        --start-day)
            START_DAY="$2"
            shift 2
            ;;
        --end-day)
            END_DAY="$2"
            shift 2
            ;;
        --hours)
            HOURS="$2"
            shift 2
            ;;
        --out-dir)
            OUT_DIR="$2"
            shift 2
            ;;
        --vars)
            VARS="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --year YEAR          Year to download (default: 2014)"
            echo "  --month MONTH        Month to download (default: 5)"
            echo "  --start-day DAY      Start day (default: 1)"
            echo "  --end-day DAY        End day (default: 31)"
            echo "  --hours HOURS        Comma-separated hours (default: 0,6,12,18)"
            echo "  --out-dir DIR        Output directory"
            echo "  --vars VARS          Comma-separated variables (optional, e.g., Z,T,U,V)"
            echo "  --help               Show this help message"
            echo ""
            echo "Examples:"
            echo "  # Download all variables for May 2014"
            echo "  $0 --year 2014 --month 5"
            echo ""
            echo "  # Download specific days with 3-hourly data"
            echo "  $0 --year 2014 --month 5 --start-day 1 --end-day 5 --hours 0,3,6,9,12,15,18,21"
            echo ""
            echo "  # Download only atmospheric variables"
            echo "  $0 --year 2014 --month 5 --vars Z,T,U,V,Q"
            echo ""
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SLURM_SCRIPT="${SCRIPT_DIR}/download_era5_rda.slurm"
PYTHON_SCRIPT="${SCRIPT_DIR}/download_era5_rda.py"

# Verify files exist
if [ ! -f "$SLURM_SCRIPT" ]; then
    echo -e "${RED}ERROR: SLURM script not found at $SLURM_SCRIPT${NC}"
    exit 1
fi

if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo -e "${RED}ERROR: Python script not found at $PYTHON_SCRIPT${NC}"
    exit 1
fi

# Display configuration
echo "=========================================="
echo "ERA5 NCAR RDA Download Job Submission"
echo "=========================================="
echo "Year:           $YEAR"
echo "Month:          $MONTH"
echo "Days:           $START_DAY to $END_DAY"
echo "Hours:          $HOURS"
echo "Variables:      ${VARS:-All (matching era5_to_int requirements)}"
echo "Output Dir:     $OUT_DIR"
echo "=========================================="
echo ""

# Check RDA credentials
RDA_CREDS="$HOME/.cdsapirc"
if [ ! -f "$RDA_CREDS" ]; then
    echo -e "${RED}ERROR: NCAR RDA API key not found!${NC}"
    echo ""
    echo "To download from NCAR RDA, you need to:"
    echo "1. Register at: https://rda.ucar.edu/"
    echo "2. Get your API key from: https://rda.ucar.edu/#!lfd"
    echo "3. Create ~/.cdsapirc with your API key:"
    echo ""
    echo "   [RDA]"
    echo "   email: your_email@example.com"
    echo "   key: your_api_key_here"
    echo ""
    echo "Alternative: Export environment variables:"
    echo "   export RDA_EMAIL='your_email@example.com'"
    echo "   export RDA_KEY='your_api_key_here'"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ Found RDA credentials${NC}"
echo ""

# Create output directory
mkdir -p "$OUT_DIR"

# Create a temporary SLURM script with custom values
TEMP_SLURM="${SCRIPT_DIR}/download_era5_rda_${YEAR}${MONTH}.slurm"
cp "$SLURM_SCRIPT" "$TEMP_SLURM"

# Update variables in temporary script
sed -i "s|YEAR=\".*\"|YEAR=\"${YEAR}\"|g" "$TEMP_SLURM"
sed -i "s|MONTH=\".*\"|MONTH=\"${MONTH}\"|g" "$TEMP_SLURM"
sed -i "s|START_DAY=.*|START_DAY=${START_DAY}|g" "$TEMP_SLURM"
sed -i "s|END_DAY=.*|END_DAY=${END_DAY}|g" "$TEMP_SLURM"
sed -i "s|HOURS=\".*\"|HOURS=\"${HOURS}\"|g" "$TEMP_SLURM"
sed -i "s|OUT_DIR=\".*\"|OUT_DIR=\"${OUT_DIR}\"|g" "$TEMP_SLURM"

if [ -n "$VARS" ]; then
    sed -i "s|VARS=\".*\"|VARS=\"${VARS}\"|g" "$TEMP_SLURM"
fi

# Submit the job
echo -e "${YELLOW}Submitting job to SLURM...${NC}"
JOB_OUTPUT=$(sbatch "$TEMP_SLURM")

if [ $? -eq 0 ]; then
    JOB_ID=$(echo "$JOB_OUTPUT" | awk '{print $NF}')
    echo -e "${GREEN}✓ Job submitted successfully!${NC}"
    echo "  Job ID: $JOB_ID"
    echo ""
    echo "Monitor job status with:"
    echo "  squeue -j $JOB_ID"
    echo ""
    echo "View output logs:"
    echo "  tail -f era5_rda_download_${JOB_ID}.out"
    echo "  tail -f era5_rda_download_${JOB_ID}.err"
    echo ""
    echo "Cancel job if needed:"
    echo "  scancel $JOB_ID"
else
    echo -e "${RED}✗ Job submission failed!${NC}"
    rm -f "$TEMP_SLURM"
    exit 1
fi

echo "=========================================="
