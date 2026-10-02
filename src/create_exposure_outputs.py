from pathlib import Path

import pandas as pd
import pyogrio


INPUT_GPKG = "data/processed/prague_buildings_rp100.gpkg"
INPUT_LAYER = "prague_buildings_rp100"

EXPOSED_GPKG = "data/processed/prague_buildings_rp100_exposed.gpkg"
EXPOSED_LAYER = "rp100_exposed_buildings"

SUMMARY_CSV = "outputs/tables/rp100_exposure_summary.csv"


Path("outputs/tables").mkdir(
    parents=True,
    exist_ok=True
)


print("=" * 60)
print("CREATING RP100 EXPOSURE OUTPUTS")
print("=" * 60)


# ---------------------------------------------------------
# 1. Read building-level RP100 results
# ---------------------------------------------------------

buildings = pyogrio.read_dataframe(
    INPUT_GPKG,
    layer=INPUT_LAYER
)

print(f"Buildings loaded: {len(buildings):,}")


# ---------------------------------------------------------
# 2. Extract buildings with modeled inundation
# ---------------------------------------------------------

exposed = buildings[
    buildings["rp100_inundated"] == True
].copy()

print(
    f"Buildings with modeled inundation: "
    f"{len(exposed):,}"
)


# ---------------------------------------------------------
# 3. Save smaller GIS dataset for QGIS
# ---------------------------------------------------------

pyogrio.write_dataframe(
    exposed,
    EXPOSED_GPKG,
    layer=EXPOSED_LAYER,
    driver="GPKG"
)


# ---------------------------------------------------------
# 4. Build summary table
# ---------------------------------------------------------

summary = (
    buildings
    .groupby(
        "rp100_depth_class",
        observed=True
    )
    .agg(
        building_count=("osm_id", "count"),
        total_footprint_m2=("area_m2", "sum"),
        mean_footprint_m2=("area_m2", "mean")
    )
    .reset_index()
)


summary["percent_of_buildings"] = (
    summary["building_count"]
    / len(buildings)
    * 100
)


# ---------------------------------------------------------
# 5. Save CSV
# ---------------------------------------------------------

summary.to_csv(
    SUMMARY_CSV,
    index=False
)


print()
print("=" * 60)
print("DEPTH CLASS SUMMARY")
print("=" * 60)

print(
    summary.to_string(
        index=False
    )
)


print()
print("=" * 60)
print("OUTPUT FILES")
print("=" * 60)

print(f"Exposed buildings: {EXPOSED_GPKG}")
print(f"Summary CSV:       {SUMMARY_CSV}")