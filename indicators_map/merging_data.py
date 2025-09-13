import geopandas as gpd
import pandas as pd
from config import WORLD_COUNTRY_DICT

filepath_world = "data/World Bank Official Boundaries - Admin 0 - Simplified.gpkg"
filepath_voltage = "data/voltage_osm_line.xlsx"
filepath_wikidata = "data/wikidata_countries_info_brut.csv"
filepath_openinframap = "data/openinframap_countries_info_brut.csv"

gdf_world = gpd.read_file(filepath_world)
df_voltage = pd.read_excel(filepath_voltage)
df_wikidata = pd.read_csv(filepath_wikidata)
df_openinframap = pd.read_csv(filepath_openinframap)

print(gdf_world.columns)
print(df_voltage.columns)
print(df_wikidata.columns)
print(df_openinframap.columns)

gdf_world = gdf_world.merge(df_voltage, left_on='ISO_A2', right_on='Country Code', suffixes=(None, "_voltage"), how='left')
gdf_world = gdf_world.merge(df_wikidata, left_on='ISO_A2', right_on='codeiso2', suffixes=(None, "_wikidata"), how='left')
gdf_world = gdf_world.merge(df_openinframap, left_on='ISO_A2', right_on='codeiso2', suffixes=(None, "_openinframap"), how='left')

gdf_world.to_file("data/worldmap_indicators.geojson")
