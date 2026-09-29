import rasterio
import numpy as np

raster_path = "data/raw/Europe_RP100_filled_depth.tif"

with rasterio.open(raster_path) as src:
    print("Raster opened successfully.")
    print()

    print("CRS:", src.crs)
    print("Width:", src.width)
    print("Height:", src.height)
    print("Resolution:", src.res)
    print("Bounds:", src.bounds)
    print("Data type:", src.dtypes[0])
    print("NoData:", src.nodata)

    data = src.read(1)

    valid_data = data[data != src.nodata]

    print("Minimum flood depth:", valid_data.min())
    print("Maximum flood depth:", valid_data.max())
    print("Valid pixel count:", valid_data.size)
    print("Total pixel count:", data.size)
    print(
        "Valid pixel percent:",
        round((valid_data.size / data.size) * 100, 3),
        "%"
    )