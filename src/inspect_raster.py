import rasterio
import numpy as np

raster_path = "data/raw/Europe_RP100_filled_depth.tif"

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

    print()
    print("Scanning raster blocks...")

    for _, window in src.block_windows(1):

        # Read only one small block at a time
        block = src.read(
            1,
            window=window,
            masked=True
        )

        # Remove NoData values
        values = block.compressed()

        # Remove NaN and infinite values
        values = values[np.isfinite(values)]

        if values.size == 0:
            continue

        valid_pixel_count += values.size

        block_min = values.min()
        block_max = values.max()

        if block_min < min_value:
            min_value = block_min

        if block_max > max_value:
            max_value = block_max

    valid_percent = (
        valid_pixel_count / total_pixels
    ) * 100

    print()
    print("=" * 60)
    print("VALID DATA STATISTICS")
    print("=" * 60)

    print(f"Minimum flood depth: {min_value:.3f} m")
    print(f"Maximum flood depth: {max_value:.3f} m")

    print(
        f"Valid pixel count: "
        f"{valid_pixel_count:,}"
    )

    print(
        f"Total pixel count: "
        f"{total_pixels:,}"
    )

    print(
        f"Valid pixel percent: "
        f"{valid_percent:.3f} %"
    )