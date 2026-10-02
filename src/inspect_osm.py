import pyogrio


gpkg_path = "data/raw/stredocesky.gpkg"

layers = pyogrio.list_layers(gpkg_path)

print("=" * 60)
print("GEOPACKAGE LAYERS")
print("=" * 60)

for layer in layers:
    print(layer)