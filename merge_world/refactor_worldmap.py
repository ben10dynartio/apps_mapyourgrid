"""
Transform world_country_shape_original.geojson (v5.1.1) into world_country_shape.geojson
with appropriated transformation to fit OpenStreetMap Shape
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "common"))

import configapps
from utils_data import convert_int

import pandas as pd
import geopandas as gpd
import zipfile
import numpy as np
import shutil

original_layer_zipfile = Path(__file__).parent / "ne_10m_admin_0_countries.zip"
extracted_layer_folder = Path(__file__).parent / "ne_10m_admin_0_countries"
exported_layer_file = Path(__file__).parent / "world_country_shape.geojson"

def clean_table(folder_path):
    gdf = gpd.read_file(folder_path / "ne_10m_admin_0_countries.shp")
    gdf = gdf.fillna("")
    print(gdf)

    # Manage France
    gdft = gdf[gdf["SOV_A3"] == "FR1"].copy()
    gdft = gdft.dissolve()
    gdf = gdf[(gdf["SOV_A3"] != "FR1") | (gdf["ADM0_A3"]=="FRA")].copy()
    gdf["geometry"] = np.where(gdf["ADM0_A3"]=="FRA",
                               gdft.iloc[0]["geometry"], gdf["geometry"])

    # Manage Australia
    gdft = gdf[gdf["SOV_A3"] == "AU1"].copy()
    gdft = gdft.dissolve()
    gdf = gdf[(gdf["SOV_A3"] != "AU1") | (gdf["ADM0_A3"]=="AUS")].copy()
    gdf["geometry"] = np.where(gdf["ADM0_A3"]=="AUS",
                               gdft.iloc[0]["geometry"], gdf["geometry"])

    # Manage United States
    gdft = gdf[gdf["SOV_A3"] == "US1"].copy()
    gdft = gdft.dissolve()
    gdf = gdf[(gdf["SOV_A3"] != "US1") | (gdf["ADM0_A3"]=="USA")].copy()
    gdf["geometry"] = np.where(gdf["ADM0_A3"]=="USA",
                               gdft.iloc[0]["geometry"], gdf["geometry"])

    # Manage Kazakhstan
    gdft = gdf[gdf["SOV_A3"] == "KA1"].copy()
    gdft = gdft.dissolve()
    gdf = gdf[(gdf["SOV_A3"] != "KA1") | (gdf["ADM0_A3"] == "KAZ")].copy()
    gdf["geometry"] = np.where(gdf["ADM0_A3"] == "KAZ",
                               gdft.iloc[0]["geometry"], gdf["geometry"])

    # Manage New Zealand
    gdft = gdf[gdf["SOV_A3"] == "NZ1"].copy()
    gdft = gdft.dissolve()
    gdf = gdf[(gdf["SOV_A3"] != "NZ1") | (gdf["ADM0_A3"] == "NZL")].copy()
    gdf["geometry"] = np.where(gdf["ADM0_A3"] == "NZL",
                               gdft.iloc[0]["geometry"], gdf["geometry"])

    # Manage New Zealand
    gdft = gdf[gdf["SOV_A3"] == "NZ1"].copy()
    gdft = gdft.dissolve()
    gdf = gdf[(gdf["SOV_A3"] != "NZ1") | (gdf["ADM0_A3"] == "NZL")].copy()
    gdf["geometry"] = np.where(gdf["ADM0_A3"] == "NZL",
                               gdft.iloc[0]["geometry"], gdf["geometry"])

    # Manage Finland
    gdft = gdf[gdf["SOV_A3"] == "FI1"].copy()
    gdft = gdft.dissolve()
    gdf = gdf[(gdf["SOV_A3"] != "FI1") | (gdf["ADM0_A3"] == "FIN")].copy()
    gdf["geometry"] = np.where(gdf["ADM0_A3"] == "FIN",
                               gdft.iloc[0]["geometry"], gdf["geometry"])

    # Manage Brazil
    gdft = gdf[gdf["SOV_A3"].isin(["BRI", "BRA"])].copy()
    gdft = gdft.dissolve()
    gdf = gdf[(gdf["SOV_A3"] != "BRI")].copy()
    gdf["geometry"] = np.where(gdf["SOV_A3"] == "BRA",
                               gdft.iloc[0]["geometry"], gdf["geometry"])


    # Manage Somalia (merge with Somaliland)
    gdft = gdf[gdf["SOV_A3"].isin(["SOL", "SOM"])].copy()
    gdft = gdft.dissolve()
    gdf = gdf[(gdf["SOV_A3"] != "SOL")].copy()
    gdf["geometry"] = np.where(gdf["SOV_A3"] == "SOM",
                               gdft.iloc[0]["geometry"], gdf["geometry"])


    # Manage The Netherlands
    gdft = gdf[gdf["SOV_A3"] == "NL1"].copy()
    gdft = gdft.dissolve()
    gdf = gdf[(gdf["SOV_A3"] != "NL1") | (gdf["ADM0_A3"] == "NLD")].copy()
    gdf["geometry"] = np.where(gdf["ADM0_A3"] == "NLD",
                               gdft.iloc[0]["geometry"], gdf["geometry"])


    # Manage Cuba
    gdft = gdf[gdf["SOV_A3"] == "CU1"].copy()
    gdft = gdft.dissolve()
    gdf = gdf[(gdf["SOV_A3"] != "CU1") | (gdf["ADM0_A3"] == "CUB")].copy()
    gdf["geometry"] = np.where(gdf["ADM0_A3"] == "CUB",
                               gdft.iloc[0]["geometry"], gdf["geometry"])

    # Manage China
    gdft = gdf[gdf["SOV_A3"] == "CH1"].copy()
    gdft = gdft.dissolve()
    gdf = gdf[(gdf["SOV_A3"] != "CH1") | (gdf["ADM0_A3"] == "CHN")].copy()
    gdf["geometry"] = np.where(gdf["ADM0_A3"] == "CHN",
                               gdft.iloc[0]["geometry"], gdf["geometry"])

    # Manage Cyprus
    gdft = gdf[gdf["SOV_A3"].isin(["CYN", "CYP", "CNM"])].copy()
    gdft = gdft.dissolve()
    gdf = gdf[~gdf["SOV_A3"].isin(["CYN", "CNM"])].copy()
    gdf["geometry"] = np.where(gdf["SOV_A3"] == "CYP",
                               gdft.iloc[0]["geometry"], gdf["geometry"])

    gdf["ISO_A2"] = gdf["ISO_A2_EH"]
    del gdf["ISO_A2_EH"]
    gdf["ISO_A3"] = gdf["ISO_A3_EH"]
    del gdf["ISO_A3_EH"]

    filepath_wikidata = configapps.OUTPUT_WORLD_FOLDER_PATH / "wikidata_countries_info_formatted.csv"
    df_wikidata = pd.read_csv(filepath_wikidata, na_filter=False)

    gdf = gdf.merge(df_wikidata, left_on="ISO_A2", right_on="codeiso2", how="left")
    gdf = gdf.fillna("")
    # Correct Netherland & Palestine
    gdf["WIKIDATAID"] = np.where(gdf["ADM0_A3"].isin(["NLD", "PSX", "SHN"]),
                                 gdf["wikidata_id"], gdf["WIKIDATAID"])
    gdf["osm_rel_id"] = gdf["osm_rel_id"].apply(lambda x: convert_int(x, default=None, error=None)).astype('Int64')

    # For Wikidata debug
    gdft = gdf[gdf["WIKIDATAID"] != gdf["wikidata_id"]]
    for row in gdft.to_dict(orient="records"):
        if row["wikidata_id"]:
            print("ERROR WITH WIKIDATA =", row)

    lst_col_del = [col for col in gdf.columns if "FCLASS_" in col and len(col)==9]
    for col in lst_col_del:
        del gdf[col]
    del gdf["wikidata_id"]

    gdf.to_file(exported_layer_file, index=False)

    # Manage US

def process_zip(zip_path):

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extracted_layer_folder)

        clean_table(extracted_layer_folder)

    finally:
        # Suppression du dossier d'extraction et de tout son contenu
        shutil.rmtree(extracted_layer_folder)
        pass

if __name__ == "__main__":
    process_zip(original_layer_zipfile)
    #clean_table(extracted_layer_folder)