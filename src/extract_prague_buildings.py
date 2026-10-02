import pyogrio


INPUT_GPKG = "data/raw/stredocesky.gpkg"
OUTPUT_GPKG = "data/interim/prague_buildings_raw.gpkg"

BUILDING_LAYER = "gis_osm_buildings_a_free"


# Same study area used for the RP100 raster clip
# (min_lon, min_lat, max_lon, max_lat)
PRAGUE_BBOX = (
    14.20,
    49.90,
    14.80,
    50.25
)


print("=" * 60)
print("PRAGUE BUILDING EXTRACTION")
print("=" * 60)


# ---------------------------------------------------------
# 1. Inspect source building layer
# ---------------------------------------------------------

info = pyogrio.read_info(
    INPUT_GPKG,
    layer=BUILDING_LAYER
)

print(f"Source layer: {BUILDING_LAYER}")
print(f"CRS: {info['crs']}")
print(f"Geometry type: {info['geometry_type']}")
print(f"Total source features: {info['features']:,}")

print()
print("Available fields:")

for field in info["fields"]:
    print(f"  - {field}")


# ---------------------------------------------------------
# 2. Read only buildings inside the Prague bounding box
# ---------------------------------------------------------

print()
print("Reading Prague study area...")

buildings = pyogrio.read_dataframe(
    INPUT_GPKG,
    layer=BUILDING_LAYER,
    bbox=PRAGUE_BBOX
)


print()
print("=" * 60)
print("EXTRACTION RESULTS")
print("=" * 60)

print(f"Buildings extracted: {len(buildings):,}")
print(f"CRS: {buildings.crs}")

print()
print("Geometry types:")
print(buildings.geometry.geom_type.value_counts())

print()
print("First columns:")
print(buildings.columns.tolist())


# ---------------------------------------------------------
# 3. Basic geometry QC
# ---------------------------------------------------------

missing_geometry = buildings.geometry.isna().sum()
empty_geometry = buildings.geometry.is_empty.sum()
invalid_geometry = (~buildings.geometry.is_valid).sum()

print()
print("=" * 60)
print("GEOMETRY QC")
print("=" * 60)

print(f"Missing geometries: {missing_geometry:,}")
print(f"Empty geometries: {empty_geometry:,}")
print(f"Invalid geometries: {invalid_geometry:,}")


# ---------------------------------------------------------
# 4. Save extracted dataset
# ---------------------------------------------------------

pyogrio.write_dataframe(
    buildings,
    OUTPUT_GPKG,
    layer="prague_buildings",
    driver="GPKG"
)


print()
print("Extraction completed successfully.")
print(f"Output: {OUTPUT_GPKG}")