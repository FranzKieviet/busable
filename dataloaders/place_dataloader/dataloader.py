import json
import math
import sys
from datetime import datetime
from pathlib import Path
import duckdb
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from query_config import get_place_query
from dataloaders.lib.mongodb import upload_data

# Coordinates around Sather Gate (1km Bounding Box)
XMIN, YMIN = -122.2695, 37.8603
XMAX, YMAX = -122.2495, 37.8803

con = duckdb.connect()

# Install and load spatial & httpfs extensions for DuckDB
con.sql("INSTALL spatial; LOAD spatial;")
con.sql("INSTALL httpfs; LOAD httpfs;")
con.sql("SET s3_region='us-west-2';")

def process_places():
    query = get_place_query(XMIN, XMAX, YMIN, YMAX)

    print("Querying Overture Maps Parquet on AWS S3...")

    # 1. Execute Query and create DataFrame
    df = con.sql(query).df()

    print(f"\nExtracted {len(df)} places!")

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

if __name__ == "__main__":
    #Create new data version:
    data_version = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Simulating your routing/stop dictionaries
    places = process_places()

    # Run the upload
    upload_data(data=places, collection_name="places" + "_" + data_version)
    print(f"\nSaved valid JSON array with {len(places)} records")


def main():
    """Programmatic entrypoint for invoking the places dataloader (e.g. from Lambda router)."""
    data_version = datetime.now().strftime("%Y%m%d_%H%M%S")
    places = process_places()
    upload_data(data=places, collection_name="places" + "_" + data_version)
    print(f"Saved places collection: places_{data_version} ({len(places)} records)")
    return {"collection": f"places_{data_version}", "count": len(places)}