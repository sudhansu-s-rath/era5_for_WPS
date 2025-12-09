# ERA5 Download via CDS API (Alternative Method)

This document describes an **alternative** method for downloading ERA5 data using the Copernicus Climate Data Store (CDS) API. 

**Note:** The recommended method is NCAR RDA download (see main README.md). Use this CDS API method only if:
- You prefer GRIB format over NetCDF
- You want to use traditional WRF ungrib.exe workflow
- NCAR RDA is unavailable

---

## Overview

### CDS API vs NCAR RDA Comparison

| Aspect | **NCAR RDA (Recommended)** | **CDS API (This Guide)** |
|--------|---------------------------|--------------------------|
| Format | NetCDF4 | GRIB1/GRIB2 |
| Processing | `era5_to_int.py` → WPS | `ungrib.exe` → WPS |
| Speed | Fast HTTP download | Slower (request queue) |
| Setup | Simple (wget + credentials) | Requires CDS API Python package |
| Variables | Pre-organized by level | Need Vtable configuration |
| Best for | Modern workflows | Traditional WRF users |

---

## Prerequisites

### 1. Register for Copernicus CDS Account

1. Visit: https://cds.climate.copernicus.eu/
2. Click "Register" and create a free account
3. Accept the license terms for ERA5 data

### 2. Get Your CDS API Key

1. Log in to CDS: https://cds.climate.copernicus.eu/
2. Go to your profile: https://cds.climate.copernicus.eu/api-how-to
3. Copy your UID and API key

### 3. Configure CDS API Credentials

**Create ~/.cdsapirc:**
```bash
cat > ~/.cdsapirc << 'EOF'
url: https://cds.climate.copernicus.eu/api/v2
key: YOUR_UID:YOUR_API_KEY
EOF

chmod 600 ~/.cdsapirc
```

Replace `YOUR_UID:YOUR_API_KEY` with your actual credentials (format: `12345:abcdef12-3456-7890-abcd-ef1234567890`).

### 4. Install CDS API Package

```bash
module load mamba/latest
source activate geo_env

pip install cdsapi
```

---

## Download ERA5 Data with CDS API

### Scripts Available

- `download_era5_cds.py` - Python script using CDS API
- `download_era5_cds.slurm` - SLURM batch script for HPC

### Download Single Month

**Edit download_era5_cds.slurm:**
```bash
# Configuration
YEAR="2014"
MONTH="5"
DAYS="1,2,3,...,31"  # Comma-separated
OUT_DIR="/data/mgeorge7/sudhansu_WORK/grb_files/era5_cds_2014_month5"
```

**Submit job:**
```bash
sbatch download_era5_cds.slurm
```

### Interactive Download (Testing)

```bash
module load mamba/latest
source activate geo_env

python download_era5_cds.py \
  --year 2014 \
  --month 5 \
  --days 1,2,3 \
  --out-dir ./test_cds
```

---

## CDS API Request Format

The CDS API downloads ERA5 in GRIB format. Example request:

```python
import cdsapi

c = cdsapi.Client()

c.retrieve(
    'reanalysis-era5-pressure-levels',
    {
        'product_type': 'reanalysis',
        'format': 'grib',
        'variable': [
            'geopotential', 'temperature', 'u_component_of_wind',
            'v_component_of_wind', 'specific_humidity',
        ],
        'pressure_level': [
            '1', '2', '3', '5', '7', '10', '20', '30', '50', '70',
            '100', '150', '200', '250', '300', '400', '500', '600',
            '700', '850', '925', '1000',
        ],
        'year': '2014',
        'month': '05',
        'day': ['01', '02', '03'],
        'time': [
            '00:00', '01:00', '02:00', '03:00', '04:00', '05:00',
            '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
            '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
            '18:00', '19:00', '20:00', '21:00', '22:00', '23:00',
        ],
    },
    'era5_pressure_levels_2014-05.grib'
)
```

---

## Processing CDS GRIB Files for WPS

### Step 1: Download GRIB files (CDS API)

```bash
sbatch download_era5_cds.slurm
```

### Step 2: Use WPS ungrib.exe

**Copy GRIB files to WPS directory:**
```bash
cd /path/to/WPS
cp /data/mgeorge7/sudhansu_WORK/grb_files/era5_cds_2014_month5/*.grib .
```

**Link Vtable for ERA5:**
```bash
ln -sf ungrib/Variable_Tables/Vtable.ERA-interim.pl Vtable
```

**Edit namelist.wps:**
```fortran
&ungrib
 out_format = 'WPS',
 prefix = 'ERA5',
/
```

**Run ungrib.exe:**
```bash
./link_grib.csh era5_*.grib
./ungrib.exe
```

This creates `ERA5:YYYY-MM-DD_HH` intermediate files.

### Step 3: Run metgrid.exe

```bash
./metgrid.exe
```

Produces `met_em.*` files ready for WRF.

---

## Known Issues with CDS API

### 1. Slow Download Speed
- CDS API uses a request queue system
- Large requests can take hours to process
- **Solution:** Use NCAR RDA method (recommended)

### 2. Request Limits
- Maximum data per request: ~120 GB
- Need to split large time periods
- **Solution:** Download month-by-month

### 3. API Timeouts
- Long requests may timeout
- **Solution:** Use smaller chunks (7-10 days)

### 4. GRIB Format Complexity
- Need correct Vtable for ungrib.exe
- Variable names different from NetCDF
- **Solution:** Use tested Vtable.ERA5 or Vtable.ERA-interim.pl

---

## CDS API Expected Sizes & Times

**Per Month (31 days):**
- Pressure levels: ~40 GB (GRIB compressed)
- Single levels: ~15 GB
- **Total: ~55 GB**

**Download Time:**
- Request queue: 10-30 minutes
- Download: 1-3 hours
- **Total: 2-4 hours per month**

---

## Troubleshooting

### Authentication Failed
```
Error: Client has not agreed to the required terms and conditions
```
**Solution:** Accept ERA5 license at https://cds.climate.copernicus.eu/

### Request Timeout
```
Error: Request ID xxxxx timed out
```
**Solution:** Reduce number of days per request (try 10 days instead of 31)

### Missing Variables
```
Error: Variable 'xxx' not found in dataset
```
**Solution:** Check variable names match CDS naming convention

---

## When to Use CDS API

✅ **Use CDS API if:**
- You're familiar with WRF GRIB workflow
- Need specific ERA5 variables not in RDA subset
- Working on a system without wget/curl

❌ **Use NCAR RDA instead if:**
- You want faster downloads
- You're using era5_to_int.py workflow
- You prefer NetCDF format
- You need simplified variable organization

---

## Additional Resources

- **CDS API Documentation:** https://cds.climate.copernicus.eu/api-how-to
- **ERA5 on CDS:** https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-pressure-levels
- **WRF Vtables:** http://www2.mmm.ucar.edu/wrf/users/docs/user_guide_v4/v4.0/users_guide_chap3.html

---

## Return to Main Workflow

For the recommended NCAR RDA workflow, see **README.md** (main documentation).
