import numpy as np
import pandas as pd
import pyogrio


INPUT_GPKG = "data/processed/prague_buildings_damage.gpkg"
INPUT_LAYER = "prague_buildings_damage"

OUTPUT_GPKG = (
    "data/processed/"
    "prague_rp100_modeled_damage.gpkg"
)

OUTPUT_LAYER = "rp100_modeled_damage"

OUTPUT_CSV = (
    "outputs/tables/"
    "rp100_damage_class_summary.csv"
)


print("=" * 70)
print("CREATING RP100 DAMAGE OUTPUTS")
print("=" * 70)


# ---------------------------------------------------------
# Read results
# ---------------------------------------------------------

buildings = pyogrio.read_dataframe(
    INPUT_GPKG,
    layer=INPUT_LAYER
)


# ---------------------------------------------------------
# Keep classified + inundated buildings only
# ---------------------------------------------------------

damage = buildings[
    (buildings["rp100_inundated"] == True)
    &
    (buildings["asset_class"] != "Unclassified")
].copy()


print(
    f"Modeled exposed buildings: "
    f"{len(damage):,}"
)


# ---------------------------------------------------------
# Create damage classes
# ---------------------------------------------------------

damage["damage_class"] = pd.cut(
    damage["estimated_damage_eur_2010"],
    bins=[
        -0.01,
        50_000,
        100_000,
        250_000,
        500_000,
        1_000_000,
        np.inf,
    ],
    labels=[
        "≤ €50k",
        "€50k–€100k",
        "€100k–€250k",
        "€250k–€500k",
        "€500k–€1M",
        "> €1M",
    ],
    include_lowest=True,
)


# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------

summary = (
    damage
    .groupby(
        "damage_class",
        observed=True
    )
    .agg(
        building_count=(
            "osm_id",
            "count"
        ),
        estimated_damage_eur_2010=(
            "estimated_damage_eur_2010",
            "sum"
        ),
        mean_damage_eur_2010=(
            "estimated_damage_eur_2010",
            "mean"
        )
    )
    .reset_index()
)


print()
print("=" * 70)
print("DAMAGE CLASS SUMMARY")
print("=" * 70)

print(
    summary.to_string(
        index=False
    )
)


# ---------------------------------------------------------
# Save GIS layer
# ---------------------------------------------------------

pyogrio.write_dataframe(
    damage,
    OUTPUT_GPKG,
    layer=OUTPUT_LAYER,
    driver="GPKG"
)


# ---------------------------------------------------------
# Save CSV
# ---------------------------------------------------------

summary.to_csv(
    OUTPUT_CSV,
    index=False
)


print()
print("=" * 70)
print("OUTPUTS")
print("=" * 70)

print(f"Damage layer: {OUTPUT_GPKG}")
print(f"Summary:      {OUTPUT_CSV}")