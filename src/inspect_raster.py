import sys
import rasterio
import numpy as np


if len(sys.argv) < 2:
    print("Usage: python src/inspect_raster.py <raster_path>")
    sys.exit(1)


raster_path = sys.argv[1]


with rasterio.open(raster_path) as src:

    print("=" * 60)
    print("RASTER INFORMATION")
    print("=" * 60)

    print(f"File: {raster_path}")
    print(f"CRS: {src.crs}")
    print(f"Width: {src.width}")
    print(f"Height: {src.height}")
    print(f"Resolution: {src.res}")
    print(f"Bounds: {src.bounds}")
    print(f"Data type: {src.dtypes[0]}")
    print(f"NoData: {src.nodata}")

    total_pixels = src.width * src.height

    valid_pixel_count = 0
    min_value = np.inf
    max_value = -np.inf

    for _, window in src.block_windows(1):

        block = src.read(
            1,
            window=window,
            masked=True
        )

        values = block.compressed()
        values = values[np.isfinite(values)]

        if values.size == 0:
            continue

        valid_pixel_count += values.size

        min_value = min(
            min_value,
            values.min()
        )

        max_value = max(
            max_value,
            values.max()
        )

    valid_percent = (
        valid_pixel_count / total_pixels
    ) * 100

    print()
    print("=" * 60)
    print("VALID DATA STATISTICS")
    print("=" * 60)

    print(f"Minimum flood depth: {min_value:.3f} m")
    print(f"Maximum flood depth: {max_value:.3f} m")
    print(f"Valid pixel count: {valid_pixel_count:,}")
    print(f"Total pixel count: {total_pixels:,}")
    print(f"Valid pixel percent: {valid_percent:.3f} %")