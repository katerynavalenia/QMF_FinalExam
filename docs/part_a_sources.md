# Part A: Sources for Monetary Regime Chronology

## Primary Source: IMF Annual Report on Exchange Arrangements and Exchange Restrictions (AREAER)

The IMF AREAER is the authoritative source for de facto exchange rate regime classification.
Each year's edition classifies Ukraine's de facto regime. The classifications used here are:

| Period | IMF AREAER Year | Classification | Notes |
|--------|----------------|----------------|-------|
| Jan 2000 – Apr 2005 | 2000, 2001, 2002, 2003, 2004 | Conventional peg | Post-1998 crisis peg to USD |
| Apr 2005 – Sep 2008 | 2005, 2006, 2007 | Conventional peg | Revalued to 5.05 UAH/USD |
| Oct 2008 – Feb 2009 | 2008 | Other managed arrangement | GFC forced abandonment of peg |
| Mar 2009 – Jan 2014 | 2009, 2010, 2011, 2012, 2013 | Stabilised arrangement | De facto peg restored |
| Feb 2014 – Feb 2015 | 2014 | Other managed → Floating | Crimea annexation; transition to float |
| Mar 2015 – Dec 2021 | 2016, 2017, 2018, 2019, 2020, 2021 | Floating | Inflation targeting adopted |
| Feb 2022 – Jul 2022 | 2022 | Stabilised arrangement | Wartime peg |
| Jul 2022 – Dec 2025 | 2023, 2024 | Other managed arrangement | Managed float with IMF EFF |

- URL: https://www.imf.org/en/Publications/Annual-Report-on-Exchange-Arrangements-and-Exchange-Restrictions
- Access date: May 2026 (retrieved via IMF eLibrary)

## IMF Article IV Consultations — Ukraine

Annual IMF country reports providing policy context and staff assessment of Ukraine's exchange rate policy.

- URL: https://www.imf.org/en/Countries/UKR
- Key consultations used:
  - IMF (2008). Ukraine: 2008 Article IV Consultation — Staff Report. IMF Country Report No. 08/356
  - IMF (2014). Ukraine: 2014 Article IV Consultation — Staff Report. IMF Country Report No. 14/263
  - IMF (2017). Ukraine: 2017 Article IV Consultation — Staff Report. IMF Country Report No. 17/83
  - IMF (2019). Ukraine: 2019 Article IV Consultation — Staff Report. IMF Country Report No. 20/42
  - IMF (2021). Ukraine: 2021 Article IV Consultation — Staff Report. IMF Country Report No. 22/12
  - IMF (2023). Ukraine: 2023 Article IV Consultation and Request for EFF. IMF Country Report No. 23/132

## IMF Program Documents

- IMF (2008). Ukraine: Request for Stand-By Arrangement. IMF Country Report No. 08/357 ($16.4bn SBA)
- IMF (2015). Ukraine: Request for Extended Arrangement under the EFF. IMF Country Report No. 15/69 ($17.5bn EFF)
- IMF (2023). Ukraine: Request for Extended Arrangement under the EFF. IMF Country Report No. 23/132 ($15.6bn EFF)

## National Bank of Ukraine (NBU)

- **Official website**: https://www.bank.gov.ua/
- **NBU Annual Reports**: https://www.bank.gov.ua/en/publikatsiji
  - Coverage: 2000–2024
  - Usage: Monetary policy decisions, exchange rate interventions, inflation target path, policy rate history
- **Monetary Policy Committee**: https://www.bank.gov.ua/en/monetary-policy
  - Key decisions: IT framework adoption (Aug 2015), policy rate adjustments (2015–2021: 30% → 6%)
- **Resolution No. 18 (21 Apr 2005)**: Official revaluation to 5.05 UAH/USD
- **Resolution No. 541 (17 Sep 2015)**: Transition to inflation targeting framework
- **NBU Law of Ukraine (2015)**: Central bank independence amendment (Law No. 541-VIII)

## Official Statistics

- **Eurostat HICP database**: Monthly harmonised consumer price indices for EA-11 countries
  - Source: https://ec.europa.eu/eurostat/web/hicp
  - Usage: EA reference inflation for counterfactual comparison

- **State Statistics Service of Ukraine (Derzhstat)**: Monthly CPI data
  - Source: http://www.ukrstat.gov.ua/
  - Usage: Raw CPI index for Ukraine, converted to month-over-month and year-over-year growth

- **Federal Reserve Bank of St. Louis (FRED)**:
  - DEXUSEU: EUR/USD exchange rate — https://fred.stlouisfed.org/series/DEXUSEU
  - ECBMRRFR: ECB main refinancing rate — https://fred.stlouisfed.org/series/ECBMRRFR
  - EA19PRINTO01IXOBM: EA Industrial Production index — https://fred.stlouisfed.org/series/EA19PRINTO01IXOBM
  - Access date: runtime via API (see `01_data.py:fetch_fred_series`)

- **World Bank World Development Indicators**:
  - NY.GDP.MKTP.KD.ZG: Ukraine GDP growth (annual %)
  - Source: https://api.worldbank.org/v2/country/UKR/indicator/NY.GDP.MKTP.KD.ZG?format=json
  - Access date: runtime via API (see `01_data.py:fetch_wb_ukraine_gdp`)

## Academic References

### Optimum Currency Area Theory
- Mundell, R.A. (1961). "A theory of optimum currency areas." *American Economic Review*, 51(4): 657–665.
- Mundell, R.A. (1963). "Capital mobility and stabilization policy under fixed and flexible exchange rates." *Canadian Journal of Economics and Political Science*, 29(4): 475–485.
- Bayoumi, T. & Eichengreen, B. (1993). "Shocking aspects of European monetary integration." In *Adjustment and Growth in the European Monetary Union* (pp. 193–229). Cambridge University Press.

### Monetary Sovereignty and Credibility
- Barro, R.J. & Gordon, D.B. (1983). "Rules, discretion and reputation in a model of monetary policy." *Journal of Monetary Economics*, 12(1): 101–121.
- Giavazzi, F. & Pagano, M. (1988). "The advantage of tying one's hands: EMS discipline and central bank credibility." *European Economic Review*, 32(5): 1055–1075.
- Frankel, J.A. & Rose, A.K. (1998). "The endogeneity of the optimum currency area criteria." *The Economic Journal*, 108(449): 1009–1025.

### Exchange Rate Regime Analysis
- Calvo, G.A. & Reinhart, C.M. (2002). "Fear of floating." *The Quarterly Journal of Economics*, 117(2): 379–408.

### Ukraine-Specific Studies
- Åslund, A. (2015). *Ukraine: What Went Wrong and How to Fix It*. Peterson Institute for International Economics.
- Gorodnichenko, Y. (2014). "Ukraine's exchange rate policy." VoxEU, 10 September 2014.
  - URL: https://cepr.org/voxeu/columns/ukraines-exchange-rate-policy
