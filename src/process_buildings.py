import geopandas as gpd
import pyogrio


INPUT_GPKG = "data/interim/prague_buildings_raw.gpkg"
OUTPUT_GPKG = "data/processed/prague_buildings.gpkg"

INPUT_LAYER = "prague_buildings"
OUTPUT_LAYER = "prague_buildings"


print("=" * 60)
print("PRAGUE BUILDING PROCESSING")
print("=" * 60)


# ---------------------------------------------------------
# 1. Read extracted buildings
# ---------------------------------------------------------

buildings = pyogrio.read_dataframe(
    INPUT_GPKG,
    layer=INPUT_LAYER
)

print(f"Buildings loaded: {len(buildings):,}")
print(f"Source CRS: {buildings.crs}")


# ---------------------------------------------------------
# 2. Keep original WGS84 coordinates
# ---------------------------------------------------------

# Representative point is guaranteed to fall inside geometry
representative_points = buildings.geometry.representative_point()

buildings["longitude"] = representative_points.x
buildings["latitude"] = representative_points.y


# ---------------------------------------------------------
# 3. Reproject to Czech national metric CRS
# ---------------------------------------------------------

buildings_metric = buildings.to_crs(
    epsg=5514
)

print(f"Metric CRS: {buildings_metric.crs}")


# ---------------------------------------------------------
# 4. Calculate building footprint area
# ---------------------------------------------------------

buildings_metric["area_m2"] = (
    buildings_metric.geometry.area
)


# ---------------------------------------------------------
# 5. Basic area quality checks
# ---------------------------------------------------------

print()
print("=" * 60)
print("BUILDING AREA STATISTICS")
print("=" * 60)

print(
    f"Minimum area: "
    f"{buildings_metric['area_m2'].min():.2f} m²"
)

print(
    f"Maximum area: "
    f"{buildings_metric['area_m2'].max():,.2f} m²"
)

print(
    f"Median area: "
    f"{buildings_metric['area_m2'].median():.2f} m²"
)

print(
    f"Mean area: "
    f"{buildings_metric['area_m2'].mean():.2f} m²"
)


# ---------------------------------------------------------
# 6. Flag suspicious footprint sizes
# ---------------------------------------------------------

buildings_metric["area_qc"] = "OK"

buildings_metric.loc[
    buildings_metric["area_m2"] < 10,
    "area_qc"
] = "VERY_SMALL"

buildings_metric.loc[
    buildings_metric["area_m2"] > 100000,
    "area_qc"
] = "VERY_LARGE"


print()
print("Area QC:")
print(
    buildings_metric["area_qc"]
    .value_counts()
)


# ---------------------------------------------------------
# 7. Inspect building types
# ---------------------------------------------------------

if "type" in buildings_metric.columns:

    print()
    print("=" * 60)
    print("TOP BUILDING TYPES")
    print("=" * 60)

    print(
        buildings_metric["type"]
        .fillna("unknown")
        .value_counts()
        .head(20)
    )


# ---------------------------------------------------------
# 8. Save processed building dataset
# ---------------------------------------------------------

pyogrio.write_dataframe(
    buildings_metric,
    OUTPUT_GPKG,
    layer=OUTPUT_LAYER,
    driver="GPKG"
)


print()
print("=" * 60)
print("PROCESSING COMPLETED")
print("=" * 60)

print(f"Output: {OUTPUT_GPKG}")
print(f"Buildings saved: {len(buildings_metric):,}")