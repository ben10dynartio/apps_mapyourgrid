import geopandas as gpd
import numpy as np
import pandas as pd
from ohsome import OhsomeClient
import os.path

# list of iso code of countries
countrylist = ["AF", "AL", "DZ", "AD", "AO", "AG", "AR", "AM", "AU", "AT", "AZ", "BH", "BD", "BB", "BY", "BE", "BZ",
               "BJ", "BT", "BO", "BA", "BW", "BR", "BN", "BG", "BF", "BI", "KH", "CM", "CA", "CV", "CF", "TD", "CL",
               "CO", "KM", "CR", "HR", "CU", "CY", "CZ", "CD", "DJ", "DM", "DO", "EC", "EG", "SV", "GQ", "ER", "EE",
               "SZ", "ET", "FM", "FJ", "FI", "FR", "GA", "GE", "DE", "GH", "GR", "GD", "GT", "GN", "GW", "GY", "HT",
               "HN", "HU", "IS", "IN", "ID", "IR", "IQ", "IE", "IL", "IT", "CI", "JM", "JP", "JO", "KZ", "KE", "NL",
               "KI", "KW", "KG", "LA", "LV", "LB", "LS", "LR", "LY", "LI", "LT", "LU", "MG", "MW", "MY", "MV", "ML",
               "MT", "MH", "MR", "MU", "MX", "MD", "MC", "MN", "ME", "MA", "MZ", "MM", "NA", "NR", "NP", "NZ", "NI",
               "NE", "NG", "KP", "MK", "NO", "OM", "PK", "PW", "PA", "PG", "PY", "CN", "PE", "PH", "PL", "PT", "QA",
               "CG", "RO", "RU", "RW", "KN", "LC", "VC", "WS", "SM", "SA", "SN", "RS", "SC", "SL", "SG", "SK", "SI",
               "SB", "SO", "ZA", "KR", "SS", "ES", "LK", "PS", "SD", "SR", "SE", "CH", "SY", "ST", "TW", "TJ", "TZ",
               "TH", "BS", "GM", "TL", "TG", "TO", "TT", "TN", "TR", "TM", "TV", "UG", "UA", "AE", "GB", "US", "UY",
               "UZ", "VU", "VA", "VE", "VN", "YE", "ZM", "ZW"]

## Initialisation file of country shapes
conversion_iso3_to_iso2_code = {"NOR":"NO"}
gdf = gpd.read_file("WB_countries_Admin0_lowres.geojson")
gdf["ISO_A2"] = np.where(gdf["WB_A3"].isin(list(conversion_iso3_to_iso2_code.keys())),
                         gdf["WB_A3"].apply(lambda x: conversion_iso3_to_iso2_code.get(x)), gdf["ISO_A2"])
gdf["isoa2"] = gdf["ISO_A2"]
gdf["geometry"] = gdf["geometry"].buffer(0)
gdf = gdf.dissolve(by='isoa2')

## Initialisation OhsomeClient
ohsome_client = OhsomeClient()
print(ohsome_client.end_timestamp)
compare_times = ["2025-08-20"] #['2025-01-01', ohsome_client.end_timestamp]

## data file name
data_filename = "countries_ohsome_power_line_length_km.csv"

def query_ohsome_power_line_length(countrycode):
    global ohsome_client, gdf
    countrydf = gdf[gdf.index == countrycode]
    response = ohsome_client.elements.length.groupByBoundary.post(
        bpolys=countrydf, filter="power=line", time = compare_times)
    response_df = response.as_dataframe()
    return {str(key[1])[:10]:int(val["value"]/1000) for key, val in response_df.to_dict(orient='index').items()}


def update_file():
    global data_filename
    if not os.path.isfile(data_filename):
        ndf = pd.DataFrame({"isoa2":countrylist})
        for timeseq in compare_times:
            ndf[str(timeseq)[:10]] = ""
        ndf.to_csv(data_filename, index=False)
        print("File created =", data_filename)

    df = pd.read_csv(data_filename).fillna("")
    for i in df.index:
        row = df.iloc[i]
        if row["isoa2"] in ["FJ", "-99", "", "RU", "TW"]:
            continue
        if row[compare_times[0]] == "":
            print("Request", row["isoa2"], end="")
            result = query_ohsome_power_line_length(row["isoa2"])
            print(" =", result)
            for key, val in result.items():
                df.at[i, key] = val
            df.to_csv(data_filename, index=False)

update_file()
