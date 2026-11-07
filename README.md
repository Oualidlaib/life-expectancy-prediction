# Life Expectancy Prediction

Predicting a country's life expectancy (2000–2015) from health, immunisation and economic indicators with scikit-learn, comparing a linear regression against a random forest.

The starting point is the WHO Life Expectancy dataset (commonly distributed on Kaggle). Its `GDP` and `Population` columns turned out to be too unreliable to use, so this project **re-collects both from external sources with web scrapers** and merges them back in.

## Why scrape GDP and population?

In the original `Life_Expectancy_Data.csv` (2,938 rows, 193 countries):

- `GDP` is missing in **448** rows and `Population` in **652**.
- `Population` is often wrong rather than just missing: more than 1,200 country-years show year-over-year swings above 50% (e.g. Afghanistan is listed at 33,736,494 in 2015 but 327,582 in 2014).

After replacing them with the scraped data, only **73** rows lack GDP and **282** lack population.

## Data

| File | Contents | Source | Produced by |
|---|---|---|---|
| `data/raw/Life_Expectancy_Data.csv` | Life expectancy plus health / immunisation / socio-economic indicators, 2000–2015 | WHO Life Expectancy dataset | original download |
| `data/external/population_data.csv` | Total population per country and year | [Perspective Monde, Université de Sherbrooke](https://perspective.usherbrooke.ca) (indicator `SP.POP.TOTL`) | `scripts/scrape_population.py` |
| `data/external/GDP_measured_in_millions.csv` | Nominal GDP in millions of USD, long format | [Wikipedia: GDP (nominal) by country, past and projected](https://en.wikipedia.org/wiki/List_of_countries_by_past_and_projected_GDP_%28nominal%29) | `scripts/scrape_gdp.py` |

Country names in the scraped files are matched to the names used in the Life Expectancy dataset, so all three merge on `(Country, Year)`.

**Coverage gaps.** Population is unavailable for 27 mostly small states (e.g. Maldives, Seychelles, Samoa, Monaco), and GDP for 6 countries (Cook Islands, Cuba, Côte d'Ivoire, North Korea, Monaco, Niue). Rows for these countries are dropped during cleaning.

## What the notebook does

`notebooks/life_expectancy.ipynb`:

1. **Explore**: feature descriptions, distributions, missing values.
2. **Clean and validate**: drop the unreliable columns, turn outliers in `Adult Mortality` and `BMI` into missing values, merge the scraped GDP and population, impute per-country medians where a country has few gaps, drop remaining incomplete rows, derive `GDP_per_capita`, and assert value ranges.
3. **Engineer features**: combine the two thinness features, log-transform skewed features, scale numeric features, one-hot encode `Status`, and remove collinear features.
4. **Model**: `LinearRegression` and `RandomForestRegressor` in scikit-learn pipelines, 80/20 split stratified by `Status`, evaluated with RMSE and MAE.

## Repository layout

```
.
├── data/
│   ├── raw/                      # Life_Expectancy_Data.csv
│   └── external/                 # scraped: population_data.csv, GDP_measured_in_millions.csv
├── notebooks/
│   └── life_expectancy.ipynb     # cleaning, features, models
├── scripts/
│   ├── scrape_population.py      # Selenium + BeautifulSoup
│   ├── scrape_gdp.py             # requests + pandas.read_html
│   └── country_codes.py          # country name -> code lookup for the population site
├── requirements.txt              # notebook dependencies
└── requirements-scraping.txt     # extra dependencies for the scrapers
```

## Getting started

Requires Python 3.9+.

```bash
git clone https://github.com/<your-username>/life-expectancy-prediction.git
cd life-expectancy-prediction

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

jupyter notebook notebooks/life_expectancy.ipynb
```

The scraped CSVs are already in the repo, so the notebook runs without scraping anything.

### Re-running the scrapers (optional)

```bash
pip install -r requirements-scraping.txt

python scripts/scrape_gdp.py          # writes data/external/GDP_measured_in_millions.csv
python scripts/scrape_population.py   # writes data/external/population_data.csv (a few minutes)
```

- The population scraper needs Google Chrome. Selenium 4.6+ downloads a matching chromedriver automatically; to use your own, set `CHROMEDRIVER_PATH`.
- Both scrapers depend on live web pages. `scrape_gdp.py` picks the Wikipedia tables by position, so it can break if the page layout changes. The committed CSVs are the snapshot used for the analysis.
