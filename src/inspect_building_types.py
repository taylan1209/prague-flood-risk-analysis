import pandas as pd
import pyogrio


INPUT_GPKG = "data/processed/prague_buildings_rp100.gpkg"
INPUT_LAYER = "prague_buildings_rp100"

OUTPUT_ALL = "outputs/tables/osm_building_types_all.csv"
OUTPUT_EXPOSED = "outputs/tables/osm_building_types_exposed.csv"


print("=" * 70)
print("OSM BUILDING TYPE INSPECTION")
print("=" * 70)


buildings = pyogrio.read_dataframe(
    INPUT_GPKG,
    layer=INPUT_LAYER
)


print(f"\nTotal buildings: {len(buildings):,}")

print("\nAvailable columns:")
print(buildings.columns.tolist())


# ---------------------------------------------------------
# Clean type field
# ---------------------------------------------------------

buildings["type_clean"] = (
    buildings["type"]
    .fillna("<missing>")
    .astype(str)
    .str.strip()
    .replace("", "<missing>")
)


# ---------------------------------------------------------
# All buildings
# ---------------------------------------------------------

all_counts = (
    buildings["type_clean"]
    .value_counts(dropna=False)
    .rename_axis("building_type")
    .reset_index(name="building_count")
)

all_counts["percent"] = (
    all_counts["building_count"]
    / len(buildings)
    * 100
)


print()
print("=" * 70)
print("TOP BUILDING TYPES — FULL STUDY AREA")
print("=" * 70)

print(
    all_counts
    .head(50)
    .to_string(index=False)
)


# ---------------------------------------------------------
# Exposed buildings only
# ---------------------------------------------------------

exposed = buildings[
    buildings["rp100_inundated"] == True
].copy()


exposed_counts = (
    exposed["type_clean"]
    .value_counts(dropna=False)
    .rename_axis("building_type")
    .reset_index(name="building_count")
)

exposed_counts["percent_of_exposed"] = (
    exposed_counts["building_count"]
    / len(exposed)
    * 100
)


print()
print("=" * 70)
print("TOP BUILDING TYPES — RP100 EXPOSED BUILDINGS")
print("=" * 70)

print(f"Exposed buildings: {len(exposed):,}")

print(
    exposed_counts
    .head(50)
    .to_string(index=False)
)


# ---------------------------------------------------------
# fclass inspection
# ---------------------------------------------------------

if "fclass" in buildings.columns:

    print()
    print("=" * 70)
    print("FCLASS DISTRIBUTION")
    print("=" * 70)

    print(
        buildings["fclass"]
        .fillna("<missing>")
        .value_counts()
        .head(30)
    )


# ---------------------------------------------------------
# Save tables
# ---------------------------------------------------------

all_counts.to_csv(
    OUTPUT_ALL,
    index=False
)

exposed_counts.to_csv(
    OUTPUT_EXPOSED,
    index=False
)


print()
print("=" * 70)
print("OUTPUTS")
print("=" * 70)

print(f"All building types:     {OUTPUT_ALL}")
print(f"Exposed building types: {OUTPUT_EXPOSED}")