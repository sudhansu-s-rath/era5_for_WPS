# ERA5 to WPS Workflow

Complete workflow for preparing ERA5 reanalysis data for WRF-WPS preprocessing system.

## Overview

This repository provides a complete multi-step workflow to make ERA5 reanalysis data compatible with the WRF Preprocessing System (WPS). The process converts hourly ERA5 NetCDF data into WPS intermediate format (GRIB) files that can be ingested by `metgrid.exe`.

**Note:** Variable selection and download approach are based on recommendations from the WRF forum discussion: [How to use ERA5 data from Copernicus database](https://forum.mmm.ucar.edu/threads/how-to-use-era5-data-from-copernicus-database.19293/)

### Workflow Steps

```
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 1: Download ERA5 NetCDF Files                                    │
│  ├─ Source: NCAR RDA (ds633.0)                                         │
│  ├─ Format: NetCDF (pressure levels + single levels)                   │
│  ├─ Resolution: 0.25° × 0.25°, hourly                                  │
│  └─ Tools: download_era5_rda.py, download_month.sh                     │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 2: Convert to WPS Intermediate Format                            │
│  ├─ Tool: era5_to_int.py (modified from GitHub)                        │
│  ├─ Input: ERA5 NetCDF files                                           │
│  ├─ Output: WPS intermediate files (GRIB format)                       │
│  └─ Variables: Automatically selects required WPS variables            │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 3: WPS Processing                                                │
│  ├─ Tool: metgrid.exe (part of WRF-WPS)                                │
│  ├─ Input: WPS intermediate files from Step 2                          │
│  ├─ Output: met_em.* files ready for WRF real.exe                      │
│  └─ Complete: Ready for WRF simulation                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

### Repository Contents

**Download Scripts (Step 1):**
- `download_era5_rda.py` - Python script for NCAR RDA downloads (NetCDF via HTTP)
- `download_era5_rda.slurm` - SLURM batch script for HPC downloads
- `download_month.sh` - Simple helper: `./download_month.sh <month> [year]`
- `submit_era5_rda_download.sh` - Advanced batch submission helper
- *Alternative:* `download_era5_cds.py` - CDS API method (see README_CDS_API.md)

**Conversion Scripts (Step 2):**
- `era5_to_int-main/` - Modified era5_to_int package for NetCDF → WPS intermediate format
- `era5_to_int-main/era5_to_int.py` - Main conversion script

**Documentation:**
- README.md - This file - Complete workflow guide
- README_CDS_API.md - Alternative download method using Copernicus CDS API

---

## STEP 1: Download ERA5 NetCDF Data

### 1.1 Prerequisites

### 1.1 Prerequisites

**Register for NCAR RDA Account:**
1. Visit: https://rda.ucar.edu/
2. Click "Register" and create a free account
3. Accept the data access terms for dataset ds633.0

**Get Your RDA API Key:**
1. Log in to NCAR RDA: https://rda.ucar.edu/
2. Go to your profile: https://rda.ucar.edu/#!lfd
3. Copy your API key (under "Authentication")

### 1.2 Configure RDA Credentials

Choose one method:

**Method A: Configuration file (Recommended)**
```bash
# Create/edit ~/.cdsapirc
cat >> ~/.cdsapirc << 'EOF'

[RDA]
email: your_email@example.com
key: your_rda_api_key_here
EOF

chmod 600 ~/.cdsapirc
```

**Method B: Environment variables**
```bash
export RDA_EMAIL='your_email@example.com'
export RDA_KEY='your_rda_api_key_here'

# Make permanent (add to ~/.bashrc)
echo "export RDA_EMAIL='your_email@example.com'" >> ~/.bashrc
echo "export RDA_KEY='your_rda_api_key_here'" >> ~/.bashrc
```

### 1.3 Download ERA5 Data

**Simple Method: Use download_month.sh helper**

```bash
cd /data/mgeorge7/sudhansu_WORK/grb_files

# Download June 2014
./download_month.sh 6

# Download July 2014
./download_month.sh 7

# Download any month/year
./download_month.sh 6 2015   # June 2015
./download_month.sh 8 2016   # August 2016
```

**What happens:**
- Creates directory: `era5_rda_YYYY/month_name/`
- Downloads pressure levels: 150 files (30 days × 5 variables)
- Downloads single levels: 20 files
- Total per month: ~210 GB, ~6 hours download time

**Check download progress:**
```bash
squeue -u $USER                    # Check job status
tail -f era5_rda_download_*.out    # Monitor progress
```

### 1.4 Downloaded Data Structure

```
era5_rda_2014/
├── may/
│   ├── pressure_levels/           # 155 files, ~204 GB
│   │   └── e5.oper.an.pl.128_*.nc
│   └── single_levels/             # 20 files, ~16 GB
│       └── e5.oper.an.sfc.128_*.nc
├── june/
│   ├── pressure_levels/
│   └── single_levels/
└── july/
    ├── pressure_levels/
    └── single_levels/
```

**Variables Downloaded:**
- **Pressure levels (37 levels, 1000-1 hPa):** Geopotential (Z), Temperature (T), U/V wind, Specific humidity (Q)
- **Single levels:** Surface pressure, 2m temperature/dewpoint, 10m winds, SST, soil moisture/temperature, snow depth, etc.

---

## STEP 2: Convert ERA5 NetCDF to WPS Intermediate Format

### 2.1 About era5_to_int

The `era5_to_int.py` script (located in `era5_to_int-main/`) converts ERA5 NetCDF files to WPS intermediate format:
- **Input:** ERA5 NetCDF files from Step 1
- **Output:** WPS intermediate files (GRIB format) that metgrid.exe can read
- **Variables:** Automatically extracts all variables required by WPS/WRF
- **Calculations:** Computes derived variables (e.g., geopotential height, RH, snow depth)

### 2.2 Prepare ERA5 Files for Conversion

Create symbolic links to organize files for era5_to_int:

```bash
cd /data/mgeorge7/sudhansu_WORK/grb_files

# Create working directory
mkdir -p era5_for_wps

# Link files from downloaded month (example: May 2014)
cd era5_for_wps
ln -s ../era5_rda_2014/may/pressure_levels/*.nc .
ln -s ../era5_rda_2014/may/single_levels/*.nc .
```

### 2.3 Run Conversion

**Single timestep (testing):**
```bash
cd /data/mgeorge7/sudhansu_WORK/grb_files/era5_to_int-main/intfiles

python ../era5_to_int.py \
  --path ../../era5_for_wps \
  --isobaric 2014-05-01_00 1
```

**Full month (hourly):**
```bash
python ../era5_to_int.py \
  --path ../../era5_for_wps \
  --isobaric 2014-05-01_00 2014-05-31_23 1
```

**3-hourly (recommended for performance):**
```bash
python ../era5_to_int.py \
  --path ../../era5_for_wps \
  --isobaric 2014-05-01_00 2014-05-31_23 3
```

### 2.4 Batch Conversion with SLURM

For large time periods, use SLURM:

**Edit conversion script:**
```bash
cd /data/mgeorge7/sudhansu_WORK/grb_files/era5_to_int-main
# Edit era5_convert.slurm with your dates and paths
```

**Submit job:**
```bash
sbatch era5_convert.slurm
```

### 2.5 Output Files

WPS intermediate files will be created in `era5_to_int-main/intfiles/`:
```
intfiles/
├── ERA5:2014-05-01_00
├── ERA5:2014-05-01_01
├── ERA5:2014-05-01_02
├── ...
└── ERA5:2014-05-31_23
```

Each file contains all meteorological variables needed by WRF at one timestep.

---

## STEP 3: WPS Processing (metgrid.exe)

### 3.1 Configure WPS

**Copy intermediate files to WPS directory:**
```bash
cd /path/to/WPS
cp /data/mgeorge7/sudhansu_WORK/grb_files/era5_to_int-main/intfiles/ERA5:* .
```

**Edit namelist.wps:**
```fortran
&share
 wrf_core = 'ARW',
 max_dom = 1,
 start_date = '2014-05-01_00:00:00',
 end_date   = '2014-05-31_23:00:00',
 interval_seconds = 3600,  ! Hourly data
 io_form_geogrid = 2,
/

&metgrid
 fg_name = 'ERA5'          ! Prefix of intermediate files
 io_form_metgrid = 2,
/
```

### 3.2 Run metgrid.exe

```bash
cd /path/to/WPS
./metgrid.exe
```

**Output:**
```
met_em.d01.2014-05-01_00:00:00.nc
met_em.d01.2014-05-01_01:00:00.nc
...
met_em.d01.2014-05-31_23:00:00.nc
```

### 3.3 Ready for WRF

The `met_em.*` files are now ready for WRF's `real.exe`:
1. Copy `met_em.*` files to WRF run directory
2. Configure `namelist.input`
3. Run `real.exe` followed by `wrf.exe`

---

## Complete Workflow Example

### Download and Process May-September 2014

**Step 1: Download all months (can run simultaneously)**
```bash
cd /data/mgeorge7/sudhansu_WORK/grb_files

./download_month.sh 5   # May 2014
./download_month.sh 6   # June 2014
./download_month.sh 7   # July 2014
./download_month.sh 8   # August 2014
./download_month.sh 9   # September 2014
```

**Step 2: Convert each month to WPS format**
```bash
# For each month, prepare links and convert
for month in may june july august september; do
  cd /data/mgeorge7/sudhansu_WORK/grb_files
  
  # Create month-specific directory
  mkdir -p era5_for_wps_$month
  cd era5_for_wps_$month
  
  # Link files
  ln -s ../era5_rda_2014/$month/pressure_levels/*.nc .
  ln -s ../era5_rda_2014/$month/single_levels/*.nc .
  
  # Convert (adjust dates for each month)
  cd ../era5_to_int-main/intfiles_$month
  python ../era5_to_int.py \
    --path ../../era5_for_wps_$month \
    --isobaric 2014-05-01_00 2014-05-31_23 1
done
```

**Step 3: Run WPS metgrid.exe**
```bash
cd /path/to/WPS
cp /data/mgeorge7/sudhansu_WORK/grb_files/era5_to_int-main/intfiles_*/ERA5:* .
./metgrid.exe
```

---

## Storage Requirements

### Per Month (30-31 days)

| Component | Size |
|-----------|------|
| ERA5 NetCDF (downloaded) | ~210 GB |
| WPS Intermediate Files | ~50 GB |
| met_em.* Files (after metgrid) | ~30 GB |
| **Total per month** | **~290 GB** |

### Multi-Month Example (May-Sep 2014, 5 months)

- Downloaded ERA5 data: ~1.1 TB
- WPS intermediate files: ~250 GB
- Final met_em files: ~150 GB
- **Total: ~1.5 TB**

---

## Troubleshooting

### Download Issues

**Problem:** Authentication failed
```
Solution: Check ~/.cdsapirc has correct RDA credentials
         Verify: https://rda.ucar.edu/#!lfd
```

**Problem:** Download too slow
```
Solution: Downloads happen at ~30 GB/hour
         Each month takes ~6 hours (normal)
```

### Conversion Issues

**Problem:** Missing variable in NetCDF file
```
Solution: Re-download the missing month
         Check era5_rda logs for failed downloads
```

**Problem:** era5_to_int.py crashes
```
Solution: Check NetCDF files are complete (not corrupted)
         Verify all required pressure/single level files exist
```

### WPS/metgrid Issues

**Problem:** metgrid.exe can't read intermediate files
```
Solution: Check file naming: ERA5:YYYY-MM-DD_HH
         Verify Vtable.ERA5 is correct
```

---

## Additional Resources

- **WRF Forum - ERA5 Usage Guide:** https://forum.mmm.ucar.edu/threads/how-to-use-era5-data-from-copernicus-database.19293/
- **ERA5 Documentation:** https://confluence.ecmwf.int/display/CKB/ERA5
- **NCAR RDA ds633.0:** https://rda.ucar.edu/datasets/ds633.0/
- **WRF Users Guide:** https://www2.mmm.ucar.edu/wrf/users/
- **era5_to_int GitHub:** https://github.com/chrisberr/era5-to-wps

---

## Quick Reference Commands

```bash
# Download June 2014
./download_month.sh 6

# Check download status
squeue -u $USER
tail -f era5_rda_download_*.out

# Convert to WPS format
cd era5_to_int-main/intfiles
python ../era5_to_int.py --path ../../era5_for_wps \
  --isobaric 2014-06-01_00 2014-06-30_23 3

# Run WPS metgrid
cd /path/to/WPS
cp /data/mgeorge7/sudhansu_WORK/grb_files/era5_to_int-main/intfiles/ERA5:* .
./metgrid.exe
```

---

## Contact & Support

For issues with:
- **ERA5 downloads:** Check NCAR RDA status page
- **era5_to_int:** Review original GitHub repository
- **WPS/WRF:** Consult WRF forums and user guide

**Repository:** https://github.com/sudhansu-s-rath/era5_for_WPS

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
