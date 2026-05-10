Explore GitHub repository data

Research data sources and methods



Fetched 2 resources





Fetched 3 resources

Fetched 3 resources



Fetched 2 resources



Fetched https://raw.githubusercontent.com/skimeur/pioneer-detection-method/main/ecb_hicp_panel_var_granger.py









Fetched https://www.imf.org/en/Publications/Annual-Report-on-Exchange-Arrangements-and-Exchange-Restrictions/Issues/2024/10/04/Annual-Report-on-Exchange-Arrangements-and-Exchange-Restrictions-2023-702427

Fetched 2 resources

Fetched 2 resources

Fetched https://en.wikipedia.org/wiki/Optimum_currency_area







Fetched https://scholar.google.com/scholar?q=Bayoumi+Eichengreen+1994+structural+VAR+demand+supply+shocks

Fetched https://scholar.google.com/scholar?q=Ciccarelli+Mojon+2010+global+inflation+common+factor

Fetched https://data.imf.org/en/Resource-Pages/IMF-API





Fetched https://data.ecb.europa.eu/help/api/overview

Fetched https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation

Now I have thorough context on the exam requirements, available data, and the repository structure. Let me create the plan. 

Created memory file [](file:///c%3A/Users/katri/AppData/Roaming/Code/User/workspaceStorage/ae4138d36a3591895e4f9c1d53c57063/GitHub.copilot-chat/memory-tool/memories/Mjk1ZGJiZDUtOGEzNS00M2ViLTgzYTktNDYzODBhYjVkOGU2/plan.md)

Here is the full plan:

---

## Plan: QMF Exam — Counterfactual Ukraine Inflation

Build a counterfactual inflation path for Ukraine under hypothetical Euro Area membership, using a **Bayoumi–Eichengreen bivariate SVAR** (Blanchard-Quah identification) as the core method, complemented by a **Ciccarelli–Mojon common factor model** for robustness. Part A documents Ukraine's monetary regime chronology. Part B constructs and interprets the counterfactual. Language: Python.

---

### Phase 1: Environment & Data Setup

**Step 1. Project scaffolding**
- Clone `https://github.com/skimeur/pioneer-detection-method`
- Create folders: `data/raw/`, `data/processed/`, `src/`, `output/`, `docs/`
- Python environment: `pandas`, `numpy`, `matplotlib`, `statsmodels`, `scipy`, `sklearn`, `requests`

**Step 2. Load & transform repository data**
- Use ecb_hicp_panel_var_granger.py as template for data loading
- **ECB HICP panel** (`data_ecb_hicp_panel.csv`): wide-format, y/y % for 11 EA countries — ready to use
- **Ukraine CPI** (`data_ukraine_cpi_raw.csv`): SDMX long-format, `OBS_VALUE` = m/m index (prev month = 100). Chain 12 monthly factors to compute y/y inflation: $\text{yoy}_t = \left(\prod_{j=0}^{11} \frac{\text{CPI}_{t-j}}{100} - 1\right) \times 100$

**Step 3. Source external data** *(parallel with Step 2)*
| Variable | Source | Method |
|---|---|---|
| Industrial Production (Ukraine + EA) | Eurostat SDMX + IMF IFS | Programmatic API |
| UAH/USD exchange rate | ECB SDMX (`EXR/M.UAH.EUR.SP00.A`) | Programmatic |
| ECB main refi rate | ECB SDMX (`FM/B.U2.EUR.4F.KR.MRR_FR.LEV`) | Programmatic |
| NBU policy rate | NBU website | Manual CSV download |
| Energy price index | IMF PCPS or World Bank Pink Sheet | Programmatic/XLS |

**Step 4. Data harmonisation**
- All series to monthly frequency; interpolate quarterly GDP if using it instead of IP
- All inflation as y/y %; handle missing values (especially 2014–15 conflict gaps)
- Master merged DataFrame: rows = months (2005–2025), columns = all variables

---

### Phase 2: Part A — Monetary Regime Chronology (30%)

**Step 5. Construct regime summary table**

| Period | UAH/USD | De Facto Regime | Key Events | Genuine Sovereignty? |
|---|---|---|---|---|
| 2000–Apr 2005 | ~5.3–5.4 | Conventional peg | Post-1998 recovery | No |
| Apr 2005–Sep 2008 | 5.05 | Conventional peg | Official fix | No |
| Oct 2008–Feb 2009 | 5.05→~7.7 | Free fall | GFC, 38% depreciation | Brief (during deval) |
| Mar 2009–Jan 2014 | ~7.7–8.0 | Stabilised arrangement | Post-GFC peg | No |
| Feb 2014–Feb 2015 | 8→~33 | Floating / other managed | Crimea, Donbas; 70% depreciation; capital controls | Yes (forced float) |
| Mar 2015–Dec 2021 | 21–28 | Floating (IT from 2016) | IT target 5%±1pp | Yes |
| Feb–Jul 2022 | 29.25 | Wartime peg | Full-scale invasion; capital controls | No |
| Jul 2022–present | 36.57→~44 | Other managed | Stepped deval, gradual crawl | Limited |

Sources: IMF AREAER reports, NBU publications, Calvo & Reinhart (2002) framework.

**Step 6. Write argument paragraph**
Key point: genuine monetary sovereignty existed mainly during (a) devaluation episodes, (b) 2016–2021 IT period. During peg periods, joining the EA would have merely switched the anchor from USD to EUR — a smaller treatment effect. The counterfactual must reflect this **time-varying treatment intensity**.

**Step 7. Part A deliverables**
- Summary table (generate programmatically or in LaTeX)
- Argument paragraph
- Full source citations

---

### Phase 3: Part B — Counterfactual Construction (50%)

#### Core Method: Bayoumi–Eichengreen SVAR with Shock Replacement

**Step 8. Estimate bivariate SVARs**
- For Ukraine and the EA aggregate: VAR in $(\Delta y_t, \pi_t)$ using monthly IP growth + inflation
- BIC lag selection; confirm stationarity (ADF tests)
- Apply **Blanchard-Quah long-run restriction**: supply shocks have permanent output effects; demand shocks do not
- Extract structural shocks $\varepsilon^s_t$ (supply) and $\varepsilon^d_t$ (demand) for both Ukraine and EA
- Implementation: `statsmodels.tsa.vector_ar` or manual via Cholesky of the long-run impact matrix

**Step 9. Compute shock correlations** *(OCA assessment, links to Part A)*
- Correlate Ukraine vs. EA supply shocks and demand shocks
- Report by sub-period (peg / float / IT) to show time-varying synchronisation
- Visualise shock series

**Step 10. Construct counterfactual via shock replacement**
- **Identification**: Under EA membership, Ukraine's demand shocks = EA demand shocks (ECB sets monetary policy); supply shocks remain Ukraine's own (real structure unchanged)
- From structural MA representation: $\pi_t = C_{21}(L)\varepsilon^s_t + C_{22}(L)\varepsilon^d_t$
- Replace $\varepsilon^d_{\text{UKR},t}$ with $\varepsilon^d_{\text{EA},t}$
- Simulate: $\pi^{CF}_t = C_{21}(L)\varepsilon^s_{\text{UKR},t} + C_{22}(L)\varepsilon^d_{\text{EA},t}$

#### Complementary Method: Ciccarelli–Mojon Common Factor

**Step 11. Extract EA common inflation factor** *(parallel with Steps 8–10)*
- Standardise EA-11 inflation panel (zero mean, unit variance)
- First principal component via PCA = EA common inflation factor $F^{EA}_t$
- Verify: should explain >50% of EA inflation variance

**Step 12. Estimate Ukraine's loading & second counterfactual**
- Regress Ukraine inflation on $F^{EA}_t$ during "quiet" co-movement periods (e.g., 2009–2013 peg)
- Counterfactual: $\hat{\pi}^{CF}_t = \hat{\lambda}_{\text{UKR}} \cdot F^{EA}_t$
- This provides a cross-check on the SVAR counterfactual

**Step 13. Consistency checks with Part A**
- During peg periods: CF ≈ actual (small treatment effect) ✓
- During devaluations: CF ≠ actual (large treatment effect) ✓
- Gap larger pre-2016 than post-2016 (credibility sanity check from exam) ✓
- CF ≠ simple EA mean (exam explicitly forbids this) ✓

---

### Phase 4: Output & Interpretation

**Step 14. Create main figure**
- Two time series on same axes: **solid** = Ukraine actual y/y inflation; **dashed** = SVAR counterfactual
- Optional: dotted line for Ciccarelli–Mojon counterfactual
- Shaded bands for crisis episodes (GFC, Crimea, 2022 invasion)
- Vertical dashed lines for regime changes
- Professional formatting: legend, axis labels, gridlines

**Step 15. Write interpretation paragraph**
- 2008–09: devaluation acted as shock absorber; without it, likely deeper real adjustment
- 2014–15: massive inflation spike avoided under EA, but internal devaluation cost (unemployment, deflation — Greek scenario)
- 2022: wartime peg meant Ukraine wasn't exercising sovereignty anyway; but De Grauwe (2012) channel: might have faced sovereign debt crisis instead
- Overall: monetary sovereignty = shock absorber at cost of higher average inflation and lower credibility

**Step 16. Code documentation & reproducibility**
- Numbered scripts: `01_data.py`, `02_part_a.py`, `03_svar.py`, `04_factor.py`, `05_figures.py`
- All external data downloads programmatic (with CSV fallbacks)
- `requirements.txt` with pinned versions
- Clear comments explaining identification strategy at each step

---

### Relevant Files
- `data_ecb_hicp_panel.csv` — EA HICP panel (wide, y/y %, 11 countries, 2000–2025). Use directly.
- `data_ukraine_cpi_raw.csv` — Ukraine CPI (SDMX long, m/m index). Transform via 12-month chaining.
- `ecb_hicp_panel_var_granger.py` — Reference template: data loading, CPI transform, ADF, Granger, VAR.

### Verification
1. **Data**: Plot raw series; verify Ukraine inflation matches known values (~25% in 2015, ~27% in 2022, ~5% in 2019)
2. **Unit roots**: ADF on all series; inflation should be I(0) or I(1); IP growth I(0)
3. **VAR diagnostics**: Residual autocorrelation (Portmanteau), stability (eigenvalues), lag selection (BIC)
4. **BQ check**: Long-run impact matrix has correct zero restriction
5. **CF sanity**: Lower average than actual; larger gap pre-2016; no extreme deval spikes; ≠ EA simple mean
6. **Factor check**: First PC explains >50% variance; loading λ is significant
7. **Reproducibility**: Full pipeline runs from clean clone

### Decisions
- **Primary method**: Bayoumi-Eichengreen SVAR + Blanchard-Quah → shock replacement (satisfies exam's SVAR/LP requirement)
- **Secondary**: Ciccarelli-Mojon PCA factor model (robustness)
- **Output proxy**: Monthly Industrial Production (better resolution than quarterly GDP)
- **Sample**: 2005–2025 (constrained by Ukraine CPI start date)
- **Excluded**: Synthetic control (no clean treatment date; exam flags this difficulty); Local projections (SVAR is more natural for counterfactual construction, LP could be added as extension)