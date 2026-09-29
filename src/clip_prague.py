import rasterio
import numpy as np

from rasterio.windows import from_bounds
from rasterio.windows import transform as window_transform


INPUT_RASTER = "data/raw/Europe_RP100_filled_depth.tif"
OUTPUT_RASTER = "data/interim/prague_rp100_depth.tif"


# Prague study area bounding box
# CRS: EPSG:4326
LEFT = 14.20
BOTTOM = 49.90
RIGHT = 14.80
TOP = 50.25


with rasterio.open(INPUT_RASTER) as src:

    print("=" * 60)
    print("PRAGUE RP100 RASTER CLIP")
    print("=" * 60)

    print(f"Input CRS: {src.crs}")

    # Convert geographic bounds to raster pixel window
    window = from_bounds(
        LEFT,
        BOTTOM,
        RIGHT,
        TOP,
        transform=src.transform
    )

    # Align window to whole raster pixels
    window = window.round_offsets().round_lengths()

    # Read only the Prague-area window
    data = src.read(
        1,
        window=window
    )

    # Convert NaN / Inf values to the raster NoData value
    data = np.where(
        np.isfinite(data),
        data,
        src.nodata
    ).astype(src.dtypes[0])

    # Calculate the geotransform of the clipped raster
    new_transform = window_transform(
        window,
        src.transform
    )

    # Copy source metadata
    profile = src.profile.copy()

    profile.update(
        height=data.shape[0],
        width=data.shape[1],
        transform=new_transform,
        count=1,
        compress="deflate"
    )

    # Write clipped raster
    with rasterio.open(
        OUTPUT_RASTER,
        "w",
        **profile
    ) as dst:
        dst.write(data, 1)


print()
print("Clip completed successfully.")
print(f"Output: {OUTPUT_RASTER}")
print(f"Raster size: {data.shape[1]} x {data.shape[0]} pixels")