This repository is used to build the health score map.


**Line/circuit length calculation details**
The line length calculation comes initially from an overpass script which fetches all lines (and metadata) of a country. 
****Important details****
1) 1) This does not include lines "under construction" for the moment.
2) 2) This takes the entire "way" of power lines, which means that interconnector line lengths can be overestimated if mapped well into another country. This can explain certain countries having a score well-above 100% for a specific voltage.
3) 3) Circuit tags are crucial for a valid comparison of actual line mapping coverage. Certain countries can have all lines fully mapped, but may lack circuit tags which can underestimate the actual coverage of lines mapped.
4) 4) If circuit tags are missing then circuit = 1
   5) When comparing official data and OSM extracted data of circuit lengths, check the certainty of the official source to see if it's circuits or lines on the wiki page.
