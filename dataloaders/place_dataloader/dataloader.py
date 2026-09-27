import json
import math
import os
import sys
import time
from datetime import datetime
from pathlib import Path
import boto3
import duckdb
import numpy as np
from botocore import UNSIGNED
from botocore.config import Config

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from .query_config import get_place_query
from lib.mongodb import load_region_places

# Each region is loaded by dropping {region}.txt into the triggers folder, and is swapped in on its own.
# A region is one or more (xmin, ymin, xmax, ymax) boxes, queried one after another in the same Lambda run.
# Boxes must not overlap, or places on the overlap are loaded twice.
# If a region's run gets close to the 15 minute Lambda limit (see the timings in the logs), split it into
# two regions with their own trigger files rather than adding boxes, since each region runs separately.
PLACE_REGIONS = {
    # Nine Bay Area counties, Sonoma/Napa in the north to Santa Clara in the south (also covers Sacramento and Stockton)
    "bay-area": [
        (-123.55, 36.89, -121.20, 38.87),
    ],
    "central": [
        # Monterey and Fresno south to San Luis Obispo and Bakersfield
        (-122.00, 34.80, -115.60, 36.89),
        # Central Valley and Sierra east of the Bay Area box: Modesto, Merced, Yosemite
        (-121.20, 36.89, -118.00, 38.87),
    ],
    # Santa Barbara to San Diego, east to the Arizona border
    "socal": [
        (-121.00, 32.50, -114.10, 34.80),
    ],
}

OVERTURE_BUCKET = "overturemaps-us-west-2"
OVERTURE_REGION = "us-west-2"


def _connect():
    """Create a DuckDB connection with spatial + httpfs loaded.

    In the Lambda image, extensions are pre-installed at build time into
    DUCKDB_EXTENSION_DIR (see Dockerfile), since Lambda has no HOME and only /tmp
    is writable. Locally, fall back to DuckDB's default dirs and install on demand.
    """
    extension_dir = os.environ.get("DUCKDB_EXTENSION_DIR")
    if extension_dir:
        con = duckdb.connect(config={
            "extension_directory": extension_dir,
            "home_directory": "/tmp",
            "temp_directory": "/tmp/duckdb_tmp",
            "autoinstall_known_extensions": False,
        })
    else:
        con = duckdb.connect()
        con.sql("INSTALL spatial; INSTALL httpfs;")

    con.sql("LOAD spatial; LOAD httpfs;")
    # Overture is a public bucket, so read it anonymously. Without this, DuckDB signs requests
    # with the Lambda role's credentials from the environment, which the bucket rejects (403).
    con.sql(f"""
        CREATE SECRET overture (
            TYPE s3, KEY_ID '', SECRET '', SESSION_TOKEN '',
            REGION '{OVERTURE_REGION}', SCOPE 's3://{OVERTURE_BUCKET}'
        )
    """)
    return con


def _latest_overture_release():
    """Overture only keeps its most recent releases, so look up the newest one rather than pinning it."""
    s3 = boto3.client("s3", region_name=OVERTURE_REGION, config=Config(signature_version=UNSIGNED))
    resp = s3.list_objects_v2(Bucket=OVERTURE_BUCKET, Prefix="release/", Delimiter="/")
    releases = [p["Prefix"].split("/")[1] for p in resp.get("CommonPrefixes", [])]
    if not releases:
        raise RuntimeError(f"No Overture releases found in s3://{OVERTURE_BUCKET}/release/")
    return max(releases)


def process_places(region):
    boxes = PLACE_REGIONS[region]
    con = _connect()
    release = _latest_overture_release()
    print(f"Querying Overture Maps release {release} on AWS S3 for region {region} ({len(boxes)} boxes)...")

    places = []
    for xmin, ymin, xmax, ymax in boxes:
        started = time.monotonic()
        places.extend(_process_box(con, release, xmin, ymin, xmax, ymax))
        print(f"Box ({xmin}, {ymin}, {xmax}, {ymax}): {len(places)} places so far, took {time.monotonic() - started:.0f}s")

    return places


def _process_box(con, release, xmin, ymin, xmax, ymax):
    query = get_place_query(release, xmin, xmax, ymin, ymax)

    # 1. Execute Query and create DataFrame
    df = con.sql(query).df()
    print(f"Extracted {len(df)} places from Overture S3")

    # 2. Replace NaN / NaT values across the entire DataFrame with None (JSON null)
    df = df.replace({np.nan: None})

    # Helper to safely clean individual fields
    def safe_float(val, default=0.0):
        if val is None:
            return default
        try:
            f = float(val)
            return default if math.isnan(f) else f
        except (ValueError, TypeError):
            return default

    # 3. Build clean dictionary list
    places = []
    for _, row in df.iterrows():
        location_geojson = json.loads(row["geojson_geometry"])
        
        places.append({
            "id": row["id"],
            "name": row["name"],
            "category": row["category"],
            "confidence": safe_float(row["confidence"]),
            "brand": row["brand"] if row["brand"] is not None else None,
            "website": row["website"] if row["website"] is not None else None,
            "popularity_score": round(safe_float(row["popularity_score"]), 2),
            "location": location_geojson  # {"type": "Point", "coordinates": [lon, lat]}
        })

    return places

def main(region):
    """Programmatic entrypoint for invoking the places dataloader for one region (e.g. from Lambda router)."""
    if region not in PLACE_REGIONS:
        raise ValueError(f"Unknown places region '{region}'. Known regions: {', '.join(PLACE_REGIONS)}")

    started = time.monotonic()
    load_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    places = process_places(region)

    # Load inactive, then swap it in for this region's current places
    load_region_places(region=region, places=places, load_id=load_id)
    print(f"Loaded {len(places)} places for region {region} in {time.monotonic() - started:.0f}s")

    return {"region": region, "load_id": load_id, "count": len(places)}

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "bay-area")
