#!/usr/bin/env python3
"""
ERA5 NetCDF Download Script for NCAR RDA (ds633.0)
Downloads ERA5 pressure-level and single-level netCDF files for use with era5_to_int.py

Variables downloaded match those required by era5_to_int.py:
- Pressure levels: Z, Q, T, U, V (37 levels)
- Single levels: SP, MSL, 2T, 2D, 10U, 10V, SST, SKT, LSM, CI, SD, RSN, SWVL1-4, STL1-4
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta


# NCAR RDA dataset configurations
RDA_DATASET = "ds633.0"
# Use THREDDS fileServer for direct HTTP downloads
RDA_BASE_URL = "https://tds.gdex.ucar.edu/thredds/fileServer/files/g/d633000"

# ERA5 variable mappings for NCAR RDA (ECMWF parameter codes)
# Format: 'WPS_NAME': ('ecmwf_param', 'level_type', 'description')
PRESSURE_LEVEL_VARS = {
    'Z': ('129', 'pl', 'Geopotential'),
    'Q': ('133', 'pl', 'Specific humidity'),
    'T': ('130', 'pl', 'Temperature'),
    'U': ('131', 'pl', 'U component of wind'),
    'V': ('132', 'pl', 'V component of wind'),
}

SINGLE_LEVEL_VARS = {
    'SP': ('134', 'sfc', 'Surface pressure'),
    'MSL': ('151', 'sfc', 'Mean sea level pressure'),
    '2T': ('167', 'sfc', '2m temperature'),
    '2D': ('168', 'sfc', '2m dewpoint temperature'),
    '10U': ('165', 'sfc', '10m U wind component'),
    '10V': ('166', 'sfc', '10m V wind component'),
    'SSTK': ('34', 'sfc', 'Sea surface temperature'),
    'SKT': ('235', 'sfc', 'Skin temperature'),
    'LSM': ('172', 'sfc', 'Land-sea mask'),
    'CI': ('31', 'sfc', 'Sea ice cover'),
    'SD': ('141', 'sfc', 'Snow depth'),
    'RSN': ('33', 'sfc', 'Snow density'),
    'SWVL1': ('39', 'sfc', 'Volumetric soil water layer 1'),
    'SWVL2': ('40', 'sfc', 'Volumetric soil water layer 2'),
    'SWVL3': ('41', 'sfc', 'Volumetric soil water layer 3'),
    'SWVL4': ('42', 'sfc', 'Volumetric soil water layer 4'),
    'STL1': ('139', 'sfc', 'Soil temperature level 1'),
    'STL2': ('170', 'sfc', 'Soil temperature level 2'),
    'STL3': ('183', 'sfc', 'Soil temperature level 3'),
    'STL4': ('236', 'sfc', 'Soil temperature level 4'),
}

# Pressure levels (hPa) - 37 levels used by ERA5
PRESSURE_LEVELS = [
    1, 2, 3, 5, 7, 10, 20, 30, 50, 70,
    100, 125, 150, 175, 200, 225, 250, 300, 350, 400,
    450, 500, 550, 600, 650, 700, 750, 775, 800, 825,
    850, 875, 900, 925, 950, 975, 1000
]


def check_credentials():
    """Check if RDA credentials are configured."""
    home = Path.home()
    rdams_file = home / ".cdsapirc"  # Using CDS-style file for consistency
    
    if not rdams_file.exists():
        print("\nERROR: NCAR RDA API key not found!")
        print("\nTo use this script, you need to:")
        print("1. Register for a free account at: https://rda.ucar.edu/")
        print("2. Get your API key from: https://rda.ucar.edu/#!lfd")
        print("3. Create ~/.cdsapirc file with your API key:")
        print("   [RDA]")
        print("   email: your_email@example.com")
        print("   key: your_api_key_from_rda")
        print("")
        print("Alternative: Set environment variables RDA_EMAIL and RDA_KEY")
        return False
    
    print(f"✓ Found RDA credentials at {rdams_file}")
    return True


def build_rda_url(year, month, day, param, level_type):
    """
    Build NCAR RDA THREDDS download URL for ERA5 data.
    
    NOTE: Files contain all 24 hours for a given day (00-23 UTC)
    
    URL pattern for ds633.0 via THREDDS:
    https://tds.gdex.ucar.edu/thredds/fileServer/files/g/d633000/
    e5.oper.an.{level_type}/{YYYYMM}/
    e5.oper.an.{level_type}.128_{param}_{var}.ll025{uv|sc}.{YYYYMMDD}00_{YYYYMMDD}23.nc
    """
    date_str = f"{year}{month:02d}{day:02d}"
    
    # Variable short names and grid type (uv for winds, sc for scalars)
    var_map = {
        '129': ('z', 'sc'),     # Geopotential
        '130': ('t', 'sc'),     # Temperature
        '131': ('u', 'uv'),     # U wind
        '132': ('v', 'uv'),     # V wind
        '133': ('q', 'sc'),     # Specific humidity
        '134': ('sp', 'sc'),    # Surface pressure
        '151': ('msl', 'sc'),   # Mean sea level pressure
        '167': ('2t', 'sc'),    # 2m temperature
        '168': ('2d', 'sc'),    # 2m dewpoint
        '165': ('10u', 'uv'),   # 10m U wind
        '166': ('10v', 'uv'),   # 10m V wind
        '34': ('sst', 'sc'),    # Sea surface temp
        '235': ('skt', 'sc'),   # Skin temperature
        '172': ('lsm', 'sc'),   # Land-sea mask
        '31': ('ci', 'sc'),     # Sea ice cover
        '141': ('sd', 'sc'),    # Snow depth
        '33': ('rsn', 'sc'),    # Snow density
        '39': ('swvl1', 'sc'),  # Soil moisture layer 1
        '40': ('swvl2', 'sc'),  # Soil moisture layer 2
        '41': ('swvl3', 'sc'),  # Soil moisture layer 3
        '42': ('swvl4', 'sc'),  # Soil moisture layer 4
        '139': ('stl1', 'sc'),  # Soil temperature layer 1
        '170': ('stl2', 'sc'),  # Soil temperature layer 2
        '183': ('stl3', 'sc'),  # Soil temperature layer 3
        '236': ('stl4', 'sc'),  # Soil temperature layer 4
    }
    
    var_short, grid_type = var_map.get(param, ('unknown', 'sc'))
    
    # File naming pattern (files contain full day 00-23 UTC)
    filename = f"e5.oper.an.{level_type}.128_{param}_{var_short}.ll025{grid_type}.{date_str}00_{date_str}23.nc"
    
    url = f"{RDA_BASE_URL}/e5.oper.an.{level_type}/{year}{month:02d}/{filename}"
    
    return url, filename


def get_rda_credentials():
    """Get RDA credentials from config file or environment variables."""
    # Try environment variables first
    email = os.environ.get('RDA_EMAIL')
    api_key = os.environ.get('RDA_KEY')
    
    if email and api_key:
        return email, api_key
    
    # Try reading from config file
    home = Path.home()
    config_file = home / ".cdsapirc"
    
    if config_file.exists():
        with open(config_file, 'r') as f:
            lines = f.readlines()
            in_rda_section = False
            for line in lines:
                line = line.strip()
                if line == '[RDA]':
                    in_rda_section = True
                    continue
                if in_rda_section and line.startswith('email:'):
                    email = line.split(':', 1)[1].strip()
                if in_rda_section and line.startswith('key:'):
                    api_key = line.split(':', 1)[1].strip()
    
    return email, api_key


def download_file(url, output_path):
    """Download a file using wget with RDA API key authentication."""
    
    email, api_key = get_rda_credentials()
    
    if not email or not api_key:
        print("  ERROR: RDA credentials not found")
        return False
    
    # Use wget with HTTP basic authentication
    cmd = [
        'wget',
        '--http-user', email,
        '--http-password', api_key,
        '--no-check-certificate',
        '--tries=3',
        '--timeout=300',
        '-O', str(output_path),
        url
    ]
    
    print(f"  Downloading: {output_path.name}")
    print(f"  URL: {url}")
    
    try:
        result = subprocess.run(
            cmd, 
            check=True, 
            stdout=subprocess.DEVNULL,  # Suppress progress output
            stderr=subprocess.PIPE, 
            universal_newlines=True
        )
        
        # Check if file was actually downloaded (not empty or error page)
        if output_path.stat().st_size < 1000:
            print(f"  WARNING: File size suspiciously small ({output_path.stat().st_size} bytes)")
            # Check if it's an HTML error page
            with open(output_path, 'rb') as f:
                header = f.read(100)
                if b'<html' in header.lower() or b'error' in header.lower():
                    print(f"  ERROR: Downloaded file appears to be an error page")
                    output_path.unlink()  # Delete bad file
                    return False
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ERROR downloading {url}")
        if e.stderr:
            # Print full error message
            print(f"  wget stderr:\n{e.stderr}")
        # Clean up failed download
        if output_path.exists():
            output_path.unlink()
        return False
    except Exception as e:
        print(f"  UNEXPECTED ERROR: {type(e).__name__}: {e}")
        if output_path.exists():
            output_path.unlink()
        return False


def download_era5_pressure_levels(year, month, days, out_dir, variables=None):
    """
    Download ERA5 pressure-level netCDF files from NCAR RDA.
    
    NOTE: Each file contains all 24 hours for a given day.
    """
    
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Filter variables if specified
    vars_to_download = PRESSURE_LEVEL_VARS
    if variables:
        vars_to_download = {k: v for k, v in PRESSURE_LEVEL_VARS.items() if k in variables}
    
    print(f"\n{'='*80}")
    print(f"Downloading Pressure Level Variables")
    print(f"{'='*80}")
    print(f"Variables: {', '.join(vars_to_download.keys())}")
    print(f"Period: {year}-{month:02d}, Days: {days}")
    print(f"Note: Each file contains all 24 hours (00-23 UTC)")
    print(f"Output: {out_dir}")
    print(f"{'='*80}\n")
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for day in days:
        for var_name, (param, level_type, desc) in vars_to_download.items():
            
            url, filename = build_rda_url(year, month, day, param, level_type)
            output_file = out_dir / filename
            
            if output_file.exists():
                print(f"  [SKIP] {filename} (already exists)")
                skip_count += 1
                continue
            
            print(f"  [{var_name}] {desc} - {year}-{month:02d}-{day:02d} (24h)")
            
            if download_file(url, output_file):
                success_count += 1
            else:
                fail_count += 1
    
    print(f"\nPressure Levels Summary: {success_count} downloaded, {skip_count} skipped, {fail_count} failed")
    return success_count, skip_count, fail_count


def download_era5_single_levels(year, month, days, out_dir, variables=None):
    """
    Download ERA5 single-level netCDF files from NCAR RDA.
    
    NOTE: Single-level files are organized by MONTH (not day).
    Each file contains all hours for the entire month.
    Format: YYYYMMDD00_YYYYMMDD23 where first DD=01 and last DD=31 (or last day of month)
    """
    
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Filter variables if specified
    vars_to_download = SINGLE_LEVEL_VARS
    if variables:
        vars_to_download = {k: v for k, v in SINGLE_LEVEL_VARS.items() if k in variables}
    
    # Determine last day of month
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    
    print(f"\n{'='*80}")
    print(f"Downloading Single Level Variables")
    print(f"{'='*80}")
    print(f"Variables: {', '.join(vars_to_download.keys())}")
    print(f"Period: {year}-{month:02d} (Full month)")
    print(f"Note: Single-level files contain entire month ({year}{month:02d}01-{year}{month:02d}{last_day})")
    print(f"Output: {out_dir}")
    print(f"{'='*80}\n")
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    # Download one file per variable for the entire month
    for var_name, (param, level_type, desc) in vars_to_download.items():
        # Build monthly filename
        # Format: e5.oper.an.sfc.128_134_sp.ll025sc.2014050100_2014053123.nc
        # Note: param codes must be zero-padded to 3 digits (e.g., 034 not 34)
        var_code, grid_type = param if isinstance(param, tuple) else (param, 'sc')
        var_code_padded = f"{int(var_code):03d}"  # Pad to 3 digits
        
        # Construct filename for monthly data
        start_datetime = f"{year}{month:02d}0100"
        end_datetime = f"{year}{month:02d}{last_day}23"
        filename = f"e5.oper.an.sfc.128_{var_code_padded}_{var_name.lower()}.ll025{grid_type}.{start_datetime}_{end_datetime}.nc"
        
        # Construct URL
        url = f"{RDA_BASE_URL}/e5.oper.an.sfc/{year}{month:02d}/{filename}"
        output_file = out_dir / filename
        
        if output_file.exists():
            print(f"  [SKIP] {filename} (already exists)")
            skip_count += 1
            continue
        
        print(f"  [{var_name}] {desc} - {year}-{month:02d} (monthly)")
        print(f"  Downloading: {filename}")
        
        if download_file(url, output_file):
            success_count += 1
        else:
            fail_count += 1
    
    print(f"\nSingle Levels Summary: {success_count} downloaded, {skip_count} skipped, {fail_count} failed")
    return success_count, skip_count, fail_count


def main():
    parser = argparse.ArgumentParser(
        description="Download ERA5 netCDF files from NCAR RDA (ds633.0) for use with era5_to_int.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download all variables for May 1, 2014 (full day, 24 hours)
  %(prog)s --year 2014 --month 5 --day 1
  
  # Download range of days
  %(prog)s --year 2014 --month 5 --start-day 1 --end-day 5
  
  # Download only specific variables
  %(prog)s --year 2014 --month 5 --day 1 --vars Z,T,U,V
  
  # Skip pressure levels (single level only)
  %(prog)s --year 2014 --month 5 --day 1 --skip-pressure
        """
    )
    
    parser.add_argument("--year", type=int, required=True, help="Year (e.g., 2014)")
    parser.add_argument("--month", type=int, required=True, help="Month (1-12)")
    parser.add_argument("--day", type=int, help="Single day to download (1-31)")
    parser.add_argument("--start-day", type=int, help="Start day for range (1-31)")
    parser.add_argument("--end-day", type=int, help="End day for range (1-31)")
    parser.add_argument("--out-dir", type=str, default="./era5_rda_data", help="Output directory")
    parser.add_argument("--vars", type=str, help="Comma-separated list of variables (e.g., Z,T,U,V)")
    parser.add_argument("--skip-pressure", action="store_true", help="Skip pressure level downloads")
    parser.add_argument("--skip-single", action="store_true", help="Skip single level downloads")
    
    args = parser.parse_args()
    
    # Check credentials
    if not check_credentials():
        sys.exit(1)
    
    # Parse days
    if args.day:
        days = [args.day]
    elif args.start_day and args.end_day:
        days = list(range(args.start_day, args.end_day + 1))
    else:
        print("ERROR: Must specify either --day or both --start-day and --end-day")
        sys.exit(1)
    
    # Parse variables
    variables = None
    if args.vars:
        variables = [v.strip() for v in args.vars.split(',')]
    
    print("="*80)
    print("ERA5 NCAR RDA Download Configuration")
    print("="*80)
    print(f"Dataset:     {RDA_DATASET}")
    print(f"Year:        {args.year}")
    print(f"Month:       {args.month}")
    print(f"Days:        {days}")
    print(f"Note:        Each file contains all 24 hours (00-23 UTC)")
    print(f"Variables:   {variables if variables else 'All'}")
    print(f"Output Dir:  {args.out_dir}")
    print("="*80)
    
    start_time = datetime.now()
    
    pl_stats = (0, 0, 0)
    sl_stats = (0, 0, 0)
    
    # Download pressure levels
    if not args.skip_pressure:
        pl_stats = download_era5_pressure_levels(
            args.year, args.month, days, 
            Path(args.out_dir) / "pressure_levels", 
            variables
        )
    
    # Download single levels
    if not args.skip_single:
        sl_stats = download_era5_single_levels(
            args.year, args.month, days,
            Path(args.out_dir) / "single_levels",
            variables
        )
    
    end_time = datetime.now()
    elapsed = end_time - start_time
    
    print("\n" + "="*80)
    print("DOWNLOAD COMPLETE")
    print("="*80)
    print(f"Total downloaded: {pl_stats[0] + sl_stats[0]}")
    print(f"Total skipped:    {pl_stats[1] + sl_stats[1]}")
    print(f"Total failed:     {pl_stats[2] + sl_stats[2]}")
    print(f"Time elapsed:     {elapsed}")
    print("="*80)
    
    if pl_stats[2] + sl_stats[2] > 0:
        print("\n⚠ Some downloads failed. Check your RDA credentials and network connection.")
        sys.exit(1)


if __name__ == "__main__":
    main()
