from pathlib import Path
import pickle

import requests
import pandas as pd
from bs4 import BeautifulSoup

from config import WORLD_COUNTRY_DICT

INV_WORLD_COUNTRY_DICT = {v: k for k, v in WORLD_COUNTRY_DICT.items()}

def fetch_data_sources(country):
    if len(country)==2:
        countrycode = country
        countryname = WORLD_COUNTRY_DICT[country]
    else:
        countrycode = INV_WORLD_COUNTRY_DICT[country]
        countryname = country
    url = f'https://wiki.openstreetmap.org/wiki/Power_networks/{countryname}'
    # Récupérer le contenu HTML
    res = requests.get(url)
    try:
        res.raise_for_status()
    except requests.exceptions.HTTPError:
        return [{
            'countryname':countryname,
            'countrycode':countrycode,
            'pagelink': url,
            'error':"Not found page",
        }]
    soup = BeautifulSoup(res.text, 'html.parser')

    # Trouver la section "Data Sources" via le titre
    # On repère l'élément <span id="Data_Sources"> ou <h2> contenant "Data Sources"
    header = soup.find('span', {'id': 'Data_Sources'})
    if not header:
        header = soup.find(lambda tag: tag.name in ['h2', 'h3'] and 'Data Sources' in tag.get_text())
    if not header:
        return [{
            'countryname': countryname,
            'countrycode': countrycode,
            'pagelink': url,
            'error': "Not found datasource section",
        }]

    # Le tableau suivant l'en-tête
    table = header.find_next('table')
    if not table:
        return [{
            'countryname': countryname,
            'countrycode': countrycode,
            'pagelink': url,
            'error': "Not found datasource table",
        }]

    data = []
    # Parcourir les lignes du tableau
    first_row = True
    for row in table.find_all('tr'):
        if first_row:
            first_row = False
            continue
        cols = row.find_all(['td', 'th'])
        if not cols or len(cols) < 4:
            continue
        source_cell = cols[0]
        license_cell = cols[1]
        date_cell = cols[2]
        suitable_cell = cols[3]
        notes_cell = cols[4] if len(cols) > 4 else None

        # Récupération textuelle et lien éventuel
        link = source_cell.find('a')
        if link:
            link_href = link.get('href')
            link_text = link.get_text(strip=True)
            source_text = source_cell.get_text(separator=' ', strip=True)
        else:
            link_href = None
            link_text = None
            source_text = source_cell.get_text(strip=True)

        data.append({
            'countryname':countryname,
            'countrycode':countrycode,
            'pagelink':url,
            'source_text': source_text,
            'link_text': link_text,
            'link_href': link_href,
            'license': license_cell.get_text(strip=True),
            'date': date_cell.get_text(strip=True),
            'suitable_for_OSM': suitable_cell.get_text(strip=True),
            'notes': notes_cell.get_text(strip=True) if notes_cell else None,
            'error':"",
        })

    return data


if __name__ == '__main__':

    for i, country in enumerate(WORLD_COUNTRY_DICT.keys()):
        fichier = Path(f"cache/wiki/{country}.pkl")
        if Path.exists(fichier):
            continue
        print(country, end=" ")
        if (i+1)%30==0:
            print()
        country_datasources = fetch_data_sources(country)
        with open(fichier, "wb") as f:  # "wb" = write binary
            pickle.dump(country_datasources, f)

    sourcelist = []
    for i, country in enumerate(WORLD_COUNTRY_DICT.keys()):
        fichier = Path(f"cache/wiki/{country}.pkl")
        with open(fichier, "rb") as f:  # "rb" = read binary
            sourcelist.extend(pickle.load(f))

    df = pd.DataFrame(sourcelist)
    df.to_excel("extracted_wikipage.xlsx")