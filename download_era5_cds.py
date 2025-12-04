#!/usr/bin/env python3
"""
ERA5 GRIB Download Script
Downloads pressure-level and single-level ERA5 data for a specified month.
"""

import os
import sys
import argparse
import cdsapi
from pathlib import Path
from datetime import datetime


def ensure_dir(path):
    """Create directory if it doesn't exist."""
    Path(path).mkdir(parents=True, exist_ok=True)


def download_era5_pressure_levels(
    year: str,
    month: str,
    days: list,
    times: list,
    out_dir: str,
    area=None,
):
    """
    Download ERA5 pressure-level data (one GRIB per day).

    Parameters
    ----------
    year : str (e.g., "2014")
    month : str (e.g., "05")
    days : list of str (e.g., ["01","02",...])
    times : list of str (e.g., ["00:00",...,"23:00"])
    out_dir : str, directory for output GRIB files
    area : list [N,W,S,E] or None for global
    """
    ensure_dir(out_dir)
    client = cdsapi.Client()

    variables = [
        "divergence",
        "fraction_of_cloud_cover",
        "geopotential",
        "ozone_mass_mixing_ratio",
        "potential_vorticity",
        "relative_humidity",
        "specific_cloud_ice_water_content",
        "specific_cloud_liquid_water_content",
        "specific_humidity",
        "specific_rain_water_content",
        "specific_snow_water_content",
        "temperature",
        "u_component_of_wind",
        "v_component_of_wind",
        "vertical_velocity",
        "vorticity",
    ]

    pressure_levels = [
        "10", "20", "30", "50", "70",
        "100", "125", "150", "175", "200",
        "225", "250", "300", "350", "400",
        "450", "500", "550", "600", "650",
        "700", "750", "775", "800", "825",
        "850", "875", "900", "925", "950",
        "975", "1000",
    ]

    for day in days:
        target = Path(out_dir) / f"era5_pl_{year}{month}{day}.grib"
        if target.exists():
            print(f"[SKIP] {target} already exists", flush=True)
            continue

        print(f"[INFO] Downloading pressure levels for {year}-{month}-{day} -> {target}", flush=True)

        request = {
            "product_type": "reanalysis",
            "format": "grib",
            "variable": variables,
            "pressure_level": pressure_levels,
            "year": year,
            "month": month,
            "day": day,
            "time": times,
        }

        if area is not None:
            request["area"] = area  # [N, W, S, E]

        try:
            client.retrieve(
                "reanalysis-era5-pressure-levels",
                request,
                str(target),
            )
            print(f"[SUCCESS] Downloaded {target}", flush=True)
        except Exception as e:
            print(f"[ERROR] Failed to download {target}: {e}", flush=True)
            sys.exit(1)


def download_era5_single_levels(
    year: str,
    month: str,
    days: list,
    times: list,
    out_dir: str,
    area=None,
):
    """
    Download ERA5 single-level data (one GRIB per day).

    Parameters
    ----------
    year : str
    month : str
    days : list of str
    times : list of str
    out_dir : str
    area : list [N,W,S,E] or None
    """
    ensure_dir(out_dir)
    client = cdsapi.Client()

    variables = [
        "10m_u_component_of_wind",
        "10m_v_component_of_wind",
        "2m_dewpoint_temperature",
        "2m_temperature",
        "land_sea_mask",
        "mean_sea_level_pressure",
        "sea_ice_cover",
        "sea_surface_temperature",
        "skin_temperature",
        "snow_density",
        "snow_depth",
        "soil_temperature_level_1",
        "soil_temperature_level_2",
        "soil_temperature_level_3",
        "soil_temperature_level_4",
        "surface_pressure",
        "volumetric_soil_water_layer_1",
        "volumetric_soil_water_layer_2",
        "volumetric_soil_water_layer_3",
        "volumetric_soil_water_layer_4",
    ]

    for day in days:
        target = Path(out_dir) / f"era5_sl_{year}{month}{day}.grib"
        if target.exists():
            print(f"[SKIP] {target} already exists", flush=True)
            continue

        print(f"[INFO] Downloading single levels for {year}-{month}-{day} -> {target}", flush=True)

        request = {
            "product_type": "reanalysis",
            "format": "grib",
            "variable": variables,
            "year": year,
            "month": month,
            "day": day,
            "time": times,
        }

        if area is not None:
            request["area"] = area  # [N, W, S, E]

        try:
            client.retrieve(
                "reanalysis-era5-single-levels",
                request,
                str(target),
            )
            print(f"[SUCCESS] Downloaded {target}", flush=True)
        except Exception as e:
            print(f"[ERROR] Failed to download {target}: {e}", flush=True)
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Download ERA5 GRIB data for a specified month"
    )
    parser.add_argument("--year", type=str, required=True, help="Year (e.g., 2014)")
    parser.add_argument("--month", type=str, required=True, help="Month (e.g., 05)")
    parser.add_argument(
        "--start-day", type=int, default=1, help="Starting day of month (default: 1)"
    )
    parser.add_argument(
        "--end-day", type=int, default=31, help="Ending day of month (default: 31)"
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="/data/mgeorge7/sudhansu_WORK/grb_files/era5_data",
        help="Output directory",
    )
    parser.add_argument(
        "--area",
        type=str,
        default=None,
        help="Geographic subset: N,W,S,E (e.g., '40,-120,25,-105')",
    )
    parser.add_argument(
        "--skip-pressure",
        action="store_true",
        help="Skip pressure level download",
    )
    parser.add_argument(
        "--skip-single",
        action="store_true",
        help="Skip single level download",
    )

    args = parser.parse_args()

    # Validate inputs
    year = args.year
    month = args.month.zfill(2)
    
    # Generate day list
    days = [f"{d:02d}" for d in range(args.start_day, args.end_day + 1)]
    
    # All hours (00:00–23:00)
    times = [f"{h:02d}:00" for h in range(24)]
    
    # Parse area if provided
    area = None
    if args.area:
        try:
            area = [float(x) for x in args.area.split(",")]
            if len(area) != 4:
                raise ValueError("Area must have 4 values: N,W,S,E")
            print(f"[INFO] Using geographic subset: {area}", flush=True)
        except Exception as e:
            print(f"[ERROR] Invalid area format: {e}", flush=True)
            sys.exit(1)

    # Create output directories
    pl_out_dir = os.path.join(args.out_dir, "p_levels")
    sl_out_dir = os.path.join(args.out_dir, "s_levels")

    print("=" * 80, flush=True)
    print(f"ERA5 Download Configuration", flush=True)
    print("=" * 80, flush=True)
    print(f"Year:        {year}", flush=True)
    print(f"Month:       {month}", flush=True)
    print(f"Days:        {args.start_day} to {args.end_day} ({len(days)} days)", flush=True)
    print(f"Output Dir:  {args.out_dir}", flush=True)
    print(f"Area:        {'Global' if area is None else area}", flush=True)
    print("=" * 80, flush=True)

    start_time = datetime.now()

    # Download pressure levels
    if not args.skip_pressure:
        print(f"\n[INFO] Starting pressure level downloads...", flush=True)
        download_era5_pressure_levels(
            year=year,
            month=month,
            days=days,
            times=times,
            out_dir=pl_out_dir,
            area=area,
        )
    else:
        print(f"\n[INFO] Skipping pressure level downloads", flush=True)

    # Download single levels
    if not args.skip_single:
        print(f"\n[INFO] Starting single level downloads...", flush=True)
        download_era5_single_levels(
            year=year,
            month=month,
            days=days,
            times=times,
            out_dir=sl_out_dir,
            area=area,
        )
    else:
        print(f"\n[INFO] Skipping single level downloads", flush=True)

    end_time = datetime.now()
    elapsed = end_time - start_time

    print("=" * 80, flush=True)
    print(f"[COMPLETE] All downloads finished", flush=True)
    print(f"Total time: {elapsed}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()
