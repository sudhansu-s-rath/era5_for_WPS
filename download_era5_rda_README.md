## ERA5 NCAR RDA Download Setup Instructions

This guide covers downloading ERA5 reanalysis data for WPS input from NCAR RDA for any year/month combination.

### Overview

**Scripts in this package:**
- `download_era5_rda.py` - Python download script (NCAR RDA via HTTP)
- `download_era5_rda.slurm` - SLURM batch script for downloads
- `submit_era5_rda_download.sh` - Helper script for batch submissions
- `download_era5_cds.py` - Alternative CDS API script (requires cdsapi)
- `download_era5_cds.slurm` - SLURM script for CDS API downloads

**Recommended:** Use the RDA scripts (download_era5_rda.*) for direct NetCDF downloads.

### Step 1: Register for NCAR RDA Account
1. Go to: https://rda.ucar.edu/
2. Click "Register" and create a free account
3. Accept the data access terms

### Step 2: Get Your RDA API Key
1. Log in to NCAR RDA: https://rda.ucar.edu/
2. Go to your profile: https://rda.ucar.edu/#!lfd
3. Copy your API key (under "Authentication")

### Step 3: Configure RDA Credentials

**Option A: Add to your existing ~/.cdsapirc file**
```bash
# Append RDA section to existing file
cat >> ~/.cdsapirc << 'EOF'

[RDA]
email: your_email@example.com
key: your_rda_api_key_here
EOF

chmod 600 ~/.cdsapirc
```

**Option B: Use environment variables**
```bash
export RDA_EMAIL='your_email@example.com'
export RDA_KEY='your_rda_api_key_here'

# Add to ~/.bashrc to make permanent
echo "export RDA_EMAIL='your_email@example.com'" >> ~/.bashrc
echo "export RDA_KEY='your_rda_api_key_here'" >> ~/.bashrc
```

Replace `your_email@example.com` and `your_rda_api_key_here` with your actual credentials.

### Step 3: Download ERA5 Data

#### Method 1: Edit SLURM script directly (Recommended for batch downloads)

Edit `download_era5_rda.slurm` and change these variables:

```bash
# Configuration
YEAR="2015"          # Change to desired year (e.g., 2014, 2015, 2016)
MONTH="6"            # Change to desired month (1-12)
START_DAY=1          # First day to download
END_DAY=30           # Last day (adjust: 28/29 for Feb, 30/31 for others)
OUT_DIR="/data/mgeorge7/sudhansu_WORK/grb_files/era5_rda_${YEAR}_month${MONTH}"

# Download options (empty = download both types)
SKIP_PRESSURE=""     # Set to "--skip-pressure" to skip pressure levels
SKIP_SINGLE=""       # Set to "--skip-single" to skip single levels
```

Then submit:
```bash
cd /data/mgeorge7/sudhansu_WORK/grb_files
sbatch download_era5_rda.slurm
```

#### Method 2: Use helper script for quick submissions

```bash
cd /data/mgeorge7/sudhansu_WORK/grb_files

# Download May 2015
./submit_era5_rda_download.sh --year 2015 --month 5

# Download June-September 2016
./submit_era5_rda_download.sh --year 2016 --month 6 --end-day 30
./submit_era5_rda_download.sh --year 2016 --month 7 --end-day 31
./submit_era5_rda_download.sh --year 2016 --month 8 --end-day 31
./submit_era5_rda_download.sh --year 2016 --month 9 --end-day 30
```

#### Method 3: Interactive testing (no SLURM)

```bash
# Load environment
module load mamba/latest
source activate geo_env

# Download single day
python download_era5_rda.py \
  --year 2015 --month 6 \
  --start-day 1 --end-day 1 \
  --out-dir ./test_era5_2015jun

# Download full month
python download_era5_rda.py \
  --year 2015 --month 6 \
  --start-day 1 --end-day 30 \
  --out-dir /data/mgeorge7/sudhansu_WORK/grb_files/era5_rda_2015_month6
```

### Step 4: After Download - Convert to WPS Intermediate Format

Once netCDF files are downloaded, use `era5_to_int.py` to convert them for WRF:

```bash
cd /data/mgeorge7/sudhansu_WORK/grb_files/era5_to_int-main/intfiles

# Single timestep
python ../era5_to_int.py --path ../../era5_for_wps --isobaric 2015-06-01_00 1

# Full month (hourly)
python ../era5_to_int.py --path ../../era5_for_wps --isobaric 2015-06-01_00 2015-06-30_23 1

# 3-hourly for performance
python ../era5_to_int.py --path ../../era5_for_wps --isobaric 2015-06-01_00 2015-06-30_23 3
```

**For SLURM batch conversion** (recommended for full months):
1. Copy and edit `era5_convert_remaining.slurm`
2. Update start/end dates and paths
3. Submit: `sbatch era5_convert_remaining.slurm`

### Expected File Sizes & Download Times

**Pressure levels (per day):**
- 5 variables × 37 levels × 24 hours = ~1.3 GB/day
- Full month: ~40 GB

**Single levels (per month):**
- 20 variables × 24 hours × 30-31 days = ~15-20 GB

**Total per month:** ~55-60 GB

**Download time (SLURM job):** 1-2 hours depending on server load

### Workflow for Multiple Years/Months

**Example: Download May-September for 2014-2016**

```bash
cd /data/mgeorge7/sudhansu_WORK/grb_files

# Create a simple loop script
cat > download_multiple_months.sh << 'EOF'
#!/bin/bash
for YEAR in 2014 2015 2016; do
  for MONTH in 5 6 7 8 9; do
    # Set correct end day
    case $MONTH in
      6|9) END_DAY=30 ;;
      5|7|8) END_DAY=31 ;;
    esac
    
    echo "Downloading ${YEAR}-${MONTH}"
    
    # Edit slurm script
    sed -i "s/YEAR=\".*\"/YEAR=\"${YEAR}\"/" download_era5_rda.slurm
    sed -i "s/MONTH=\".*\"/MONTH=\"${MONTH}\"/" download_era5_rda.slurm
    sed -i "s/END_DAY=.*/END_DAY=${END_DAY}/" download_era5_rda.slurm
    sed -i "s|OUT_DIR=\".*\"|OUT_DIR=\"/data/mgeorge7/sudhansu_WORK/grb_files/era5_rda_${YEAR}_month${MONTH}\"|" download_era5_rda.slurm
    
    # Submit job
    sbatch download_era5_rda.slurm
    
    # Wait between submissions
    sleep 5
  done
done
EOF

chmod +x download_multiple_months.sh
./download_multiple_months.sh
```

Monitor all jobs:
```bash
squeue -u $USER
watch "squeue -u $USER; echo '---'; ls -lhd era5_rda_*/"
```

**Pressure Levels (37 levels, 1000-1 hPa):**
- Z: Geopotential
- Q: Specific humidity
- T: Temperature
- U: U component of wind
- V: V component of wind

**Single Levels:**
- SP: Surface pressure
- MSL: Mean sea level pressure
- 2T: 2m temperature
- 2D: 2m dewpoint temperature
- 10U, 10V: 10m wind components
- SSTK: Sea surface temperature
- SKT: Skin temperature
- LSM: Land-sea mask
- CI: Sea ice cover
- SD: Snow depth
- RSN: Snow density
- SWVL1-4: Soil moisture (4 layers)
- STL1-4: Soil temperature (4 layers)

These match exactly what `era5_to_int.py` requires!

### Variables Downloaded

**Pressure Levels (37 levels, 1000-1 hPa):**
- Z: Geopotential
- Q: Specific humidity
- T: Temperature
- U: U component of wind
- V: V component of wind

**Single Levels:**
- SP: Surface pressure
- MSL: Mean sea level pressure
- 2T: 2m temperature
- 2D: 2m dewpoint temperature
- 10U, 10V: 10m wind components
- SSTK: Sea surface temperature
- SKT: Skin temperature
- LSM: Land-sea mask
- CI: Sea ice cover
- SD: Snow depth
- RSN: Snow density
- SWVL1-4: Soil moisture (4 layers)
- STL1-4: Soil temperature (4 layers)

These variables match exactly what `era5_to_int.py` requires for WRF/WPS!

### Troubleshooting

**Downloads fail with authentication error:**
- Verify RDA credentials in `~/.cdsapirc` or environment variables
- Check RDA account is active: https://rda.ucar.edu/

**Job runs out of time (48h limit):**
- Download fewer days per job
- Split into 10-day chunks using START_DAY/END_DAY

**Single-level files fail to download:**
- Some soil variables (STL2-4, SWVL2-4) may be unavailable
- Set `SKIP_SINGLE="--skip-single"` if not needed
- Pressure-level data alone is sufficient for most WRF simulations

**Disk space issues:**
- Each month requires ~55-60 GB
- Plan for ~300 GB per year (May-Sep)
- Monitor: `du -sh era5_rda_*`

### Directory Organization

Recommended structure:
```
grb_files/
├── download_era5_rda.py
├── download_era5_rda.slurm
├── submit_era5_rda_download.sh
├── era5_rda_2014_month5/      # May 2014 (~60 GB)
│   ├── pressure_levels/       # 155 files
│   └── single_levels/         # 20 files
├── era5_rda_2015_month6/      # June 2015
├── era5_rda_2015_month7/      # July 2015
├── era5_for_wps/              # Symlinks for conversion
└── era5_to_int-main/
    └── intfiles/              # WPS intermediate format output
```

### Comparison: NCAR RDA vs CDS API

| Aspect | NCAR RDA (download_era5_rda.*) | CDS API (download_era5_cds.*) |
|--------|--------------------------------|-------------------------------|
| Format | NetCDF4 | GRIB1/GRIB2 |
| Processing | `era5_to_int.py` → WPS | `ungrib.exe` → WPS |
| Speed | Direct netCDF access | GRIB decode step |
| Variables | Pre-organized by level | Need Vtable setup |
| Credentials | RDA account | Copernicus CDS account |
| Best for | MPAS-A, WRF (modern) | Traditional WRF workflow |
| Status | ✅ Working (2014 May complete) | ⚠️ Alternative method |
