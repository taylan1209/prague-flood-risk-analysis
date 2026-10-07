import pyogrio


INPUT_GPKG = "data/processed/prague_buildings_rp100.gpkg"
INPUT_LAYER = "prague_buildings_rp100"

OUTPUT_GPKG = "data/processed/prague_buildings_classified.gpkg"
OUTPUT_LAYER = "prague_buildings_classified"


RESIDENTIAL_TYPES = {
    "house",
    "residential",
    "detached",
    "apartments",
    "bungalow",
    "dormitory",
}

COMMERCIAL_TYPES = {
    "commercial",
    "retail",
    "office",
    "hotel",
    "kiosk",
}

INDUSTRIAL_TYPES = {
    "industrial",
    "warehouse",
    "manufacture",
}


print("=" * 70)
print("BUILDING ASSET CLASSIFICATION")
print("=" * 70)


buildings = pyogrio.read_dataframe(
    INPUT_GPKG,
    layer=INPUT_LAYER
)


buildings["type_clean"] = (
    buildings["type"]
    .fillna("<missing>")
    .astype(str)
    .str.strip()
    .str.lower()
)


def classify_asset(building_type):

    if building_type in RESIDENTIAL_TYPES:
        return "Residential"

    if building_type in COMMERCIAL_TYPES:
        return "Commercial"

    if building_type in INDUSTRIAL_TYPES:
        return "Industrial"

    return "Unclassified"


buildings["asset_class"] = (
    buildings["type_clean"]
    .apply(classify_asset)
)


# ---------------------------------------------------------
# Summary — full study area
# ---------------------------------------------------------

print()
print("FULL STUDY AREA")
print("-" * 70)

full_summary = (
    buildings["asset_class"]
    .value_counts()
)

print(full_summary)


# ---------------------------------------------------------
# Summary — exposed buildings
# ---------------------------------------------------------

exposed = buildings[
    buildings["rp100_inundated"] == True
].copy()


print()
print("RP100 EXPOSED BUILDINGS")
print("-" * 70)

exposed_summary = (
    exposed["asset_class"]
    .value_counts()
)

print(exposed_summary)


classified_exposed = (
    exposed["asset_class"] != "Unclassified"
).sum()

coverage = (
    classified_exposed
    / len(exposed)
    * 100
)


print()
print(
    f"Classified exposed buildings: "
    f"{classified_exposed:,}"
)

print(
    f"Classification coverage: "
    f"{coverage:.2f}%"
)


# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

pyogrio.write_dataframe(
    buildings,
    OUTPUT_GPKG,
    layer=OUTPUT_LAYER,
    driver="GPKG"
)


print()
print("=" * 70)
print("CLASSIFICATION COMPLETED")
print("=" * 70)

print(f"Output: {OUTPUT_GPKG}")