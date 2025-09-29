import requests
import json

from config import WORLD_COUNTRY_DICT, CONTINENTAL_COUNTRY_DICT

LOG_LEVEL = "INFO"

def fetch_osmose_issues(country="colombia*", item=7040, cls=3, use_dev_item="all"):
    """
    Récupère les données GeoJSON issues de l'API Osmose pour des critères donnés.
    Some example of URL :
    https://osmose.openstreetmap.fr/fr/issues/open?source=411091&item=7040&class=3&useDevItem=all
    https://osmose.openstreetmap.fr/api/0.3/issues?source=411091&item=7040&class=3&useDevItem=true&full=true
    https://osmose.openstreetmap.fr/api/0.3/issues.geojson?source=411091&item=7040&class=3&useDevItem=all&full=true
    https://osmose.openstreetmap.fr/api/0.3/issues.geojson?country=colombia*&item=7040&class=3&useDevItem=all

    Osmose classes :
    # class 1 : Lone power tower or pole
    # class 2 : Unfinished power transmission line
    # class 3 : Connection between different voltages
    # class 4 : Non power node on power way
    # class 5 : Missing power tower or pole
    # class 6 : Unfinished power distribution line
    # class 7 : Unmatched voltage of line on substation
    # class 8 : Power support line management suggestion

    Args:
        country (str): Nom (ou wildcard) du pays (ex. "colombia*").
        item (int): Code de l'item Osmose.
        cls (int): Code de la classe de l'item.
        use_dev_item (str): "true", "false" ou "all" selon le filtrage des items en développement.

    Returns:
        dict: Contenu JSON parsé (GeoJSON).
    """
    url = "https://osmose.openstreetmap.fr/api/0.3/issues.geojson"
    params = {
        "country": country,
        "item": item,
        "class": cls,
        "useDevItem": use_dev_item,
        "limit": "1000000",
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":

    for countrycode, countryname in {"IN":"India"}.items(): #CONTINENTAL_COUNTRY_DICT["Europe"].items(): #WORLD_COUNTRY_DICT.items(): #

        countryref = countryname.lower().replace(" ", "_") + "*"
        myresult = {"country":countrycode, "class":{}, "class-extend":{}}
        for i in range(1, 9): #[3,]: #
            #print("--------", i)

            geojson = fetch_osmose_issues(country=countryref, item=7040, cls=i, use_dev_item="all", )
            # Traitement simple : affichage du nombre de features
            features = geojson.get("features", [])
            print(f"({countrycode}-{countryref}) Class {i} / Nombre de features récupérées : {len(features)}")
            myresult["class"][i] = len(features)
            if LOG_LEVEL in ["DEBUG"]:
                import pprint
                pprint.pp(features)
            if i == 1:
                elems = [f["properties"]["elems"][0]["tags"]["power"] for f in features]
                myresult["class-extend"]["nb_lone_power_tower"] = elems.count("tower")
            if i == 5:
                elems = [f["properties"]["elems"][0]["tags"]["power"] for f in features]
                myresult["class-extend"]["nb_missing_power_tower"] = elems.count("tower")
            if i == 7:
                elems = [f["properties"]["elems"][1]["id"] for f in features]
                elems = set(elems)
                myresult["class-extend"]["nb_unmatched_substation_voltage"] = len(elems)

            # Exemple d'utilisation : afficher les types géométriques (geometry.type)
            types = set(f.get("geometry", {}).get("type", "None") for f in features)
            #print("Types de géométries présents :", types)


        with open(f"build/osmose_{countrycode}.json", "w", encoding="utf-8") as f:
            json.dump(myresult, f, ensure_ascii=False, indent=4)
            print()

        print("Results =", myresult)

