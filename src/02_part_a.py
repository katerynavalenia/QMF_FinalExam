import os
import numpy as np
import pandas as pd

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'output')
DOCS_DIR = os.path.join(PROJECT_DIR, 'docs')
PROC_DIR = os.path.join(PROJECT_DIR, 'data', 'processed')
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

EA_COUNTRIES = ['AT', 'BE', 'DE', 'ES', 'FI', 'FR', 'GR', 'IE', 'IT', 'NL', 'PT']

REGIME_TABLE = [
    {
        'period': 'Jan 2000 – Apr 2005',
        'start': '2000-01-01',
        'end': '2005-04-30',
        'uah_usd': '~5.3–5.4',
        'de_facto_regime': 'Conventional peg to USD',
        'imf_classification': 'Conventional peg (AREAER 2000–2004)',
        'key_events': 'Post-1998 crisis stabilisation. NBU maintained narrow band around 5.3–5.4 UAH/USD. Extensive FX intervention.',
        'capital_controls': 'Moderate (surrender requirements for exporters)',
        'genuine_sovereignty': 0.0,
        'sovereignty_rationale': 'Exchange rate anchor constrained monetary policy via impossible trinity.'
    },
    {
        'period': 'Apr 2005 – Sep 2008',
        'start': '2005-05-01',
        'end': '2008-09-30',
        'uah_usd': '5.05 (fixed)',
        'de_facto_regime': 'Conventional peg to USD',
        'imf_classification': 'Conventional peg (AREAER 2005–2007)',
        'key_events': 'NBU officially revalued to 5.05 UAH/USD (21 Apr 2005). Rapid credit growth, real estate bubble.',
        'capital_controls': 'Moderate (gradually eased)',
        'genuine_sovereignty': 0.0,
        'sovereignty_rationale': 'Rigid peg eliminated monetary policy independence.'
    },
    {
        'period': 'Oct 2008 – Feb 2009',
        'start': '2008-10-01',
        'end': '2009-02-28',
        'uah_usd': '5.05 → ~7.7 (≈38% deprec.)',
        'de_facto_regime': 'Free fall / managed float',
        'imf_classification': 'Other managed arrangement (AREAER 2008)',
        'key_events': 'GFC. Steel export collapse, capital flight. IMF SBA ($16.4bn, Nov 2008). Forced peg abandonment.',
        'capital_controls': 'Tightened (temporary FX purchase restrictions)',
        'genuine_sovereignty': 0.5,
        'sovereignty_rationale': 'Forced devaluation exercised exchange-rate adjustment unavailable under EA membership. But crisis response, not discretionary policy.'
    },
    {
        'period': 'Mar 2009 – Jan 2014',
        'start': '2009-03-01',
        'end': '2014-01-31',
        'uah_usd': '~7.7–8.0',
        'de_facto_regime': 'Stabilised arrangement (de facto peg)',
        'imf_classification': 'Stabilised arrangement (AREAER 2009–2013)',
        'key_events': 'De facto peg restored at ~8.0. Multiple IMF programs. Reserve depletion. Pre-Euromaidan tensions.',
        'capital_controls': 'Moderate (mandatory FX surrender, repatriation rules)',
        'genuine_sovereignty': 0.0,
        'sovereignty_rationale': 'De facto dollar peg restored. Calvo & Reinhart (2002) fear of floating diagnosis applies.'
    },
    {
        'period': 'Feb 2014 – Feb 2015',
        'start': '2014-02-01',
        'end': '2015-02-28',
        'uah_usd': '8.0 → ~33 (≈76% deprec.)',
        'de_facto_regime': 'Free fall / floating',
        'imf_classification': 'Other managed → Floating (AREAER 2014)',
        'key_events': 'Euromaidan, Crimea annexation (Mar 2014), Donbas conflict. Massive capital flight. 96 banks liquidated.',
        'capital_controls': 'Severe (mandatory 75% FX surrender, ban on dividend repatriation)',
        'genuine_sovereignty': 1.0,
        'sovereignty_rationale': 'Primary exchange-rate buffer that EA membership would eliminate. Without it, internal devaluation (Greek scenario).'
    },
    {
        'period': 'Mar 2015 – Dec 2021',
        'start': '2015-03-01',
        'end': '2021-12-31',
        'uah_usd': '~21–28 (fluctuating)',
        'de_facto_regime': 'Floating (inflation targeting from 2016)',
        'imf_classification': 'Floating (AREAER 2016–2021)',
        'key_events': 'IT framework adopted Aug 2015, operational 2016. Target 5%±1pp. Gradual disinflation from ~43% to ~2.7% (2020).',
        'capital_controls': 'Gradually eased (partial liberalisation 2017–2019)',
        'genuine_sovereignty': 0.8,
        'sovereignty_rationale': 'First period of genuine discretionary monetary policy. EA membership would represent the largest change here.'
    },
    {
        'period': 'Feb 2022 – Jul 2022',
        'start': '2022-02-01',
        'end': '2022-07-31',
        'uah_usd': '29.25 (wartime fix)',
        'de_facto_regime': 'Conventional peg (wartime)',
        'imf_classification': 'Stabilised arrangement (AREAER 2022)',
        'key_events': 'Full-scale invasion (24 Feb 2022). NBU fixed rate at 29.25. Policy rate raised from 10% to 25%. Martial law.',
        'capital_controls': 'Severe (ban on FX purchases, 100% surrender, withdrawal limits)',
        'genuine_sovereignty': 0.0,
        'sovereignty_rationale': 'Wartime peg eliminated exchange-rate flexibility. Regime resembled conventional peg.'
    },
    {
        'period': 'Jul 2022 – Dec 2025',
        'start': '2022-08-01',
        'end': '2025-12-31',
        'uah_usd': '36.57 → ~44 (managed deprec.)',
        'de_facto_regime': 'Other managed arrangement',
        'imf_classification': 'Other managed arrangement (AREAER 2023–2024)',
        'key_events': 'Stepped devaluation to 36.57 (21 Jul 2022, ≈25%). Gradual crawl. IMF EFF ($15.6bn, Mar 2023).',
        'capital_controls': 'Gradually easing (FX surrender reduced to 50%)',
        'genuine_sovereignty': 0.4,
        'sovereignty_rationale': 'Partial return to managed flexibility. Exchange rate management constrains full independence.'
    },
]


def compute_regime_statistics(regime_df):
    """Enrich regime table with quantitative metrics from master panel."""
    mp_path = os.path.join(PROC_DIR, 'master_panel.csv')
    mp = pd.read_csv(mp_path, index_col=0, parse_dates=True)
    ea_infl = mp[EA_COUNTRIES].mean(axis=1)

    stats = []
    for _, r in regime_df.iterrows():
        mask = (mp.index >= pd.Timestamp(r['start'])) & (mp.index <= pd.Timestamp(r['end']))
        ua_sub = mp.loc[mask, 'UA'].dropna()
        ea_sub = ea_infl.loc[mask].dropna()
        total_months = mask.sum()
        ua_months = len(ua_sub)
        stats.append({
            'months_total': total_months,
            'months_with_data': ua_months,
            'avg_UA_inflation': round(ua_sub.mean(), 1) if ua_months > 0 else np.nan,
            'sd_UA_inflation': round(ua_sub.std(), 1) if ua_months > 1 else np.nan,
            'max_UA_inflation': round(ua_sub.max(), 1) if ua_months > 0 else np.nan,
            'avg_EA_inflation': round(ea_sub.mean(), 1) if len(ea_sub) > 0 else np.nan,
            'inflation_differential': round(ua_sub.mean() - ea_sub.mean(), 1) if ua_months > 0 and len(ea_sub) > 0 else np.nan,
        })
    stats_df = pd.DataFrame(stats)
    return pd.concat([regime_df.reset_index(drop=True), stats_df], axis=1)


def build_regime_table():
    return pd.DataFrame(REGIME_TABLE)


def build_treatment_intensity(start='2000-01-01', end='2025-12-01'):
    dates = pd.date_range(start=start, end=end, freq='MS')
    intensity = pd.Series(0.0, index=dates, name='treatment_intensity')
    for regime in REGIME_TABLE:
        mask = (dates >= pd.Timestamp(regime['start'])) & (dates <= pd.Timestamp(regime['end']))
        intensity.loc[mask] = regime['genuine_sovereignty']
    return intensity.to_frame()


SOVEREIGNTY_ARGUMENT = (
    'PART A: TO WHAT EXTENT DID UKRAINE EXERCISE GENUINE MONETARY SOVEREIGNTY?\n'
    '======================================================================\n\n'
    'ANSWER IN BRIEF\n'
    '---------------\n'
    'Ukraine exercised genuine monetary sovereignty during three distinct episodes '
    'totalling approximately 11.75 of the 25 years under review (2000–2025): the two '
    'crisis-driven devaluation episodes (Oct 2008–Feb 2009 and Feb 2014–Feb 2015), '
    'and the inflation-targeting period (Mar 2015–Dec 2021). During these windows, '
    'Ukraine either used the exchange rate as an asymmetric shock absorber or operated '
    'a fully discretionary monetary policy framework with central bank independence. '
    'In the remaining ~53% of the sample period, Ukraine lacked effective monetary '
    'sovereignty — the exchange rate regime (de facto dollar peg or wartime peg) '
    'constrained interest-rate policy through the Mundell-Fleming impossible trinity. '
    'The overall weighted-average treatment intensity is ω̄ = 0.325, indicating that '
    'over the full sample, Ukraine exercised roughly one-third of the monetary '
    'independence that a fully sovereign central bank could deploy.\n\n'
    'THEORETICAL FRAMEWORK\n'
    '---------------------\n'
    'The analysis follows the impossible trinity (Mundell, 1961, 1963): a country '
    'cannot simultaneously maintain a fixed exchange rate, free capital mobility, and '
    'independent monetary policy. When Ukraine operated a de facto or de jure dollar peg '
    '(2000–2008, 2009–2014, early 2022), the exchange rate anchor eliminated monetary '
    'independence — the central bank was compelled to set interest rates consistent with '
    'the peg rather than with domestic objectives. Conversely, during floating or managed-'
    'float periods, the NBU could pursue autonomous monetary policy, at the cost of '
    'exchange-rate volatility.\n\n'
    'The treatment intensity ω(t) ∈ [0, 1] operationalises this concept for the Part B '
    'counterfactual. A score of 0 means the regime is equivalent to EA membership in terms '
    'of monetary constraint (peg periods); a score of 1 means full independent monetary '
    'policy was exercised (devaluation periods). The IT period receives 0.8 because: '
    '(a) the NBU had full instrument independence under the 2015 NBU Law, (b) inflation '
    'targeting provided a nominal anchor distinct from the exchange rate, but (c) the '
    'framework itself imported ECB-style discipline, so the marginal cost of switching '
    'to EA membership was somewhat reduced (credibility convergence).\n\n'
    'EMPIRICAL CHRONOLOGY\n'
    '--------------------\n'
    'Regime 1 — Dollar peg I (Jan 2000–Apr 2005, 64 months, ω = 0.0):\n'
    'After the 1998 Russian crisis, the NBU stabilised the hryvnia at ~5.3–5.4 UAH/USD '
    'via heavy FX intervention. The IMF AREAER (2000–2004) classified Ukraine as a '
    'conventional peg. Average inflation was 7.7% (vs 2.6% EA), with a differential '
    'of +5.1pp driven by incomplete credibility rather than sovereign policy divergence.\n\n'
    'Regime 2 — Dollar peg II (May 2005–Sep 2008, 41 months, ω = 0.0):\n'
    'The NBU revalued to 5.05 UAH/USD in April 2005 and maintained the peg through '
    'a credit boom. The IMF AREAER (2005–2007) confirmed the conventional peg status. '
    'Inflation accelerated to 14.8% average (+12.2pp differential), driven by rapid '
    'domestic credit growth that the NBU was unable to counter — the peg prevented '
    'independent interest-rate tightening.\n\n'
    'Regime 3 — GFC devaluation (Oct 2008–Feb 2009, 5 months, ω = 0.5):\n'
    'The GFC triggered a 38% depreciation (5.05 → 7.7 UAH/USD). Steel exports collapsed, '
    'and capital fled. The IMF SBA ($16.4bn) and AREAER (2008) classified the regime as '
    '"other managed arrangement." This was crisis management rather than discretionary '
    'policy, hence ω = 0.5: the exchange rate absorbed the shock, but the choice was forced '
    'rather than strategic. Inflation averaged 22.2% (+20.2pp diff).\n\n'
    'Regime 4 — De facto peg restoration (Mar 2009–Jan 2014, 59 months, ω = 0.0):\n'
    'The hryvnia was re-pegged at ~7.7–8.0, later sliding to ~8.0. The IMF AREAER '
    '(2009–2013) classified this as a "stabilised arrangement." Calvo & Reinhart (2002) '
    'diagnose this behaviour as "fear of floating": countries that claim to float often '
    'intervene heavily to stabilise the exchange rate. Ukraine fit this pattern, '
    'sacrificing monetary independence for exchange-rate stability. Inflation averaged '
    '6.1% (+4.5pp diff).\n\n'
    'Regime 5 — Crimea- Donbas shock (Feb 2014–Feb 2015, 13 months, ω = 1.0):\n'
    'The Euromaidan revolution, Crimea annexation, and Donbas conflict triggered a 76% '
    'depreciation (8.0 → ~33 UAH/USD). This is the clearest case of genuine monetary '
    'sovereignty: the exchange rate served as the primary macroeconomic shock absorber. '
    'The IMF AREAER (2014) transitioned classification from "other managed" to "floating." '
    'Without the devaluation, Ukraine would have required a Greek-style internal '
    'devaluation — politically infeasible and economically catastrophic. Inflation peaked '
    'at 60.9% (Apr 2015), but the average of 16.0% masks enormous intra-period variation. '
    'The inflation differential was +15.8pp.\n\n'
    'Regime 6 — Inflation targeting (Mar 2015–Dec 2021, 82 months, ω = 0.8):\n'
    'The NBU adopted formal inflation targeting (target: 5% ± 1pp), backed by the 2015 '
    'NBU Law that granted full instrument independence. The IMF AREAER (2016–2021) '
    'classified the regime as "floating." The NBU successfully reduced inflation from 43% '
    'to 2.7% (2020), demonstrating credible disinflation. Average inflation was 15.2% '
    '(+14.1pp diff), but this is driven by the early disinflation period; from 2019–2021, '
    'inflation averaged 6.9%. ω = 0.8 rather than 1.0 because the IT framework itself '
    'imported ECB-style credibility: the gap between NBU IT and ECB membership narrowed '
    'via the Frankel-Rose (1998) endogeneity mechanism. The negative CF gap of −1.7pp in '
    'Part B confirms this convergence.\n\n'
    'Regime 7 — Wartime peg (Feb–Jul 2022, 6 months, ω = 0.0):\n'
    'The full-scale Russian invasion forced the NBU to fix the hryvnia at 29.25 UAH/USD '
    'and impose severe capital controls. The IMF AREAER (2022) classified this as a '
    '"stabilised arrangement." Monetary sovereignty was suspended. Inflation averaged '
    '17.1% (+9.0pp diff).\n\n'
    'Regime 8 — Managed float (Aug 2022–Dec 2025, 41 months, ω = 0.4):\n'
    'A stepped devaluation to 36.57 (≈25%) and gradual crawl partially restored exchange-'
    'rate flexibility. The IMF AREAER (2023–2024) classified the regime as "other managed '
    'arrangement." The IMF EFF ($15.6bn, Mar 2023) provided an external anchor. ω = 0.4 '
    'reflects partial sovereignty: monetary policy had some room for domestic objectives '
    'but remained constrained by exchange-rate management and IMF conditionality. '
    'Inflation averaged 12.7% (+8.6pp diff).\n\n'
    'TREATMENT INTENSITY SUMMARY\n'
    '---------------------------\n'
    '  ω = 0.0 (no sovereignty): 159 months with UA data (53.0%) — dollar pegs, wartime peg\n'
    '  ω = 0.4 (partial):          41 months (13.7%) — managed float with IMF EFF\n'
    '  ω = 0.5 (crisis):            5 months  (1.7%) — GFC forced devaluation\n'
    '  ω = 0.8 (discretionary):    82 months (27.3%) — inflation targeting\n'
    '  ω = 1.0 (full sovereignty): 13 months  (4.3%) — Crimea shock absorber\n\n'
    'Weighted-average treatment intensity (across 300 months with inflation data):\n'
    '  ω̄ = (159×0.0 + 41×0.4 + 5×0.5 + 82×0.8 + 13×1.0) / 300 = 0.325\n\n'
    'IMPLICATION FOR PART B\n'
    '----------------------\n'
    'The time-varying ω(t) enters the SVAR counterfactual multiplicatively:\n'
    '  π_CF(t) = π_actual(t) − ω(t) × d_contrib_UA(t)\n'
    'where d_contrib_UA(t) is Ukraine\'s demand-shock contribution to inflation.\n'
    'This ensures that the counterfactual "treatment" of EA membership is strongest '
    'when Ukraine exercised genuine sovereignty (ω → 1) and weakest when Ukraine was '
    'effectively already a de facto member of a currency union (ω → 0). The empirical '
    'result — CF ≠ EA mean by 9.1pp on average, with the largest gap during the Crimea '
    'devaluation (+11.5pp) — directly validates the Part A regime classification.\n\n'
    'REFERENCES\n'
    '----------\n'
    'Barro, R.J. & Gordon, D.B. (1983). "Rules, discretion and reputation in a model '
    'of monetary policy." Journal of Monetary Economics, 12(1): 101–121.\n'
    'Calvo, G.A. & Reinhart, C.M. (2002). "Fear of floating." Quarterly Journal of '
    'Economics, 117(2): 379–408.\n'
    'Frankel, J.A. & Rose, A.K. (1998). "The endogeneity of the optimum currency area '
    'criteria." The Economic Journal, 108(449): 1009–1025.\n'
    'Giavazzi, F. & Pagano, M. (1988). "The advantage of tying one\'s hands." European '
    'Economic Review, 32(5): 1055–1075.\n'
    'IMF. Annual Report on Exchange Arrangements and Exchange Restrictions (AREAER), '
    '2000–2024 editions. Washington, DC: International Monetary Fund.\n'
    'Mundell, R.A. (1961). "A theory of optimum currency areas." American Economic '
    'Review, 51(4): 657–665.\n'
    'Mundell, R.A. (1963). "Capital mobility and stabilization policy under fixed and '
    'flexible exchange rates." Canadian Journal of Economics, 29(4): 475–485.\n'
    'National Bank of Ukraine. Annual Reports (2000–2024). Kyiv: NBU.\n'
    'Åslund, A. (2015). Ukraine: What Went Wrong and How to Fix It. Peterson Institute.\n'
    'Gorodnichenko, Y. (2014). "Ukraine\'s exchange rate policy." VoxEU, 10 September 2014.\n'
    'IMF. Ukraine: Article IV Consultations (2000–2024). Washington, DC: IMF.\n'
)


def run_part_a():
    print('[part_a] Building regime chronology table...')
    table = build_regime_table()
    enriched = compute_regime_statistics(table)

    print('\n' + '=' * 130)
    print('  PART A — MONETARY REGIME CHRONOLOGY AND SOVEREIGNTY ASSESSMENT')
    print('=' * 130)
    print()
    print(f'  {"Period":30s} {"Mths":>4s} {"De Facto Regime":26s} {"ω":>4s} {"UA CPI":>7s} {"EA CPI":>7s} {"Diff":>7s} {"Peak":>7s}')
    print(f'  {"-"*30} {"-"*4} {"-"*26} {"-"*4} {"-"*7} {"-"*7} {"-"*7} {"-"*7}')
    for _, r in enriched.iterrows():
        mths = r['months_with_data']
        ua = f'{r["avg_UA_inflation"]:.1f}%' if not np.isnan(r['avg_UA_inflation']) else 'n/a'
        ea = f'{r["avg_EA_inflation"]:.1f}%' if not np.isnan(r['avg_EA_inflation']) else 'n/a'
        diff = f'{r["inflation_differential"]:+.1f}' if not np.isnan(r['inflation_differential']) else 'n/a'
        peak = f'{r["max_UA_inflation"]:.1f}%' if not np.isnan(r['max_UA_inflation']) else 'n/a'
        print(f'  {r["period"]:30s} {mths:4.0f} {r["de_facto_regime"]:26s} {r["genuine_sovereignty"]:4.1f} {ua:>7s} {ea:>7s} {diff:>7s} {peak:>7s}')
    print()
    total_mths = enriched['months_with_data'].sum()
    sov_mask = enriched['genuine_sovereignty'] > 0
    sov_mths = enriched.loc[sov_mask, 'months_with_data'].sum()
    w_avg = np.average(enriched['genuine_sovereignty'], weights=enriched['months_with_data'])
    print(f'  Weighted-average treatment intensity (omega_bar): {w_avg:.3f} (across {int(total_mths)} months with data)')
    print(f'  Total sovereign months (omega > 0): {int(sov_mths)}')
    print(f'  Share of sample with genuine sovereignty: {sov_mths/total_mths*100:.1f}%')
    print()

    csv_path = os.path.join(OUTPUT_DIR, 'part_a_regime_table.csv')
    summary_cols = ['period', 'start', 'end', 'months_with_data', 'de_facto_regime',
                    'imf_classification', 'uah_usd', 'genuine_sovereignty',
                    'avg_UA_inflation', 'avg_EA_inflation', 'inflation_differential',
                    'max_UA_inflation', 'capital_controls', 'sovereignty_rationale']
    enriched[summary_cols].to_csv(csv_path, index=False, float_format='%.1f')
    print(f'[part_a] Regime table saved to {csv_path}')

    txt_path = os.path.join(DOCS_DIR, 'part_a_argument.txt')
    with open(txt_path, 'w') as f:
        f.write(SOVEREIGNTY_ARGUMENT + '\n')
    print(f'[part_a] Argument saved to {txt_path}')

    print('[part_a] Building treatment intensity series...')
    intensity = build_treatment_intensity()
    intensity_path = os.path.join(OUTPUT_DIR, 'treatment_intensity.csv')
    intensity.to_csv(intensity_path)
    print(f'[part_a] Treatment intensity saved to {intensity_path}')
    vals = sorted(intensity['treatment_intensity'].unique())
    for v in vals:
        n = (intensity['treatment_intensity'] == v).sum()
        print(f'  ω = {v:.1f}: {int(n)} months ({n/len(intensity)*100:.1f}%)')

    return enriched, intensity


if __name__ == '__main__':
    run_part_a()
