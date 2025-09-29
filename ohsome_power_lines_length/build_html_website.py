import pandas as pd

def iso2_to_flag(iso2: str) -> str:
    iso2 = iso2.upper()
    if iso2 == "XK":
        return "🇽🇰"
    if len(iso2) == 2 and iso2.isalpha():
        return "".join(chr(127397 + ord(c)) for c in iso2)
    return ""

def clamp(x):
    return max(0, min(x, 255))

def rgb_to_hex(r, g, b):
    return "#{0:02x}{1:02x}{2:02x}".format(clamp(r), clamp(g), clamp(b))

def get_color_evolution(evolution_value):
    if str(evolution_value).lower() == "nan":
        return rgb_to_hex(200, 200, 200)
    if evolution_value <= 0:
        return rgb_to_hex(200, 200, 200)
    else:
        pctgreen = min(25, evolution_value) / 25
        return rgb_to_hex(round(170 * (1 - pctgreen)), round(255 - 75 * pctgreen), 0)

def intify(value):
    try:
        return round(float(value))
    except (ValueError, TypeError):
        return "-"

def compute_evolution(value, base, returntype):
    try:
        val_evolution = ((value - base) / base) * 100
        txt_evolution = "{:0.1f}".format(val_evolution) + " %"
    except (ValueError, TypeError, ZeroDivisionError):
        val_evolution = 0
        txt_evolution = "-"
    return txt_evolution if returntype is str else val_evolution

# === Load Data ===
merge_file_list = [
    "countries_ohsome_power_line_length_km_1.csv",
    "countries_ohsome_power_line_length_km_3.csv"
]

df0 = pd.read_csv(merge_file_list[0])
for file in merge_file_list[1:]:
    dft = pd.read_csv(file)
    df0 = df0.merge(dft, on="isoa2")

list_dates = sorted([col for col in df0.columns if col != "isoa2"])
dates_to_exclude_from_html = ["2025-01-01", "2025-04-06"]
list_dates_html = [d for d in list_dates if d not in dates_to_exclude_from_html]

df_data = pd.read_csv("wikidata_countries_info_formatted.csv")
df = df_data.merge(df0, left_on="codeiso2", right_on="isoa2")

# === Compute Evolution ===
for myd in list_dates:
    df[myd + "/val_evolution"] = df.apply(lambda x: compute_evolution(x[myd], x["2025-01-01"], float), axis=1)
    df[myd + "/txt_evolution"] = df.apply(lambda x: compute_evolution(x[myd], x["2025-01-01"], str), axis=1)

# === Generate MediaWiki Table ===
colsname = " !! ".join([
    f"Power line length (in km)<br>on {myd}" + (" !! Growth since<br>2025-01-01" if myd != '2025-01-01' else "")
    for myd in list_dates
])
wikistring = "{| class='wikitable sortable' \n|-\n! Country !! " + colsname + " \n"

for row in df.to_dict(orient='records'):
    base20250101 = row.get('2025-01-01')
    if intify(base20250101) == "-" or intify(base20250101) == 0:
        continue

    extracols = " || ".join([
        f"{intify(row.get(myd))} \n|style='background:{get_color_evolution(row.get(myd + '/val_evolution'))}'| {row.get(myd + '/txt_evolution')}"
        for myd in list_dates if myd != '2025-01-01'
    ])
    wikistring += f"|-\n| {row.get('name')} || {intify(base20250101)} || {extracols}\n"

wikistring += "\n|}"

with open("power_line_length_wikitable.txt", "w") as text_file:
    text_file.write(wikistring)

# === Generate HTML Table ===
html_header = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Power Line Length Evolution</title>
    <style>
        table.sortable {
            border-collapse: collapse;
            width: 100%;
            font-family: sans-serif;
        }
        .sortable th, .sortable td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: center;
        }
        .sortable th {
            background-color: #f2f2f2;
            cursor: pointer;
        }
        .sortable th:hover {
            background-color: #e0e0e0;
        }
    </style>
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const getCellValue = (tr, idx) =>
                tr.children[idx].getAttribute('data-sort') || tr.children[idx].innerText;

            const comparer = (idx, asc) => (a, b) => {
                const v1 = getCellValue(asc ? a : b, idx);
                const v2 = getCellValue(asc ? b : a, idx);
                const f1 = parseFloat(v1);
                const f2 = parseFloat(v2);
                return (!isNaN(f1) && !isNaN(f2)) ? f1 - f2 : v1.localeCompare(v2);
            };

            document.querySelectorAll('table.sortable th').forEach(th => {
                th.addEventListener('click', () => {
                    const table = th.closest('table');
                    const tbody = table.querySelector('tbody');
                    const index = Array.from(th.parentNode.children).indexOf(th);
                    const rows = Array.from(tbody.querySelectorAll('tr'));
                    const asc = !th.asc;
                    th.asc = asc;
                    rows.sort(comparer(index, asc));
                    rows.forEach(tr => tbody.appendChild(tr));
                });
            });
        });
    </script>
</head>
<body>
<p style="font-family: sans-serif; font-size: 14px; margin-bottom: 10px;">
    🔽 Click on any column header to sort the table.
</p>
<table class="sortable" id="sortable-table">
<thead>
<tr>
<th>Country</th>
"""

for myd in list_dates_html:
    html_header += f"<th>Power line length (km)<br>{myd}</th>"
    html_header += f"<th>Growth since 2025-01-01 (%)</th>"
    html_header += f"<th>Growth since 2025-01-01 (km)</th>"
html_header += "</tr></thead>\n<tbody>\n"

# ✅ Sort by latest available relative growth (%)
latest_date = sorted(list_dates_html)[-1]
df = df.sort_values(by=f"{latest_date}/val_evolution", ascending=False)

html_rows = ""

for row in df.to_dict(orient='records'):
    base_value = row.get("2025-01-01")
    if intify(base_value) == "-" or intify(base_value) == 0:
        continue

    html_row = f"<tr><td>{row.get('name')} {iso2_to_flag(row.get('codeiso2'))}</td>"

    for myd in list_dates_html:
        current_value = row.get(myd)
        pct_growth = row.get(myd + "/txt_evolution").replace("%", "").strip()
        evol_val = row.get(myd + "/val_evolution")
        color = get_color_evolution(evol_val)

        # Compute absolute growth
        if isinstance(current_value, (int, float)) and isinstance(base_value, (int, float)):
            try:
                km_growth_val = current_value - base_value
                km_growth = round(km_growth_val)
            except:
                km_growth_val = 0
                km_growth = "-"
        else:
            km_growth_val = 0
            km_growth = "-"

        html_row += f"<td data-sort='{current_value}'>{intify(current_value)}</td>"
        html_row += f"<td style='background:{color}' data-sort='{evol_val}'>{pct_growth} %</td>"
        html_row += f"<td style='background:{color}' data-sort='{km_growth_val}'>{km_growth}</td>"

    html_row += "</tr>\n"
    html_rows += html_row

html_footer = """
</tbody>
</table>
</body>
</html>
"""

with open("power_line_length_table.html", "w") as html_file:
    html_file.write(html_header + html_rows + html_footer)

print(f"✅ HTML and MediaWiki tables generated. HTML table is fully sortable. Default sorting by relative growth on {latest_date}.")
