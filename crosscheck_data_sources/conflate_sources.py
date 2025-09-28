import pandas as pd

from config import WORLD_COUNTRY_DICT

df_wiki = pd.read_excel("extracted_wikipage.xlsx").fillna("")
df_wiki = df_wiki[df_wiki["error"]==""]
del df_wiki['Unnamed: 0']
df_awes = pd.read_excel("extracted_awesome_list.xlsx").fillna("")
del df_awes['Unnamed: 0']

allstr = ""
for countrycode, countryname in WORLD_COUNTRY_DICT.items():
    strreport = ""
    tdf_wiki = df_wiki[df_wiki["countryname"]==countryname]
    tdf_wiki = tdf_wiki[tdf_wiki["source_text"]!="xxx"]
    tdf_wiki = tdf_wiki[tdf_wiki["source_text"] != ""]
    tdf_awes = df_awes[df_awes["countryname"].apply(lambda x: countryname in x.split(";"))]
    strreport += f"==== {countryname} ({countrycode}) ====\n"

    if (len(tdf_awes)==0) and (len(tdf_wiki)==0):
        strreport += f"  >> No source\n"
    else:
        strreport += f"  >> {len(tdf_wiki)} data sources in wiki - https://wiki.openstreetmap.org/wiki/Power_networks/{countryname.replace(" ", "_")}\n"
        for row in tdf_wiki.to_dict(orient='records'):
            strreport += f"    * {row["link_text"]} : {row["link_href"]}"
            strreport += "  || " + " | ".join([f"{keyop}={row[keyop]}" for keyop in ["date", "license", "suitable_for_OSM", "notes"]])
            strreport += "\n"

        strreport += f"  >> {len(tdf_awes)} data sources in awesomelist\n"
        for row in tdf_awes.to_dict(orient='records'):
            strreport += f"    * {row["text_refined"]} : {row["link_href"]}\n"


        list_wiki_href = set(tdf_wiki["link_href"].tolist())
        list_awes_href = set(tdf_awes["link_href"].tolist())

        strreport += f"  >> Conflation ({len(list_wiki_href & list_awes_href)} sources in common)\n"


        lines = [f"* ({countryname}) [{row["link_text"]}]({row["link_href"]})\n"
                 for row in tdf_wiki.to_dict(orient='records') if row["link_href"] not in list_awes_href]
        if lines:
            strreport += f"    * ------ Missing in Awesome list :\n"
            for l in lines:
                strreport += l

        lines = [f"{{{{PowerNetworksDatasourceRow|source=[{row["link_href"]} {row["text_refined"].strip()}]|license=?|date=?|osm_suitable=?|comments=-}}}}\n"
                 for row in tdf_awes.to_dict(orient='records') if row["link_href"] not in list_wiki_href]
        if lines:
            strreport += f"    * ------ Missing OSM Wiki :\n"
            for l in lines:
                strreport += l

    #strreport += "\n"
    allstr += strreport + "\n"
    print(strreport)
    with open("conflation_analysis_result.txt", "w", encoding="utf-8") as f:
        f.write(allstr)
