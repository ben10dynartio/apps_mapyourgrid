"""
Prototype
Plotly lib is not in requirement.txt please install it separetly
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "common"))

import configapps

import plotly.express as px

import geopandas as gpd

continent_colors = {
    "Europe": "#4C72B0",
    "Africa": "#55A868",
    "Asia": "#C44E52",
    "North America": "#8172B3",
    "South America": "#64B5CD",
    "Oceania": "#CCB974",
    "Antarctica": "#DDDDDD",
    "": "#DDDDDD",
}


df = gpd.read_file(configapps.OUTPUT_WORLD_FOLDER_PATH / "worldmap_indicators.geojson")
df2 = gpd.read_file(configapps.OUTPUT_WORLD_FOLDER_PATH / "wikidata_countries_info_brut.csv")

df = df.merge(df2, left_on="code_isoa2", right_on="codeiso2", suffixes=(None, "_y"))

df = df[df["osm_circuit_above_50kv_length_km"] > 0].copy()

fig = px.treemap(
    df,
    path=["continent", "name"],
    values="osm_circuit_above_50kv_length_km",
    color="continent",
    color_discrete_map=continent_colors
)

fig.show()