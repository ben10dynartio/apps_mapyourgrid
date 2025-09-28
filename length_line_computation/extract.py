import geopandas as gpd
import pandas as pd
import numpy as np
import math

data_path = "/home/ben/DevProjets/osm-power-grid-map-analysis/data/AR/"

# Colombia : 6273 ; Nepal : 6207
gdf = gpd.read_file(data_path + "osm_brut_power_line.gpkg")


def haversine_distance(coord1, coord2):
    """Calculates the distance between two lat/lon coordinates in kilometers."""
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def length_way(geometry) :
    coords = geometry.coords
    total_length = 0
    for i in range(len(coords) - 1):
        total_length += haversine_distance(coords[i], coords[i+1])
    return total_length


print(gdf.crs)
print(gdf)

#gdf["line_length"] = gdf["geometry"].length / 1000
gdf["line_length"] = gdf["geometry"].apply(lambda x: length_way(x))
gdf["circuits"] = np.where(gdf["circuits"].isna(), '1', gdf["circuits"]).astype(int)
gdf["voltage"] = np.where(gdf["voltage"].isna(), "", gdf["voltage"])
gdf["nb_voltage"] = gdf["voltage"].apply(lambda x: x.count(";") + 1)
gdf["nb_voltage"] = np.where(gdf["voltage"] == "", 0, gdf["nb_voltage"])



print("Somme = ", sum(gdf["line_length"]), "km")
print("circuits values =", gdf["circuits"].unique().tolist())
print("voltage values =", gdf["voltage"].unique().tolist())

# :todo: Check inconsistency
temp = gdf[(gdf["nb_voltage"]!=gdf["circuits"]) & (gdf["nb_voltage"]>=2)]
for row in temp.to_dict(orient='records'):
    print(" * ERROR with number of circuits with ", row)

# Not reliable
#gdf["circuits"] = np.where(gdf["nb_voltage"] == 2, 2, gdf["circuits"])

## Splitting voltages
append_rows = []
for row in gdf.to_dict(orient='records'):
    for i in range(2, max(gdf["circuits"])):
        if row["nb_voltage"] >= i:
            #print(row)
            temp = row.copy()
            temp["voltage"] = temp["voltage"].split(";")[i-1]
            append_rows.append(temp)

gdf["voltage"] = np.where(gdf["nb_voltage"] == 2, gdf["voltage"].apply(lambda x: x.split(";")[0]), gdf["voltage"])

if len(append_rows) > 0:
    gdf = pd.concat([gdf, gpd.GeoDataFrame(append_rows, geometry="geometry", crs=gdf.crs)])

gdf["voltage"] = np.where(gdf["voltage"] == "", 0, gdf["voltage"]).astype(int)

print(gdf)
print(type(gdf))
print(gdf.crs)

print("Somme = ", sum(gdf["line_length"]), "km")
print("circuits values =", gdf["circuits"].unique().tolist())
print("voltage values =", gdf["voltage"].unique().tolist())
#print("voltage values =", gdf["voltage"].unique().tolist())

gdf["circuit_length"] = gdf["line_length"] * gdf["circuits"]

lsv = gdf["voltage"].unique().tolist()
lsv.sort()
results = {}
for v in lsv:
    tdf = gdf[gdf["voltage"]==v]
    results[v] = round(float(tdf["circuit_length"].sum()), 2)

import pprint
pprint.pp(results)