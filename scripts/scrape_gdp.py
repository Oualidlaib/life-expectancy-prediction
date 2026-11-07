"""Scrape nominal GDP (millions of USD, 2000-2015) from Wikipedia."""

from io import StringIO
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_CSV = ROOT / "data" / "external" / "GDP_measured_in_millions.csv"

URL = "https://en.wikipedia.org/wiki/List_of_countries_by_past_and_projected_GDP_(nominal)"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
}

# Position of the two tables on the page (0-indexed): 2000-2009 and 2010-2019.
# NOTE: this is positional, so it breaks if Wikipedia reorders the page.
TABLE_2000S_INDEX = 3
TABLE_2010S_INDEX = 4

COUNTRY_COL = "Country / territory"
YEARS_2000S = [str(y) for y in range(2000, 2010)]
YEARS_2010S = [str(y) for y in range(2010, 2016)]
ALL_YEARS = YEARS_2000S + YEARS_2010S

# Wikipedia name -> name used in the Life Expectancy dataset.
NAME_FIXES = {
    "Bolivia": "Bolivia (Plurinational State of)",
    "Brunei": "Brunei Darussalam",
    "Republic of the Congo": "Congo",
    "Cape Verde": "Cabo Verde",
    "Czech Republic": "Czechia",
    "Federated States of Micronesia": "Micronesia (Federated States of)",
    "United Kingdom": "United Kingdom of Great Britain and Northern Ireland",
    "Iran": "Iran (Islamic Republic of)",
    "South Korea": "Republic of Korea",
    "Laos": "Lao People's Democratic Republic",
    "Moldova": "Republic of Moldova",
    "North Macedonia": "The former Yugoslav republic of Macedonia",
    "Russia": "Russian Federation",
    "São Tomé and Príncipe": "Sao Tome and Principe",
    "Eswatini": "Swaziland",
    "Syria": "Syrian Arab Republic",
    "Tanzania": "United Republic of Tanzania",
    "United States": "United States of America",
    "Venezuela": "Venezuela (Bolivarian Republic of)",
    "Vietnam": "Viet Nam",
}

# Territories / entities that are not in the Life Expectancy dataset.
# ("Ivory Coast" is dropped here too, so Côte d'Ivoire has no GDP rows.)
EXCLUDED_COUNTRIES = [
    "Palestine", "Taiwan", "Puerto Rico", "Macau", "Liechtenstein",
    "Kosovo", "Hong Kong", "Ivory Coast", "Andorra", "Aruba",
]


def fetch_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    response = requests.get(URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    tables = soup.find_all("table")

    table_2000s = pd.read_html(StringIO(str(tables[TABLE_2000S_INDEX])))[0]
    table_2010s = pd.read_html(StringIO(str(tables[TABLE_2010S_INDEX])))[0]
    return table_2000s, table_2010s


def build_gdp_long(table_2000s: pd.DataFrame, table_2010s: pd.DataFrame) -> pd.DataFrame:
    """Combine the two wide Wikipedia tables into one long (Country, Year, GDP) frame."""
    table_2000s = table_2000s.loc[:, [COUNTRY_COL] + YEARS_2000S]
    table_2010s = table_2010s.loc[:, [COUNTRY_COL] + YEARS_2010S]

    merged = pd.merge(table_2000s, table_2010s, on=COUNTRY_COL, how="inner")
    merged = merged.rename(columns={COUNTRY_COL: "Country"})

    merged = merged[~merged["Country"].isin(EXCLUDED_COUNTRIES)].copy()
    merged["Country"] = merged["Country"].replace(NAME_FIXES)

    return pd.melt(
        merged,
        id_vars=["Country"],
        value_vars=ALL_YEARS,
        var_name="Year",
        value_name="GDP",
    )


def main() -> None:
    table_2000s, table_2010s = fetch_tables()
    gdp_long = build_gdp_long(table_2000s, table_2010s)

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    
    gdp_long.to_csv(OUTPUT_CSV)
    print(f"Saved {len(gdp_long)} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
