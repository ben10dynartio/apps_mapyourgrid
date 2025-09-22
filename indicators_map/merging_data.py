import geopandas as gpd
import pandas as pd
import numpy as np
import ast
from config import WORLD_COUNTRY_DICT
import random

def gradient_color(t: float) -> str:
    """
    Retourne la couleur hexadécimale correspondant à la valeur t (0 ≤ t ≤ 1)
    selon le gradient défini.
    """
    # Stops définis comme (offset, (R,G,B))
    if t<=0:
        return "#AAAAAA"

    stops = [
        (0.0,   (0, 0, 0) ),
        (0.1111111111111111, (23, 12, 1)),
        (0.2222222222222222, (47, 24, 2)),
        (0.3333333333333333, (56, 29, 2)),
        (0.4444444444444444, (80, 40, 14)),
        (0.5555555555555556, (124, 54, 28)),
        (0.6666666666666666, (177, 104, 49)),
        (0.7777777777777778, (210, 166, 62)),
        (0.8888888888888888, (242, 229, 76)),
        (1.0,  (42, 163, 100)),
    ]

    stops = [
        (0.0,   (255, 0, 0) ),
        (0.75, (255, 255, 0)),
        (1.0,  (0, 255, 0)),
    ]

    # Clamp t dans [0,1]
    t = max(0.0, min(1.0, t))

    # Trouver les deux stops encadrant t
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]
        if t0 <= t <= t1:
            # interpolation linéaire
            ratio = (t - t0) / (t1 - t0) if t1 != t0 else 0
            r = round(c0[0] + (c1[0] - c0[0]) * ratio)
            g = round(c0[1] + (c1[1] - c0[1]) * ratio)
            b = round(c0[2] + (c1[2] - c0[2]) * ratio)
            return f"#{r:02X}{g:02X}{b:02X}"

    # Cas extrême : si t == 1
    return f"#{stops[-1][1][0]:02X}{stops[-1][1][1]:02X}{stops[-1][1][2]:02X}"

filepath_world = "data/country_worldmap/custom.geojson"
filepath_voltage = "data/osm_country_data_power_line.xlsx"
filepath_wikidata = "data/wikidata_countries_info_formatted.csv"
filepath_openinframap = "data/openinframap_countries_info_brut.csv"
filepath_health_score = "data/0_health_score.xlsx"
filepath_coverage_score = "data/0_coverage_score.xlsx"

gdf_world = gpd.read_file(filepath_world, na_filter=False)
df_voltage = pd.read_excel(filepath_voltage, na_filter=False)
df_wikidata = pd.read_csv(filepath_wikidata, na_filter=False)
df_openinframap = pd.read_csv(filepath_openinframap, na_filter=False)
df_health_score = pd.read_excel(filepath_health_score, na_filter=False)
df_coverage_score = pd.read_excel(filepath_coverage_score, na_filter=False)

print(gdf_world.columns)
print(df_voltage.columns)
print(df_wikidata.columns)
print(df_openinframap.columns)
print(df_health_score.columns)
print(df_coverage_score.columns)

gdf_world = gdf_world.merge(df_voltage, left_on='iso_a2_eh', right_on='Country Code', suffixes=(None, "_voltage"), how='left')
gdf_world = gdf_world.merge(df_wikidata, left_on='iso_a2_eh', right_on='codeiso2', suffixes=(None, "_wikidata"), how='left')
gdf_world = gdf_world.merge(df_openinframap, left_on='iso_a2_eh', right_on='codeiso2', suffixes=(None, "_openinframap"), how='left')
gdf_world = gdf_world.merge(df_health_score, left_on='iso_a2_eh', right_on='codeiso2', suffixes=(None, "_health_score"), how='left')
gdf_world = gdf_world.merge(df_coverage_score, left_on='iso_a2_eh', right_on='codeiso2', suffixes=(None, "_coverage_score"), how='left')


print("-------------------")
import pprint
pprint.pp(list(gdf_world.columns))

print(gdf_world.iloc[0])

gdf_world["code_isoa2"] = gdf_world["iso_a2_eh"]
gdf_world["name"] = gdf_world["Country Name"]

gdf_world["quality_score"] = gdf_world['Line voltage'].apply(lambda x: random.random())
gdf_world["quality_color"] = gdf_world['quality_score'].apply(lambda x: gradient_color(x))
gdf_world["quality_score"] = np.where(gdf_world["name"].isna(), -1, gdf_world["quality_score"] )
gdf_world["quality_color"] = np.where(gdf_world["name"].isna(), "#AAAAAA", gdf_world["quality_color"] )

gdf_world["temp_line_voltage"] = gdf_world['Line voltage']
gdf_world["temp_line_voltage"] = np.where(gdf_world["temp_line_voltage"].isna(), "[]", gdf_world["temp_line_voltage"])
gdf_world["temp_line_voltage"] = gdf_world["temp_line_voltage"].map(ast.literal_eval)
gdf_world["line_voltage"] = gdf_world["temp_line_voltage"].apply(lambda x: ", ".join([str(int(int(j)/1000)) + " kV" for j in x if int(j) > 50000])).astype(str)

health_score_cols = ['health_power_line_connectivity',
 'health_grid_connectivity_without_circuit',
 'health_grid_connectivity_with_circuit',
 'health_line_voltage_completeness',
 'health_line_cables_completness',
 'health_substation_voltage_completness',
 'health_connected_power_tower',
 'health_complete_power_line',
 'health_consistent_line_voltage_connection',
 'health_consistent_linesub_voltage_connection']

other_cols = [
 'stats_nb_international_connections',
 'stats_nb_substations',
 'stats_line_voltages',
    'coverage_population']

select_columns = ["code_isoa2", "name", "flag_image", "osm_rel_id", "population", "area_km2", "gdp_bd", "power_line_total_length",
                  "wikidata_id",
                  "power_plant_count", "power_plant_output_mw", "line_voltage",
                  "quality_score", "quality_color",
                  'geometry'] + other_cols + health_score_cols

gdf_world = gdf_world[select_columns]

for col in health_score_cols:
    gdf_world[col] = gdf_world[col].apply(lambda x: float(x) if x else 0)
    gdf_world[col] = np.where(gdf_world[col].isna(),
                              0, gdf_world[col])

gdf_world["health_score_overall"] = 0
for col in health_score_cols:
    gdf_world["health_score_overall"] += gdf_world[col]
gdf_world["health_score_overall"] /= len(health_score_cols)
gdf_world["quality_score"] = gdf_world["health_score_overall"] / 100
gdf_world["quality_color"] = gdf_world["quality_score"].map(gradient_color)

gdf_world.to_file("data/worldmap_indicators.geojson")
