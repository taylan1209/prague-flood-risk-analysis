import numpy as np
import pandas as pd
import pyogrio
import rasterio


BUILDINGS_GPKG = "data/processed/prague_buildings.gpkg"
BUILDINGS_LAYER = "prague_buildings"

FLOOD_RASTER = "data/interim/prague_rp100_depth.tif"

OUTPUT_GPKG = "data/processed/prague_buildings_rp100.gpkg"
OUTPUT_LAYER = "prague_buildings_rp100"


print("=" * 60)
print("RP100 FLOOD DEPTH SAMPLING")
print("=" * 60)


# ---------------------------------------------------------
# 1. Load processed building dataset
# ---------------------------------------------------------

buildings = pyogrio.read_dataframe(
    BUILDINGS_GPKG,
    layer=BUILDINGS_LAYER
)

print(f"Buildings loaded: {len(buildings):,}")
print(f"Building CRS: {buildings.crs}")


# ---------------------------------------------------------
# 2. Check required coordinate fields
# ---------------------------------------------------------

required_fields = ["longitude", "latitude"]

for field in required_fields:
    if field not in buildings.columns:
        raise ValueError(
            f"Required field missing: {field}"
        )


# ---------------------------------------------------------
# 3. Prepare output array
#
# NaN initially means:
# no valid modeled flood depth was returned.
# ---------------------------------------------------------

depths = np.full(
    len(buildings),
    np.nan,
    dtype="float32"
)


# ---------------------------------------------------------
# 4. Sample RP100 raster
# ---------------------------------------------------------

with rasterio.open(FLOOD_RASTER) as src:

    print(f"Flood raster CRS: {src.crs}")
    print(f"Raster NoData: {src.nodata}")

    if str(src.crs) != "EPSG:4326":
        raise ValueError(
            "Flood raster must be EPSG:4326 "
            "for longitude/latitude sampling."
        )

    coordinates = zip(
        buildings["longitude"].to_numpy(),
        buildings["latitude"].to_numpy()
    )

    print()
    print("Sampling flood raster...")

    for i, value in enumerate(
        src.sample(
            coordinates,
            indexes=1,
            masked=True
        )
    ):

        pixel_value = value[0]

        # Skip masked / NoData pixels
        if np.ma.is_masked(pixel_value):
            continue

        pixel_value = float(pixel_value)

        # Skip NaN / Inf
        if not np.isfinite(pixel_value):
            continue

        # Skip explicit NoData
        if (
            src.nodata is not None
            and np.isclose(pixel_value, src.nodata)
        ):
            continue

        depths[i] = pixel_value


# ---------------------------------------------------------
# 5. Store raw sampled depth
# ---------------------------------------------------------

buildings["rp100_depth_raw_m"] = depths


# ---------------------------------------------------------
# 6. Distinguish modeled inundation from NoData
#
# In this first-pass portfolio analysis, raster cells
# without a positive modeled flood depth are treated as
# "no modeled inundation" rather than claiming
# that flooding is impossible.
# ---------------------------------------------------------

buildings["rp100_inundated"] = (
    np.isfinite(buildings["rp100_depth_raw_m"])
    & (buildings["rp100_depth_raw_m"] > 0)
)


# Use 0 for analysis/summary where no inundation was modeled
buildings["rp100_depth_m"] = (
    buildings["rp100_depth_raw_m"]
    .fillna(0.0)
)


# ---------------------------------------------------------
# 7. Create hazard-depth classes
# ---------------------------------------------------------

buildings["rp100_depth_class"] = pd.cut(
    buildings["rp100_depth_m"],
    bins=[
        -0.001,
        0.0,
        0.5,
        1.0,
        2.0,
        3.0,
        np.inf
    ],
    labels=[
        "No modeled inundation",
        "0.10-0.50 m",
        "0.50-1.00 m",
        "1.00-2.00 m",
        "2.00-3.00 m",
        ">3.00 m"
    ],
    include_lowest=True
)


# ---------------------------------------------------------
# 8. Summary statistics
# ---------------------------------------------------------

total_buildings = len(buildings)

inundated_buildings = int(
    buildings["rp100_inundated"].sum()
)

inundated_percent = (
    inundated_buildings
    / total_buildings
    * 100
)


print()
print("=" * 60)
print("RP100 EXPOSURE SUMMARY")
print("=" * 60)

print(
    f"Total buildings: "
    f"{total_buildings:,}"
)

print(
    f"Buildings with modeled inundation: "
    f"{inundated_buildings:,}"
)

print(
    f"Inundated buildings: "
    f"{inundated_percent:.2f} %"
)


if inundated_buildings > 0:

    flooded_depths = buildings.loc[
        buildings["rp100_inundated"],
        "rp100_depth_m"
    ]

    print(
        f"Mean depth among inundated buildings: "
        f"{flooded_depths.mean():.2f} m"
    )

    print(
        f"Median depth among inundated buildings: "
        f"{flooded_depths.median():.2f} m"
    )

    print(
        f"Maximum sampled depth: "
        f"{flooded_depths.max():.2f} m"
    )


print()
print("Depth classes:")
print(
    buildings["rp100_depth_class"]
    .value_counts()
    .sort_index()
)


# ---------------------------------------------------------
# 9. Save result
# ---------------------------------------------------------

pyogrio.write_dataframe(
    buildings,
    OUTPUT_GPKG,
    layer=OUTPUT_LAYER,
    driver="GPKG"
)


print()
print("=" * 60)
print("SAMPLING COMPLETED")
print("=" * 60)

print(f"Output: {OUTPUT_GPKG}")
print(f"Buildings saved: {len(buildings):,}")