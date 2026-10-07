import numpy as np
import pyogrio


INPUT_GPKG = "data/processed/prague_buildings_damage.gpkg"
INPUT_LAYER = "prague_buildings_damage"


print("=" * 70)
print("DIRECT DAMAGE MODEL QUALITY CONTROL")
print("=" * 70)


buildings = pyogrio.read_dataframe(
    INPUT_GPKG,
    layer=INPUT_LAYER
)


# ---------------------------------------------------------
# 1. Modeled / unclassified subsets
# ---------------------------------------------------------

modeled = buildings[
    buildings["damage_model_status"] == "MODELED"
].copy()

unclassified = buildings[
    buildings["damage_model_status"] == "UNCLASSIFIED"
].copy()


print(f"\nTotal buildings: {len(buildings):,}")
print(f"Modeled buildings: {len(modeled):,}")
print(f"Unclassified buildings: {len(unclassified):,}")


# ---------------------------------------------------------
# 2. Damage ratio must be between 0 and 1
# ---------------------------------------------------------

invalid_ratio = modeled[
    (modeled["damage_ratio"] < 0)
    | (modeled["damage_ratio"] > 1)
]

print()
print("CHECK 1 — DAMAGE RATIO RANGE")
print(f"Invalid ratios: {len(invalid_ratio):,}")


# ---------------------------------------------------------
# 3. Maximum damage formula
#
# area_m2 × max_damage_eur_m2
# ---------------------------------------------------------

expected_max_damage = (
    modeled["area_m2"]
    * modeled["max_damage_eur_m2_2010"]
)

max_damage_difference = np.abs(
    modeled["max_damage_eur_2010"]
    - expected_max_damage
)

invalid_max_damage = (
    max_damage_difference > 0.01
).sum()

print()
print("CHECK 2 — MAXIMUM DAMAGE FORMULA")
print(
    f"Formula mismatches: "
    f"{invalid_max_damage:,}"
)


# ---------------------------------------------------------
# 4. Estimated damage formula
#
# max damage × damage ratio
# ---------------------------------------------------------

expected_damage = (
    modeled["max_damage_eur_2010"]
    * modeled["damage_ratio"]
)

damage_difference = np.abs(
    modeled["estimated_damage_eur_2010"]
    - expected_damage
)

invalid_damage_formula = (
    damage_difference > 0.01
).sum()

print()
print("CHECK 3 — ESTIMATED DAMAGE FORMULA")
print(
    f"Formula mismatches: "
    f"{invalid_damage_formula:,}"
)


# ---------------------------------------------------------
# 5. Damage must not exceed maximum damage
# ---------------------------------------------------------

damage_above_max = modeled[
    modeled["estimated_damage_eur_2010"]
    >
    modeled["max_damage_eur_2010"] + 0.01
]

print()
print("CHECK 4 — DAMAGE <= MAXIMUM DAMAGE")
print(
    f"Violations: "
    f"{len(damage_above_max):,}"
)


# ---------------------------------------------------------
# 6. Zero flood depth should imply zero damage
# ---------------------------------------------------------

zero_depth = modeled[
    modeled["rp100_depth_m"] <= 0
]

zero_depth_with_damage = zero_depth[
    zero_depth["estimated_damage_eur_2010"] > 0.01
]

print()
print("CHECK 5 — ZERO DEPTH = ZERO DAMAGE")
print(
    f"Zero-depth buildings: "
    f"{len(zero_depth):,}"
)

print(
    f"Zero-depth buildings with damage: "
    f"{len(zero_depth_with_damage):,}"
)


# ---------------------------------------------------------
# 7. Unclassified buildings should have no modeled damage
# ---------------------------------------------------------

unclassified_with_damage = unclassified[
    unclassified[
        "estimated_damage_eur_2010"
    ].notna()
]

print()
print("CHECK 6 — UNCLASSIFIED BUILDINGS")
print(
    f"Unclassified buildings with damage value: "
    f"{len(unclassified_with_damage):,}"
)


# ---------------------------------------------------------
# 8. Show sample exposed modeled buildings
# ---------------------------------------------------------

sample = (
    modeled[
        modeled["rp100_inundated"] == True
    ][
        [
            "osm_id",
            "type_clean",
            "asset_class",
            "area_m2",
            "rp100_depth_m",
            "damage_ratio",
            "max_damage_eur_m2_2010",
            "max_damage_eur_2010",
            "estimated_damage_eur_2010",
        ]
    ]
    .sort_values(
        "estimated_damage_eur_2010",
        ascending=False
    )
    .head(10)
)


print()
print("=" * 70)
print("TOP 10 MODELED DAMAGE BUILDINGS")
print("=" * 70)

print(
    sample.to_string(
        index=False
    )
)


# ---------------------------------------------------------
# Final QC status
# ---------------------------------------------------------

problems = (
    len(invalid_ratio)
    + invalid_max_damage
    + invalid_damage_formula
    + len(damage_above_max)
    + len(zero_depth_with_damage)
    + len(unclassified_with_damage)
)


print()
print("=" * 70)

if problems == 0:
    print("QC PASSED — NO MODEL CONSISTENCY ERRORS FOUND")
else:
    print(
        f"QC WARNING — "
        f"{problems:,} issue(s) detected"
    )

print("=" * 70)