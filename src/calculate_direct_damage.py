import numpy as np
import pandas as pd
import pyogrio


# ============================================================
# INPUT / OUTPUT
# ============================================================

BUILDINGS_GPKG = (
    "data/processed/"
    "prague_buildings_classified.gpkg"
)

BUILDINGS_LAYER = "prague_buildings_classified"

JRC_FILE = (
    "data/raw/vulnerability/"
    "jrc_global_flood_depth_damage.xlsx"
)

OUTPUT_GPKG = (
    "data/processed/"
    "prague_buildings_damage.gpkg"
)

OUTPUT_LAYER = "prague_buildings_damage"

OUTPUT_SUMMARY = (
    "outputs/tables/"
    "rp100_direct_damage_summary.csv"
)


# ============================================================
# FUNCTIONS
# ============================================================

def read_europe_damage_curve(
    excel_path,
    damage_class
):
    """
    Read the European JRC depth-damage curve for a building class.

    damage_class:
        Residential
        Commercial
        Industrial
    """

    df = pd.read_excel(
        excel_path,
        sheet_name="Damage functions",
        header=None
    )

    # Row 2 contains continent names.
    continent_row = df.iloc[2]

    europe_columns = [
        i
        for i, value in enumerate(continent_row)
        if str(value).strip().upper() == "EUROPE"
    ]

    if not europe_columns:
        raise ValueError(
            "EUROPE column could not be found "
            "in Damage functions sheet."
        )

    # First EUROPE column corresponds to damage function,
    # later EUROPE column corresponds to standard deviation.
    europe_col = europe_columns[0]

    class_label = f"{damage_class} buildings"

    matches = df.index[
        df.iloc[:, 0]
        .astype(str)
        .str.strip()
        .eq(class_label)
    ].tolist()

    if not matches:
        raise ValueError(
            f"Damage curve not found for: {damage_class}"
        )

    start_row = matches[0]

    # Find beginning of next damage class
    end_row = len(df)

    for row in range(start_row + 1, len(df)):

        class_value = df.iloc[row, 0]

        if pd.notna(class_value):
            end_row = row
            break

    curve = df.iloc[
        start_row:end_row,
        [1, europe_col]
    ].copy()

    curve.columns = [
        "depth_m",
        "damage_ratio"
    ]

    curve["depth_m"] = pd.to_numeric(
        curve["depth_m"],
        errors="coerce"
    )

    curve["damage_ratio"] = pd.to_numeric(
        curve["damage_ratio"],
        errors="coerce"
    )

    curve = (
        curve
        .dropna()
        .sort_values("depth_m")
        .reset_index(drop=True)
    )

    return curve


def read_czech_max_damage(
    excel_path,
    damage_class
):
    """
    Read Czech Republic building-based TOTAL
    maximum damage value in EUR/m2 (2010).
    """

    sheet = f"MaxDamage-{damage_class}"

    df = pd.read_excel(
        excel_path,
        sheet_name=sheet,
        header=None
    )

    matches = df[
        df.iloc[:, 0]
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("czech republic")
    ]

    if matches.empty:
        raise ValueError(
            f"Czech Republic not found in {sheet}"
        )

    # Column positions:
    # 0 Country
    # 1 Structure
    # 2 Content
    # 3 Building-based Total
    value = pd.to_numeric(
        matches.iloc[0, 3],
        errors="raise"
    )

    return float(value)


def interpolate_damage_ratio(
    depths,
    curve
):
    """
    Linear interpolation between JRC depth-damage
    curve points.
    """

    depth_points = (
        curve["depth_m"]
        .to_numpy(dtype=float)
    )

    damage_points = (
        curve["damage_ratio"]
        .to_numpy(dtype=float)
    )

    result = np.interp(
        depths,
        depth_points,
        damage_points,
        left=damage_points[0],
        right=damage_points[-1]
    )

    return np.clip(
        result,
        0.0,
        1.0
    )


# ============================================================
# 1. LOAD BUILDINGS
# ============================================================

print("=" * 70)
print("JRC RP100 DIRECT DAMAGE MODEL")
print("=" * 70)

buildings = pyogrio.read_dataframe(
    BUILDINGS_GPKG,
    layer=BUILDINGS_LAYER
)

print(
    f"\nBuildings loaded: "
    f"{len(buildings):,}"
)


# ============================================================
# 2. LOAD JRC PARAMETERS
# ============================================================

asset_classes = [
    "Residential",
    "Commercial",
    "Industrial"
]


curves = {}
max_damage_values = {}


print()
print("=" * 70)
print("JRC MODEL PARAMETERS")
print("=" * 70)


for asset_class in asset_classes:

    curves[asset_class] = (
        read_europe_damage_curve(
            JRC_FILE,
            asset_class
        )
    )

    max_damage_values[asset_class] = (
        read_czech_max_damage(
            JRC_FILE,
            asset_class
        )
    )

    print()
    print(asset_class)

    print(
        curves[asset_class]
        .to_string(index=False)
    )

    print(
        "Czech max damage: "
        f"{max_damage_values[asset_class]:,.2f} "
        "EUR/m² (2010)"
    )


# ============================================================
# 3. PREPARE DAMAGE FIELDS
# ============================================================

buildings["damage_ratio"] = np.nan

buildings[
    "max_damage_eur_m2_2010"
] = np.nan

buildings[
    "max_damage_eur_2010"
] = np.nan

buildings[
    "estimated_damage_eur_2010"
] = np.nan

buildings[
    "damage_model_status"
] = "UNCLASSIFIED"


# ============================================================
# 4. APPLY JRC DAMAGE MODEL
# ============================================================

for asset_class in asset_classes:

    mask = (
        buildings["asset_class"]
        == asset_class
    )

    if not mask.any():
        continue

    depths = (
        buildings.loc[
            mask,
            "rp100_depth_m"
        ]
        .fillna(0.0)
        .to_numpy(dtype=float)
    )

    ratios = interpolate_damage_ratio(
        depths,
        curves[asset_class]
    )

    max_damage_m2 = (
        max_damage_values[
            asset_class
        ]
    )

    area = (
        buildings.loc[
            mask,
            "area_m2"
        ]
        .to_numpy(dtype=float)
    )

    max_damage = (
        area
        * max_damage_m2
    )

    estimated_damage = (
        max_damage
        * ratios
    )

    buildings.loc[
        mask,
        "damage_ratio"
    ] = ratios

    buildings.loc[
        mask,
        "max_damage_eur_m2_2010"
    ] = max_damage_m2

    buildings.loc[
        mask,
        "max_damage_eur_2010"
    ] = max_damage

    buildings.loc[
        mask,
        "estimated_damage_eur_2010"
    ] = estimated_damage

    buildings.loc[
        mask,
        "damage_model_status"
    ] = "MODELED"


# ============================================================
# 5. EXPOSED BUILDING SUBSET
# ============================================================

exposed = buildings[
    buildings["rp100_inundated"] == True
].copy()


classified_exposed = exposed[
    exposed["damage_model_status"]
    == "MODELED"
].copy()


unclassified_exposed = exposed[
    exposed["damage_model_status"]
    != "MODELED"
].copy()


# ============================================================
# 6. SUMMARY BY ASSET CLASS
# ============================================================

summary = (
    classified_exposed
    .groupby(
        "asset_class",
        observed=True
    )
    .agg(
        building_count=(
            "osm_id",
            "count"
        ),

        total_footprint_m2=(
            "area_m2",
            "sum"
        ),

        mean_flood_depth_m=(
            "rp100_depth_m",
            "mean"
        ),

        mean_damage_ratio=(
            "damage_ratio",
            "mean"
        ),

        estimated_damage_eur_2010=(
            "estimated_damage_eur_2010",
            "sum"
        )
    )
    .reset_index()
)


total_modeled_damage = (
    classified_exposed[
        "estimated_damage_eur_2010"
    ]
    .sum()
)


# ============================================================
# 7. COVERAGE METRICS
# ============================================================

building_coverage = (
    len(classified_exposed)
    / len(exposed)
    * 100
)


total_exposed_area = (
    exposed["area_m2"]
    .sum()
)

classified_exposed_area = (
    classified_exposed["area_m2"]
    .sum()
)

area_coverage = (
    classified_exposed_area
    / total_exposed_area
    * 100
)


# ============================================================
# 8. PRINT RESULTS
# ============================================================

print()
print("=" * 70)
print("RP100 DIRECT DAMAGE SUMMARY")
print("=" * 70)

print(
    f"Total RP100 exposed buildings: "
    f"{len(exposed):,}"
)

print(
    f"Classified exposed buildings: "
    f"{len(classified_exposed):,}"
)

print(
    f"Unclassified exposed buildings: "
    f"{len(unclassified_exposed):,}"
)

print(
    f"Building classification coverage: "
    f"{building_coverage:.2f}%"
)

print(
    f"Footprint-area coverage: "
    f"{area_coverage:.2f}%"
)


print()
print("Damage by asset class:")
print()

print(
    summary.to_string(
        index=False
    )
)


print()
print(
    "Estimated direct damage "
    "(classified subset only): "
    f"€{total_modeled_damage:,.2f} "
    "(2010 EUR)"
)


# ============================================================
# 9. SAVE OUTPUTS
# ============================================================

summary.to_csv(
    OUTPUT_SUMMARY,
    index=False
)


pyogrio.write_dataframe(
    buildings,
    OUTPUT_GPKG,
    layer=OUTPUT_LAYER,
    driver="GPKG"
)


print()
print("=" * 70)
print("OUTPUT FILES")
print("=" * 70)

print(
    f"Building-level damage: "
    f"{OUTPUT_GPKG}"
)

print(
    f"Damage summary: "
    f"{OUTPUT_SUMMARY}"
)