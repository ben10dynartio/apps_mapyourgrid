# GridInspector

GridInspector is a suite of quality analysis tools for power grid data in OpenStreetMap. It is developped by <a href="https://dynartio.com" target="_blank">Dynartio</a> as part of the <a href="https://mapyourgrid.org" target="_blank">#MapYourGrid</a> initiative.

## Related repository (data extraction)

The data processed by GridInspector is extracted using scripts from:  
https://github.com/ben10dynartio/osm-power-grid-map-analysis

## Repository structure
This repository contains the following tools :
- `circuit_length/` : Compute power line and circuit lengths
- `common/` : Shared configuration (notably file paths) and utility functions
- `crosscheck_data_source/` : Fetch sources from the OSM Wiki and from MapYourGrid's <a href="https://github.com/open-energy-transition/Awesome-Electrical-Grid-Mapping/blob/main/README.md" target="_blank">Awesome Electrical Grid Mapping List</a> and compare them
- `gridgraph_webpage/` : Prototyping (web)
- `graphics/` : Prototyping (data visualisation)
- `indicators_map/` : Generate the global indicator map (rendered here: [https://apps.dynartio.com/mapyourgrid/gridindicator.html](https://mapyourgrid.dynartio.com/gridinspector/))
- `interconnectors/` : Extract international power grid interconnectors
- `merge_world/` : Merge outputs from all tools and produce the indicator map dataset
- `ohsome_power_lines_length/` : Fetch Ohsome to get historical power line length data (not maintened)
- `osmwiki/` : Fetch data from Wikidata and [OpenInfraMap](https://openinframap.org/#2/26/12)
- `quality_grid_stats/` : Perform grid topology and connectivity analysis 
- `show_errors_page/` : In developpement (render collected errors during script execution)
- `spatial_analysis/` : Evaluate substation coverageusing population density
- `voltage_operator_analysis/` : Extract voltage and operator information for each country

## Download complementary data
- Create the folder `spatial_analysis/data_kontur`
- Populate it using this ZIP file: https://github.com/ben10dynartio/mygprocess/releases/download/v0.1/releasedata.zip

## Line/circuit length calculation details
Line length calculation initially comes from an Overpass script that fetches all power lines (and metadata) for a country.

## Important details
1) Lines tagged as `construction:power=line` are **not** considered.
2) Lengths are computed from the full geometry of each OSM `way`. As a result, interconnector lengths can be **overestimated** if a line is mapped extensively into a neighboring country. This can explain scores **above 100%** for a given voltage in some countries.
3. `circuits=*` tags are critical to compare OSM coverage with official circuit statistics. Some countries may have power lines well mapped geometrically but lack circuit tags, which can **underestimate** the mapped circuit coverage.
4. If `circuits=*` tags are missing, the tools assume: `circuits=1`.
5. When comparing official sources with OSM-extracted circuit lengths, verify whether the official reference reports **line length** or **circuit length** (OSM Wiki sources may mix the two).

## External data used in this repository :
- Country Shape : https://www.naturalearthdata.com/downloads/10m-cultural-vectors/
- Population density : https://data.humdata.org/dataset/kontur-population-dataset-3km
- MapYourGrid's Global Transmission Lenght Index : https://docs.google.com/spreadsheets/d/1qmVIQ2_ynVVfbTWcMXJQWb4Sq0Dq-1fu8zgZ9J_0cZI
