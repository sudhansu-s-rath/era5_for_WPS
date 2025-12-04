#!/bin/bash

# ==============================================================================
# Helper script to submit ERA5 download jobs to SLURM
# ==============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
YEAR="2014"
MONTH="05"
START_DAY=1
END_DAY=31
OUT_DIR="/data/mgeorge7/sudhansu_WORK/grb_files/2014era_hrly"
AREA=""

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
        --out-dir)
            OUT_DIR="$2"
            shift 2
            ;;
        --area)
            AREA="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --year YEAR          Year to download (default: 2014)"
            echo "  --month MONTH        Month to download (default: 05)"
            echo "  --start-day DAY      Start day (default: 1)"
            echo "  --end-day DAY        End day (default: 31)"
            echo "  --out-dir DIR        Output directory"
            echo "  --area N,W,S,E       Geographic subset (optional)"
            echo "  --help               Show this help message"
            echo ""
            echo "Example:"
            echo "  $0 --year 2014 --month 05 --start-day 1 --end-day 31"
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
SLURM_SCRIPT="${SCRIPT_DIR}/download_era5_cds.slurm"
PYTHON_SCRIPT="${SCRIPT_DIR}/download_era5_cds.py"

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
echo "ERA5 Download Job Submission"
echo "=========================================="
echo "Year:           $YEAR"
echo "Month:          $MONTH"
echo "Days:           $START_DAY to $END_DAY"
echo "Output Dir:     $OUT_DIR"
echo "Area:           ${AREA:-Global}"
echo "=========================================="
echo ""

# Create output directory
mkdir -p "$OUT_DIR"

# Create a temporary SLURM script with custom values
TEMP_SLURM="${SCRIPT_DIR}/download_era5_cds_${YEAR}${MONTH}.slurm"
cp "$SLURM_SCRIPT" "$TEMP_SLURM"

# Update variables in temporary script
sed -i "s|YEAR=\".*\"|YEAR=\"${YEAR}\"|g" "$TEMP_SLURM"
sed -i "s|MONTH=\".*\"|MONTH=\"${MONTH}\"|g" "$TEMP_SLURM"
sed -i "s|START_DAY=.*|START_DAY=${START_DAY}|g" "$TEMP_SLURM"
sed -i "s|END_DAY=.*|END_DAY=${END_DAY}|g" "$TEMP_SLURM"
sed -i "s|OUT_DIR=\".*\"|OUT_DIR=\"${OUT_DIR}\"|g" "$TEMP_SLURM"

if [ -n "$AREA" ]; then
    sed -i "s|AREA=\".*\"|AREA=\"${AREA}\"|g" "$TEMP_SLURM"
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
    echo "  tail -f download_era5_cds_${JOB_ID}.out"
    echo "  tail -f download_era5_cds_${JOB_ID}.err"
    echo ""
    echo "Cancel job if needed:"
    echo "  scancel $JOB_ID"
else
    echo -e "${RED}✗ Job submission failed!${NC}"
    rm -f "$TEMP_SLURM"
    exit 1
fi

echo "=========================================="
