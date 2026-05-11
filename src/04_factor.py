import os
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC_DIR = os.path.join(PROJECT_DIR, 'data', 'processed')
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

EA_COUNTRIES = ['AT', 'BE', 'DE', 'ES', 'FI', 'FR', 'GR', 'IE', 'IT', 'NL', 'PT']

QUIET_START = '2000-01-01'
QUIET_END = '2008-09-30'


def extract_ea_common_factor(inflation_df):
    ea = inflation_df[EA_COUNTRIES].dropna()
    if len(ea) < 12:
        raise ValueError(f'Not enough EA data for PCA: {len(ea)} rows')

    ea_std = (ea - ea.mean()) / ea.std()
    pca = PCA(n_components=2)
    scores = pca.fit_transform(ea_std)

    explained = pca.explained_variance_ratio_
    print(f'[factor] PC1 explains {explained[0]*100:.1f}% of EA inflation variance')
    print(f'[factor] PC2 explains {explained[1]*100:.1f}% of EA inflation variance')

    loadings = pd.DataFrame(
        pca.components_.T,
        index=EA_COUNTRIES,
        columns=[f'F{i+1}' for i in range(2)]
    )

    factor_df = pd.DataFrame(
        {'F1': scores[:, 0], 'F2': scores[:, 1]},
        index=ea.index
    )

    return factor_df, loadings, explained


QUIET_PERIODS = {
    '2000-2008 (pre-GFC)': ('2000-01-01', '2008-09-30'),
    '2009-2014 (post-GFC peg)': ('2009-03-01', '2014-01-31'),
}


def estimate_ukraine_loading(inflation_df, factor_df, quiet_start=QUIET_PERIODS['2000-2008 (pre-GFC)'][0], quiet_end=QUIET_PERIODS['2000-2008 (pre-GFC)'][1]):
    quiet_mask = (inflation_df.index >= pd.Timestamp(quiet_start)) & \
                 (inflation_df.index <= pd.Timestamp(quiet_end))
    quiet_dates = inflation_df.index[quiet_mask]
    common_dates = quiet_dates.intersection(factor_df.index)
    valid_mask = inflation_df.loc[common_dates, 'UA'].notna().values
    common_dates = common_dates[valid_mask]

    X_quiet = factor_df.loc[common_dates, 'F1'].values.reshape(-1, 1)
    y_quiet = inflation_df.loc[common_dates, 'UA'].values

    model_quiet = LinearRegression()
    model_quiet.fit(X_quiet, y_quiet)
    lambda_quiet = model_quiet.coef_[0]
    alpha_quiet = model_quiet.intercept_
    r2_quiet = model_quiet.score(X_quiet, y_quiet)

    print(f'[factor] Ukraine loading (quiet period): λ = {lambda_quiet:.4f}, α = {alpha_quiet:.4f}, R² = {r2_quiet:.4f}')

    all_dates = inflation_df.index.intersection(factor_df.index)
    valid_all = inflation_df.loc[all_dates, 'UA'].notna().values
    all_dates = all_dates[valid_all]
    X_all = factor_df.loc[all_dates, 'F1'].values.reshape(-1, 1)
    y_all = inflation_df.loc[all_dates, 'UA'].values

    model_full = LinearRegression()
    model_full.fit(X_all, y_all)
    lambda_full = model_full.coef_[0]
    alpha_full = model_full.intercept_
    r2_full = model_full.score(X_all, y_all)

    print(f'[factor] Ukraine loading (full sample): λ = {lambda_full:.4f}, α = {alpha_full:.4f}, R² = {r2_full:.4f}')
    print(f'[factor] Using quiet-period loading for counterfactual (higher R² = {r2_quiet:.4f})')

    return lambda_quiet, alpha_quiet, model_quiet


def compare_quiet_periods(inflation_df, factor_df):
    """Estimate Ukraine loading across multiple quiet periods and compare R²."""
    results = []
    for label, (qs, qe) in QUIET_PERIODS.items():
        lam, alp, r2 = estimate_ukraine_loading(inflation_df, factor_df, qs, qe)
        results.append({'period': label, 'lambda': round(lam, 4), 'alpha': round(alp, 4), 'R2': round(r2, 4)})
    return pd.DataFrame(results)


def construct_factor_counterfactual(inflation_df, factor_df, lambda_ua, alpha_ua):
    common_idx = inflation_df.index.intersection(factor_df.index)
    F1 = factor_df.loc[common_idx, 'F1']
    cf = alpha_ua + lambda_ua * F1
    cf.name = 'UA_counterfactual_factor'
    return cf.to_frame()


def run_factor_counterfactual():
    print('[factor] ===== CICCARELLI-MOJON COMMON FACTOR MODEL =====')
    path = os.path.join(PROC_DIR, 'inflation_panel.csv')
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    print(f'[factor] Inflation panel shape: {df.shape}, range: {df.index[0]} to {df.index[-1]}')

    print('[factor] Extracting EA common inflation factor via PCA...')
    factor_df, loadings, explained = extract_ea_common_factor(df)
    factor_df.to_csv(os.path.join(OUTPUT_DIR, 'ea_common_factors.csv'))
    loadings.to_csv(os.path.join(OUTPUT_DIR, 'ea_factor_loadings.csv'))
    print(f'[factor] Loadings:\n{loadings}')

    print('[factor] Estimating Ukraine\'s loading on EA common factor (quiet period)...')
    lambda_ua, alpha_ua, model = estimate_ukraine_loading(df, factor_df)

    print('[factor] Constructing factor counterfactual...')
    cf = construct_factor_counterfactual(df, factor_df, lambda_ua, alpha_ua)

    common_idx = df.index.intersection(factor_df.index)
    result = pd.DataFrame(index=common_idx)
    result['UA_actual'] = df.loc[common_idx, 'UA']
    result['UA_counterfactual_factor'] = cf['UA_counterfactual_factor']
    result['EA_mean'] = df.loc[common_idx, EA_COUNTRIES].mean(axis=1)
    result['EA_factor_F1'] = factor_df.loc[common_idx, 'F1']

    result.to_csv(os.path.join(OUTPUT_DIR, 'factor_counterfactual.csv'))
    print(f'[factor] Factor counterfactual saved ({len(result)} rows)')
    print(f'[factor] Mean actual: {result["UA_actual"].mean():.2f}%')
    print(f'[factor] Mean counterfactual: {result["UA_counterfactual_factor"].mean():.2f}%')
    print(f'[factor] Mean EA: {result["EA_mean"].mean():.2f}%')

    return result, loadings, explained


if __name__ == '__main__':
    run_factor_counterfactual()
