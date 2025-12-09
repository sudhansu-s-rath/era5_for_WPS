#!/bin/bash
#SBATCH --job-name=era5_rda_download
#SBATCH --output=era5_rda_download_%j.out
#SBATCH --error=era5_rda_download_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8GB
#SBATCH --time=48:00:00

# ============================================================
# SLURM batch script for ERA5 netCDF download from NCAR RDA
# Dataset: ds633.0 (ERA5 Reanalysis 0.25° Lat-Lon Grid)
# ============================================================
# 
# Usage:
#   sbatch download_era5_rda.slurm
#
# Note: Each file contains all 24 hours (00-23 UTC) per day
# ============================================================

echo "======================================================"
echo "ERA5 RDA Download Job"
echo "======================================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "CPUs: $SLURM_CPUS_PER_TASK"
echo "Memory: $SLURM_MEM_PER_NODE MB"
echo "Started: $(date)"
echo "======================================================"

# Load required modules
module load mamba/latest

# Activate Python environment
source activate geo_env

# Verify wget is available
which wget || {
    echo "ERROR: wget not found"
    exit 1
}

# Configuration (can be overridden via --export when submitting job)
YEAR="${YEAR:-2014}"
MONTH="${MONTH:-5}"
START_DAY="${START_DAY:-1}"
END_DAY="${END_DAY:-31}"
OUT_DIR="${OUT_DIR:-/data/mgeorge7/sudhansu_WORK/grb_files/era5_rda_2014may}"

# Optional: Specify variables (leave empty for all)
# VARS="Z,T,U,V,Q"  # Example: only atmospheric variables
VARS=""

# Optional: Skip pressure or single level downloads
# SKIP_PRESSURE="--skip-pressure"  # Uncomment to skip pressure levels if already downloaded
# SKIP_SINGLE="--skip-single"      # Uncomment to skip single levels if not needed
SKIP_PRESSURE=""
SKIP_SINGLE=""

echo ""
echo "Configuration:"
echo "  Year:       $YEAR"
echo "  Month:      $MONTH"
echo "  Days:       $START_DAY to $END_DAY"
echo "  Note:       Pressure files are daily (24h), surface files are monthly"
echo "  Variables:  ${VARS:-All}"
echo "  Output Dir: $OUT_DIR"
echo ""

# Change to script directory
cd $SLURM_SUBMIT_DIR

# Script location
PYTHON_SCRIPT="./download_era5_rda.py"

# Verify script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "ERROR: Python script not found at $PYTHON_SCRIPT"
    exit 1
fi

# Create output directory
mkdir -p "$OUT_DIR"

# Build command
CMD="python $PYTHON_SCRIPT --year $YEAR --month $MONTH --start-day $START_DAY --end-day $END_DAY --out-dir $OUT_DIR"

if [ -n "$VARS" ]; then
    CMD="$CMD --vars $VARS"
fi

if [ -n "$SKIP_PRESSURE" ]; then
    CMD="$CMD $SKIP_PRESSURE"
fi

if [ -n "$SKIP_SINGLE" ]; then
    CMD="$CMD $SKIP_SINGLE"
fi

echo "Running command:"
echo "$CMD"
echo ""

# Run the download script
$CMD

EXIT_CODE=$?

echo ""
echo "======================================================"
echo "Job finished: $(date)"
echo "Exit code: $EXIT_CODE"
echo "======================================================"

exit $EXIT_CODE
