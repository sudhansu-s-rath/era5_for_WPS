#!/bin/bash
# Simple script to download one month of ERA5 data
# Usage: ./download_month.sh <month_number> [year]
#
# Examples:
#   ./download_month.sh 6        # Downloads June 2014
#   ./download_month.sh 7        # Downloads July 2014
#   ./download_month.sh 8 2015   # Downloads August 2015


if [ $# -ne 2 ]; then
    echo "Usage: $0 <month_number> <year>"
    echo ""
    echo "Examples:"
    echo "  $0 6 2014      # June 2014"
    echo "  $0 7 2014      # July 2014"
    echo "  $0 8 2015      # August 2015"
    exit 1
fi

MONTH=$1
YEAR=$2

# Month names for directory
declare -A MONTH_NAMES=(
    [1]="january" [2]="february" [3]="march" [4]="april"
    [5]="may" [6]="june" [7]="july" [8]="august"
    [9]="september" [10]="october" [11]="november" [12]="december"
)

# Days in each month (non-leap year)
declare -A DAYS_IN_MONTH=(
    [1]=31 [2]=28 [3]=31 [4]=30 [5]=31 [6]=30
    [7]=31 [8]=31 [9]=30 [10]=31 [11]=30 [12]=31
)

# Adjust February for leap years
if [ $((YEAR % 4)) -eq 0 ] && { [ $((YEAR % 100)) -ne 0 ] || [ $((YEAR % 400)) -eq 0 ]; }; then
    DAYS_IN_MONTH[2]=29
fi

MONTH_NAME=${MONTH_NAMES[$MONTH]}
END_DAY=${DAYS_IN_MONTH[$MONTH]}

if [ -z "$MONTH_NAME" ]; then
    echo "ERROR: Invalid month number: $MONTH (must be 1-12)"
    exit 1
fi

BASE_DIR="/data/mgeorge7/sudhansu_WORK/grb_files/era5_rda_${YEAR}"
OUT_DIR="$BASE_DIR/$MONTH_NAME"

echo "======================================================"
echo "ERA5 Download - $MONTH_NAME $YEAR"
echo "======================================================"
echo "Year:       $YEAR"
echo "Month:      $MONTH ($MONTH_NAME)"
echo "Days:       1-$END_DAY"
echo "Output:     $OUT_DIR"
echo "======================================================"

# Create output directory if it doesn't exist
mkdir -p "$OUT_DIR"

# Submit job
cd /data/mgeorge7/sudhansu_WORK/grb_files

JOB_ID=$(sbatch --parsable \
    --export=ALL,YEAR=$YEAR,MONTH=$MONTH,START_DAY=1,END_DAY=$END_DAY,OUT_DIR="$OUT_DIR" \
    download_era5_rda.slurm)

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Job submitted successfully!"
    echo "  Job ID: $JOB_ID"
    echo ""
    echo "Monitor progress:"
    echo "  squeue -u \$USER"
    echo "  tail -f era5_rda_download_${JOB_ID}.out"
    echo ""
    echo "Check logs after completion:"
    echo "  less era5_rda_download_${JOB_ID}.out"
    echo "  less era5_rda_download_${JOB_ID}.err"
else
    echo "ERROR: Job submission failed"
    exit 1
fi
