# Data Sources Documentation

## Repository Data (Provided)

### ECB HICP Panel
- **File**: `data/raw/data_ecb_hicp_panel.csv`
- **Source**: ECB Data Portal (originally from GitHub repository: https://github.com/skimeur/pioneer-detection-method)
- **Content**: Monthly Harmonised Index of Consumer Prices (HICP), year-on-year percentage change
- **Countries**: AT, BE, DE, ES, FI, FR, GR, IE, IT, NL, PT (11 Euro Area countries)
- **Coverage**: January 2000 – December 2025 (312 months)
- **Access date**: Downloaded with repository (pre-committed)
- **Format**: Wide-format (columns: TIME_PERIOD + country codes)
- **Usage**: Panel inflation data for PCA common factor extraction and EA average inflation

### Ukraine CPI Raw
- **File**: `data/raw/data_ukraine_cpi_raw.csv`
- **Source**: State Statistics Service of Ukraine (SSSU) via SDMX
- **Content**: Monthly Consumer Price Index, month-on-month index (previous month = 100)
- **Coverage**: February 2005 – July 2025
- **Access date**: Downloaded with repository (pre-committed)
- **Format**: SDMX long-format (columns: TIME_PERIOD, OBS_VALUE)
- **Usage**: Transformed to year-on-year inflation via 12-month chaining:
  ```
  yoy_t = (prod_{j=0}^{11} CPI_{t-j} / 100 - 1) * 100
  ```

## External Data (Downloaded Programmatically)

### Ukraine GDP Growth (Annual)
- **Variable**: NY.GDP.MKTP.KD.ZG — GDP growth (annual %)
- **Source**: World Bank API
- **URL**: `https://api.worldbank.org/v2/country/UKR/indicator/NY.GDP.MKTP.KD.ZG?format=json&per_page=100`
- **Coverage**: 1988–2024 (37 years)
- **Access date**: Downloaded at runtime (see `01_data.py:fetch_wb_ukraine_gdp`)
- **Fallback**: Cached to `data/raw/ua_gdp_growth.csv`
- **Usage**: Interpolated to monthly frequency via quadratic spline to serve as output proxy in bivariate SVAR
- **Citation**: World Bank, World Development Indicators

### EUR/USD Exchange Rate
- **Variable**: DEXUSEU — U.S. Dollars to Euro Spot Exchange Rate
- **Source**: Federal Reserve Bank of St. Louis (FRED)
- **URL**: `https://fred.stlouisfed.org/series/DEXUSEU`
- **Download**: `https://fred.stlouisfed.org/graph/fredgraph.csv?id=DEXUSEU&cosd=2000-01-01&coed=2025-12-01`
- **Coverage**: Daily, Jan 2000 – Dec 2025 (converted to monthly, last business day)
- **Access date**: Downloaded at runtime (see `01_data.py:fetch_fred_series`)
- **Fallback**: Cached to `data/raw/EUR_USD.csv`
- **Usage**: Supplementary macro series; exchange rate effects captured through VAR dynamics
- **Citation**: FRED, Federal Reserve Bank of St. Louis

### ECB Main Refinancing Rate
- **Variable**: ECBMRRFR — ECB Main Refinancing Operations Rate: Fixed Rate Tenders
- **Source**: Federal Reserve Bank of St. Louis (FRED)
- **URL**: `https://fred.stlouisfed.org/series/ECBMRRFR`
- **Download**: `https://fred.stlouisfed.org/graph/fredgraph.csv?id=ECBMRRFR&cosd=2000-01-01&coed=2025-12-01`
- **Coverage**: Daily, Jan 2000 – Dec 2025 (converted to monthly, forward-filled)
- **Access date**: Downloaded at runtime (see `01_data.py:fetch_fred_series`)
- **Fallback**: Cached to `data/raw/ECB_MRR.csv`
- **Usage**: Supplementary macro series; monetary policy stance indicator
- **Citation**: FRED, Federal Reserve Bank of St. Louis

### Attempted but Unavailable

The following official data sources were attempted but their APIs have changed:

#### Euro Area Industrial Production
- **Source**: Eurostat STS_INPR_M
- **Status**: HTTP 400
- **Alternative**: The code falls back to using inflation-only data for the EA VAR

#### EUR/UAH Exchange Rate (ECB Official API)
- **Source**: ECB SDMX  
- **Status**: HTTP 404
- **Alternative**: EUR/USD sourced from FRED as a proxy

#### ECB Main Refinancing Rate (ECB Official API)
- **Source**: ECB SDMX
- **Status**: HTTP 404  
- **Alternative**: Rate sourced from FRED (ECBMRRFR series)

## Data Transformations

| Transformation | Method | Location |
|----------------|--------|----------|
| Ukraine CPI m/m → y/y | 12-month chain product: `rolling(12).apply(prod) - 1` | `01_data.py:cpi_mom_to_yoy()` |
| Annual GDP → monthly IP proxy | Quadratic interpolation | `01_data.py:interpolate_gdp_to_monthly()` |
| Date harmonisation | All series converted to month-start timestamps `to_timestamp(how='start')` | `01_data.py` |
| Inflation standardisation | All inflation as year-on-year percentage | Throughout |
| EA IP growth computation | 12-month percent change `pct_change(12) * 100` | `01_data.py:compute_ip_growth()` |

## Notes

- The 12-month rolling transformation for Ukraine CPI means the first 11 observations of each series are lost
- Missing values for Ukraine GDP (before 1988) are not an issue since the sample starts at 2000
- The quadratic interpolation of annual GDP to monthly is a limitation acknowledged in the analysis; monthly IP data would be preferable
