import json
import math
import os
import sys
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
from lib.mongodb import upload_data

# Coordinates around Sather Gate (1km Bounding Box)
XMIN, YMIN = -122.2695, 37.8603
XMAX, YMAX = -122.2495, 37.8803

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


def process_places():
    con = _connect()
    release = _latest_overture_release()
    query = get_place_query(release, XMIN, XMAX, YMIN, YMAX)

    print(f"Querying Overture Maps release {release} on AWS S3...")

    # 1. Execute Query and create DataFrame
    try:
        df = con.sql(query).df()
        print(f"\nExtracted {len(df)} places from Overture S3!")

        # 2. Replace NaN / NaT values across the entire DataFrame with None (JSON null)
        df = df.replace({np.nan: None})
    except Exception as e:
        # Fallback: try loading a local sample JSON file included in the repo
        local_sample = Path(__file__).parent / "overture_berkeley_places.json"
        if local_sample.exists():
            print(f"Failed to query Overture S3 ({e}). Falling back to local sample {local_sample}")
            import json as _json
            with local_sample.open(encoding="utf-8") as fh:
                places_list = _json.load(fh)
            print(f"Loaded {len(places_list)} places from local sample")
            return places_list
        else:
            raise

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

def main():
    """Programmatic entrypoint for invoking the places dataloader (e.g. from Lambda router)."""
    
    data_version = datetime.now().strftime("%Y%m%d_%H%M%S")
    places = process_places()
    
    upload_data(data=places, collection_name="places" + "_" + data_version)
    print(f"Saved places collection: places_{data_version} ({len(places)} records)")

    return {"collection": f"places_{data_version}", "count": len(places)}

if __name__ == "__main__":
    main()