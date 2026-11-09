"""Scrape yearly total population (2000-2015) for every country in the Life Expectancy dataset."""

import os
import time
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select, WebDriverWait

from country_codes import COUNTRY_CODES

ROOT = Path(__file__).resolve().parents[1]
LIFE_EXPECTANCY_CSV = ROOT / "data" / "raw" / "Life_Expectancy_Data.csv"
OUTPUT_CSV = ROOT / "data" / "external" / "population_data.csv"

START_YEAR, END_YEAR = 2000, 2015

URL = (
    "https://perspective.usherbrooke.ca/bilan/servlet/BMTendanceStatPays"
    "?codeTheme=1&codeStat=SP.POP.TOTL&codePays=AUS&optionsPeriodes=Aucune"
    "&codeTheme2=1&codeStat2=x&codePays2=AFG&optionsDetPeriodes=avecNomP"
)

# Countries in the Life Expectancy dataset that the source site does not cover
COUNTRIES_TO_EXCLUDE = (
    "Dominica", "Antigua and Barbuda", "Barbados", "Belize", "Brunei Darussalam",
    "Cook Islands", "Grenada", "Maldives", "Marshall Islands",
    "Micronesia (Federated States of)", "Monaco", "Nauru", "Niue",
    "Palau", "Saint Kitts and Nevis", "Saint Lucia",
    "Saint Vincent and the Grenadines", "Samoa", "San Marino",
    "Sao Tome and Principe", "Seychelles", "Solomon Islands", "Tonga", "Tuvalu",
    "United Republic of Tanzania", "Vanuatu", "Timor-Leste",
)


def make_driver() -> webdriver.Chrome:
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH")
    service = Service(executable_path=chromedriver_path) if chromedriver_path else Service()
    return webdriver.Chrome(service=service)


def parse_population_table(html: str) -> list[tuple[int, int]]:
    """Return [(year, population), ...] from the page's #listeDonnee table."""
    soup = BeautifulSoup(html, "html.parser")
    tds = soup.find("tbody", {"id": "listeDonnee"}).find_all("td")

    rows = []
    
    for i in range(0, len(tds), 3):
        year = int(tds[i].get_text(strip=True))
        population = tds[i + 1].get_text(strip=True).replace("\xa0", "").replace(" ", "")
        rows.append((year, int(population)))
    return rows


def scrape_country(driver: webdriver.Chrome, country_name: str) -> list[tuple[str, int, int]]:
    select_element = WebDriverWait(driver, 20).until(
        ec.presence_of_element_located((By.NAME, "codePays"))
    )
    Select(select_element).select_by_value(COUNTRY_CODES[country_name])

    WebDriverWait(driver, 20).until(ec.presence_of_element_located((By.ID, "listeDonnee")))
    time.sleep(2)  

    rows = parse_population_table(driver.page_source)
    return [
        (country_name, year, population)
        for year, population in rows
        if START_YEAR <= year <= END_YEAR
    ]


def main() -> None:
    country_names = pd.read_csv(LIFE_EXPECTANCY_CSV)["Country"].unique().tolist()

    driver = make_driver()
    data = []
    try:
        driver.get(URL)
        for country_name in country_names:
            if country_name in COUNTRIES_TO_EXCLUDE:
                continue
            country_rows = scrape_country(driver, country_name)
            print(f"{country_name}: {len(country_rows)} years")
            data.extend(country_rows)
            time.sleep(1)
    finally:
        driver.quit()

    df = pd.DataFrame(data, columns=["Country", "Year", "Population"])
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved {len(df)} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
