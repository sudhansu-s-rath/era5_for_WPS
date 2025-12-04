#!/bin/bash
#SBATCH --job-name=era5_grib_download
#SBATCH --output=era5_grib_download_%j.out
#SBATCH --error=era5_grib_download_%j.err
#SBATCH --time=48:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8GB
#SBATCH --partition=general

# ==============================================================================
# SLURM script for downloading ERA5 GRIB data
# ==============================================================================

echo "=========================================="
echo "Job started at: $(date)"
echo "Job ID: $SLURM_JOB_ID"
echo "Running on node: $(hostname)"
echo "=========================================="

# Load required modules (adjust for your system)
module purge
module load mamba/latest

# Activate Python environment with cdsapi installed
# Adjust this to your actual environment name
source activate geo_env

# Check if cdsapi is available
python -c "import cdsapi; print('cdsapi version:', cdsapi.__version__)" || {
    echo "ERROR: cdsapi not found in environment"
    exit 1
}

# Configuration (edit these variables)
YEAR="2014"
MONTH="05"
START_DAY=1
END_DAY=31
OUT_DIR="/data/mgeorge7/sudhansu_WORK/grb_files/2014era_hrly"

# Optional: Geographic subset [N,W,S,E]
# Leave empty for global download
# AREA="40,-120,25,-105"  # Example: Phoenix region
AREA=""

# Script location
SCRIPT_DIR="/data/mgeorge7/sudhansu_WORK/grb_files"
PYTHON_SCRIPT="${SCRIPT_DIR}/era5_grib_download.py"

# Verify script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "ERROR: Python script not found at $PYTHON_SCRIPT"
    exit 1
fi

# Change to output directory
mkdir -p "$OUT_DIR"
cd "$OUT_DIR" || exit 1

echo ""
echo "Configuration:"
echo "  Year:       $YEAR"
echo "  Month:      $MONTH"
echo "  Days:       $START_DAY to $END_DAY"
echo "  Output Dir: $OUT_DIR"
echo "  Area:       ${AREA:-Global}"
echo ""

# Build command
CMD="python $PYTHON_SCRIPT --year $YEAR --month $MONTH --start-day $START_DAY --end-day $END_DAY --out-dir $OUT_DIR"

if [ -n "$AREA" ]; then
    CMD="$CMD --area $AREA"
fi

echo "Running command:"
echo "$CMD"
echo ""

# Run the download script
$CMD

EXIT_CODE=$?

echo ""
echo "=========================================="
echo "Job finished at: $(date)"
echo "Exit code: $EXIT_CODE"
echo "=========================================="

exit $EXIT_CODE
