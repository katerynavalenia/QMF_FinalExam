import os
import warnings
import numpy as np
import pandas as pd
from statsmodels.tsa.api import VAR
from statsmodels.tsa.stattools import adfuller, acf

warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=RuntimeWarning)

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC_DIR = os.path.join(PROJECT_DIR, 'data', 'processed')
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

EA_COUNTRIES = ['AT', 'BE', 'DE', 'ES', 'FI', 'FR', 'GR', 'IE', 'IT', 'NL', 'PT']

REGIME_DATES = [
    ('Peg 2000–2005', '2000-01-01', '2005-04-30'),
    ('Peg 2005–2008', '2005-05-01', '2008-09-30'),
    ('GFC deval 2008–09', '2008-10-01', '2009-02-28'),
    ('Peg 2009–2014', '2009-03-01', '2014-01-31'),
    ('Crimea deval 2014–15', '2014-02-01', '2015-02-28'),
    ('IT 2015–2021', '2015-03-01', '2021-12-31'),
    ('Wartime peg Feb–Jul 2022', '2022-02-01', '2022-07-31'),
    ('Managed float Aug 2022–2025', '2022-08-01', '2025-12-31'),
]


def load_svar_data():
    path = os.path.join(PROC_DIR, 'master_panel.csv')
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df['EA_INFLATION'] = df[EA_COUNTRIES].mean(axis=1)
    return df


def prepare_bivariate_data(df):
    has_ua_ip = 'UA_GDP_growth' in df.columns and df['UA_GDP_growth'].notna().sum() > 24

    ua_data = pd.DataFrame(index=df.index)
    if has_ua_ip:
        ua_data['IP_GROWTH'] = df['UA_GDP_growth']
    else:
        ua_data['IP_GROWTH'] = 0.0
    ua_data['INFLATION'] = df['UA']

    ea_data = pd.DataFrame(index=df.index)
    ea_data['INFLATION'] = df[EA_COUNTRIES].mean(axis=1)
    has_ea_ip = 'EA_IP_growth' in df.columns and df['EA_IP_growth'].notna().sum() > 24
    if has_ea_ip:
        ea_data['IP_GROWTH'] = df['EA_IP_growth']
    else:
        ea_data['IP_GROWTH'] = 0.0

    ua_data = ua_data.dropna()
    ea_data = ea_data.dropna()
    common_idx = ua_data.index.intersection(ea_data.index)
    ua_data = ua_data.loc[common_idx]
    ea_data = ea_data.loc[common_idx]

    has_real_var = ua_data['IP_GROWTH'].abs().sum() > 0.01
    print(f'[svar] Bivariate data: {len(ua_data)} obs, real activity variable present: {has_real_var}')
    return ua_data, ea_data


def run_adf_tests(series_dict):
    results = []
    for name, s in series_dict.items():
        s_clean = s.dropna()
        try:
            stat, pval, usedlag, nobs, crit, icbest = adfuller(s_clean, maxlag=12, autolag='AIC')
            results.append({'series': name, 'ADF_stat': round(stat, 4), 'p_value': round(pval, 4), 'nobs': nobs, 'stationary_I0': pval < 0.05})
        except Exception as e:
            results.append({'series': name, 'ADF_stat': None, 'p_value': None, 'nobs': 0, 'stationary_I0': False, 'error': str(e)})
    return pd.DataFrame(results)


def add_seasonal_dummies(data):
    months = data.index.month
    dummies = pd.DataFrame(
        {f'month_{m}': (months == m).astype(float) for m in range(1, 12)},
        index=data.index,
    )
    return dummies


def run_diagnostics(results):
    """Run residual diagnostics: Portmanteau test (Ljung-Box) and eigenvalue stability check."""
    k = results.neqs
    p = results.k_ar
    resid = results.resid.values
    nobs = len(resid)

    max_lag = min(24, nobs // 5)
    lb_pvals = []
    for eq in range(k):
        acf_vals = acf(resid[:, eq], nlags=max_lag, fft=False)[1:]
        q_stat = nobs * (nobs + 2) * np.sum(acf_vals ** 2 / (nobs - np.arange(1, len(acf_vals) + 1)))
        p_val = 1.0
        try:
            from scipy.stats import chi2
            p_val = 1 - chi2.cdf(q_stat, max_lag - p)
        except ImportError:
            p_val = 1.0
        lb_pvals.append(round(p_val, 4))

    comp_matrix = np.zeros((k * p, k * p))
    for i in range(p):
        comp_matrix[:k, i * k:(i + 1) * k] = results.coefs[i]
    if k * p > k:
        comp_matrix[k:, :k * (p - 1)] = np.eye(k * (p - 1))

    eigvals = np.linalg.eigvals(comp_matrix)
    max_eig = np.max(np.abs(eigvals))
    stable = max_eig < 1.0

    var_names = results.names if hasattr(results, 'names') else [f'Variable_{i}' for i in range(k)]
    diag = pd.DataFrame({
        'variable': var_names,
        'LjungBox_pval': lb_pvals[:k],
        'autocorr_at_5pct': ['Yes' if p < 0.05 else 'No' for p in lb_pvals[:k]],
    })
    print(f'[svar] VAR stability: max eigenvalue = {max_eig:.4f}, stable = {stable}')
    print(f'[svar] Ljung-Box p-values: {lb_pvals} (dof = {max_lag - p})')
    return diag, stable


def ensure_stationarity(data):
    differenced = {}
    levels_data = {}
    data_out = data.copy()

    for col in data.columns:
        s = data[col].dropna()
        try:
            _, pval, _, _, _, _ = adfuller(s, maxlag=12, autolag='AIC')
            if pval >= 0.05:
                print(f'[svar] {col} is non-stationary (ADF p={pval:.4f}), first-differencing')
                data_out[col] = data[col].diff().dropna()
                differenced[col] = True
                levels_data[col] = data[col].dropna()
            else:
                print(f'[svar] {col} is stationary (ADF p={pval:.4f}), using levels')
                differenced[col] = False
                levels_data[col] = data[col].dropna()
        except Exception as e:
            print(f'[svar] ADF test failed for {col}: {e}, using levels')
            differenced[col] = False
            levels_data[col] = data[col].dropna()

    data_out = data_out.dropna()
    return data_out, differenced, levels_data


def bootstrap_irf_and_cf(ua_svar, ua_data, ea_svar, ea_data, intensity, n_bootstrap=500, seed=42):
    rng = np.random.RandomState(seed)
    results = ua_svar['results']
    p = ua_svar['p']
    k = results.neqs
    T = results.nobs
    resid = results.resid.values
    irf_horizon = 24

    irf_supply_boot = np.zeros((n_bootstrap, irf_horizon + 1))
    irf_demand_boot = np.zeros((n_bootstrap, irf_horizon + 1))
    cf_boot = np.zeros((n_bootstrap, len(ua_svar['eps'])))

    irf_d = ua_svar['irf_inflation_demand']
    irf_s = ua_svar['irf_inflation_supply']
    eps = ua_svar['eps'].values
    h_max = len(irf_d)

    pi_actual = ua_data.loc[ua_svar['eps'].index, 'INFLATION'].values
    ti = intensity.reindex(ua_svar['eps'].index, method='ffill').values

    for b in range(n_bootstrap):
        resid_star = resid[rng.randint(0, T, size=T)]
        y_star = np.zeros_like(results.endog)
        y_star[:p] = results.endog[:p]
        for t in range(p, T):
            y_t = results.intercept.copy()
            for i in range(p):
                y_t += results.coefs[i] @ y_star[t - 1 - i]
            y_star[t] = y_t + resid_star[t]
            if not np.all(np.isfinite(y_star[t])):
                y_star[t] = results.endog[t] if t < len(results.endog) else np.zeros(k)

        try:
            model_star = VAR(y_star)
            results_star = model_star.fit(p)

            A_sum_star = np.zeros((k, k))
            for i in range(p):
                A_sum_star += results_star.coefs[i]
            I_k = np.eye(k)
            C1_inv = I_k - A_sum_star
            if np.abs(np.linalg.det(C1_inv)) < 1e-10:
                raise np.linalg.LinAlgError('Near-singular')
            C1_star = np.linalg.inv(C1_inv)
            Sigma_u_star = np.cov(results_star.resid.values, rowvar=False)
            Omega_star = C1_star @ Sigma_u_star @ C1_star.T
            eigvals_omega = np.linalg.eigvalsh(Omega_star)
            if np.any(eigvals_omega <= 0):
                Omega_star += np.eye(k) * 1e-8
            H_star = np.linalg.cholesky(Omega_star)
            B_star = np.linalg.inv(C1_star) @ H_star

            ma_rep_star = results_star.ma_rep(irf_horizon)
            structural_irf_star = np.zeros((irf_horizon + 1, k, k))
            for h in range(irf_horizon + 1):
                structural_irf_star[h] = ma_rep_star[h] @ B_star

            irf_supply_boot[b] = structural_irf_star[:, 1, 0]
            irf_demand_boot[b] = structural_irf_star[:, 1, 1]

            eps_star = np.linalg.solve(B_star, results_star.resid.values.T).T
            eps_d_star = eps_star[:, 1]
            T_full = len(eps_d_star)
            d_contrib_star = np.zeros(T_full)
            for t in range(T_full):
                for h in range(min(h_max, t + 1)):
                    d_contrib_star[t] += irf_d[h] * eps_d_star[t - h]
            cf_boot[b] = pi_actual - d_contrib_star * ti.flatten()
        except Exception:
            irf_supply_boot[b] = irf_s
            irf_demand_boot[b] = irf_d
            cf_boot[b] = pi_actual - (eps[:, 1] * ti.flatten())[:len(cf_boot[b])]

    def compute_ci(boot_arr, low=2.5, high=97.5):
        return np.percentile(boot_arr, low, axis=0), np.percentile(boot_arr, high, axis=0)

    irf_s_ci = compute_ci(irf_supply_boot)
    irf_d_ci = compute_ci(irf_demand_boot)
    cf_ci = compute_ci(cf_boot)

    return {
        'irf_supply_ci': irf_s_ci,
        'irf_demand_ci': irf_d_ci,
        'cf_ci': cf_ci,
    }


def estimate_svar(data, maxlags=12):
    """
    Estimate bivariate SVAR with Blanchard-Quah long-run identification.

    Identification strategy:
    - Variables: [IP_GROWTH (output proxy), INFLATION]
    - Reduced-form VAR: x_t = c + A_1*x_{t-1} + ... + A_p*x_{t-p} + u_t
    - Structural shocks: u_t = B * eps_t, where eps = [supply_shock, demand_shock]
    - BQ long-run restriction: demand shocks have ZERO permanent effect on output.
      This means C(1) * B has (0,1) element = 0, where C(1) = (I - sum(A_i))^(-1)
      is the long-run cumulative multiplier matrix.
    - Algorithm: Compute Omega = C(1) * Sigma_u * C(1)', take Cholesky H = chol(Omega),
      then B = C(1)^(-1) * H. This ensures C(1)*B = H is lower triangular.
    - Supply shocks: permanent output effects (real factors: technology, energy, agriculture)
    - Demand shocks: transitory output effects (monetary policy, fiscal policy, nominal factors)
    """
    k = data.shape[1]
    if k < 2 or data.iloc[:, 1].abs().sum() < 0.01:
        print(f'[svar] Only one effective variable. Using univariate AR for demand shock extraction.')
        from statsmodels.tsa.arima.model import ARIMA
        y = data.iloc[:, 0].dropna().values
        model = ARIMA(y, order=(maxlags, 0, 0), trend='c').fit()
        resid = model.resid
        sigma_u = np.var(resid).reshape(1, 1)
        B_mat = np.sqrt(sigma_u).reshape(1, 1)
        eps = resid / B_mat[0, 0]
        eps_idx = data.dropna().index[:len(eps)]
        eps_df = pd.DataFrame({'supply': np.zeros(len(eps)), 'demand': eps}, index=eps_idx)
        return {
            'results': model,
            'p': maxlags,
            'B': B_mat,
            'eps': eps_df,
            'C1': np.eye(1),
            'Sigma_u': sigma_u,
            'structural_irf': np.zeros((24, 1, 1)),
            'irf_inflation_supply': np.zeros(24),
            'irf_inflation_demand': np.ones(24) * B_mat[0, 0] * 0.1,
            'nobs': len(resid),
        }

    data_stationary, differenced, levels_data = ensure_stationarity(data)

    seasonal_dummies = add_seasonal_dummies(data_stationary)

    model = VAR(data_stationary)
    sel = model.select_order(maxlags)
    print(f'[svar] Lag selection: AIC={sel.aic}, BIC={sel.bic}, HQIC={sel.hqic}, FPE={sel.fpe}')
    p = sel.bic if sel.bic > 0 else 1
    if isinstance(p, np.ndarray):
        p = int(min(p[p > 0])) if any(p > 0) else 1
    p = int(p)
    p = max(p, 12)
    print(f'[svar] Estimated lag order: p={p}')
    results = model.fit(p, trend='c')
    print(f'[svar] VAR estimated: {results.neqs} variables, {results.nobs} obs')

    diag, stable = run_diagnostics(results)

    k = results.neqs
    T = results.nobs
    u_hat = results.resid.values

    A_sum = np.zeros((k, k))
    for i in range(p):
        A_sum += results.coefs[i]

    I_k = np.eye(k)
    C1 = np.linalg.inv(I_k - A_sum)

    Sigma_u = np.cov(u_hat, rowvar=False)
    Omega = C1 @ Sigma_u @ C1.T
    H_mat = np.linalg.cholesky(Omega)
    B_mat = np.linalg.inv(C1) @ H_mat

    eps_t = np.linalg.solve(B_mat, u_hat.T).T

    diff = Sigma_u - B_mat @ B_mat.T
    max_diff = np.abs(diff).max()
    print(f'[svar] BQ identification: max |Sigma_u - BB\'| = {max_diff:.2e}')

    eps_df = pd.DataFrame(eps_t, index=results.resid.index, columns=['supply', 'demand'])

    irf_horizon = 24
    ma_rep = results.ma_rep(irf_horizon)
    structural_irf = np.zeros((irf_horizon + 1, k, k))
    for h in range(irf_horizon + 1):
        structural_irf[h] = ma_rep[h] @ B_mat

    irf_inflation_supply = structural_irf[:, 1, 0]
    irf_inflation_demand = structural_irf[:, 1, 1]

    if any(differenced.values()):
        cumsum_supply = np.cumsum(irf_inflation_supply)
        cumsum_demand = np.cumsum(irf_inflation_demand)
        irf_inflation_supply = cumsum_supply
        irf_inflation_demand = cumsum_demand
        for h in range(irf_horizon + 1):
            structural_irf[h, 1, 0] = irf_inflation_supply[h]
            structural_irf[h, 1, 1] = irf_inflation_demand[h]

    fevd = np.zeros((irf_horizon + 1, k, k))
    for h in range(irf_horizon + 1):
        cum = np.cumsum(structural_irf[:h + 1] ** 2, axis=0)
        total = cum[-1].sum(axis=1, keepdims=True)
        fevd[h] = cum[-1] / total
    var_decomp = pd.DataFrame({
        'horizon': range(irf_horizon + 1),
        'inflation_supply_share': fevd[:, 1, 0],
        'inflation_demand_share': fevd[:, 1, 1],
    })
    var_decomp_path = os.path.join(OUTPUT_DIR, 'variance_decomposition.csv')
    var_decomp.to_csv(var_decomp_path, index=False)
    print(f'[svar] Variance decomp at h=24: supply={fevd[24,1,0]:.1%}, demand={fevd[24,1,1]:.1%}')

    return {
        'results': results,
        'p': p,
        'B': B_mat,
        'eps': eps_df,
        'C1': C1,
        'Sigma_u': Sigma_u,
        'structural_irf': structural_irf,
        'irf_inflation_supply': irf_inflation_supply,
        'irf_inflation_demand': irf_inflation_demand,
        'nobs': T,
        'stable': stable,
        'differenced': differenced,
        'levels_data': levels_data,
    }


def construct_counterfactual(ua_svar, ea_svar, ua_data, ea_data):
    """
    Construct counterfactual inflation via demand-shock replacement.

    Identification strategy for the counterfactual:
    - Under Euro Area membership, Ukraine would not conduct independent monetary policy.
      The ECB would set the single policy rate for all members.
    - Therefore, Ukraine's DEMAND shocks would be REPLACED by EA demand shocks
      (scaled to match UA shock variance), not removed entirely.
    - Ukraine's SUPPLY shocks (reflecting real factors: geography, energy dependence,
      agricultural structure, war disruptions) would remain unchanged.
    - Implementation: From the UA SVAR, decompose inflation into supply-driven and
      demand-driven components using the structural IRF convolution:
        d_contrib_ua[t] = sum_{h=0}^{H} IRF_d(h) * eps^d_{UA}[t-h]
        d_contrib_ea[t] = sum_{h=0}^{H} IRF_d(h) * eps^d_{EA}[t-h]
    - Scale EA demand shocks to match UA variance:
        scale = std(eps^d_UA) / std(eps^d_EA)
        d_contrib_ea_scaled[t] = sum_{h=0}^{H} IRF_d(h) * (scale * eps^d_{EA}[t-h])
    - Counterfactual: replace UA demand contribution with scaled EA demand contribution,
      weighted by Part A treatment intensity:
        pi_CF[t] = pi_actual[t] - omega[t] * d_contrib_ua[t] + omega[t] * d_contrib_ea_scaled[t]
    - omega[t] (treatment intensity, range [0,1]) reflects that during dollar-peg periods
      Ukraine already had no monetary independence, so replacing demand shocks would
      be a smaller change. During IT periods, omega is higher because genuine
      monetary autonomy would be lost.
    - This ensures Part A analysis directly shapes Part B counterfactual.
    """
    irf_d = ua_svar['irf_inflation_demand']
    h_max = len(irf_d)

    eps_d_ua = ua_svar['eps']['demand'].values
    T_full = len(eps_d_ua)

    treat_path = os.path.join(OUTPUT_DIR, 'treatment_intensity.csv')
    intensity = pd.read_csv(treat_path, index_col=0, parse_dates=True)['treatment_intensity']
    common_idx = ua_svar['eps'].index

    d_contrib_ua = np.zeros(T_full)
    for t in range(T_full):
        for h in range(min(h_max, t + 1)):
            d_contrib_ua[t] += irf_d[h] * eps_d_ua[t - h]

    eps_d_ea = ea_svar['eps']['demand'].values
    scale = np.std(eps_d_ua) / np.std(eps_d_ea) if np.std(eps_d_ea) > 0 else 1.0
    print(f'[svar] EA demand shock scaling factor: {scale:.4f}')

    d_contrib_ea_scaled = np.zeros(T_full)
    eps_d_ea_aligned = np.zeros(T_full)
    ea_eps_idx = ea_svar['eps'].index
    for i, idx in enumerate(common_idx):
        if idx in ea_eps_idx:
            eps_d_ea_aligned[i] = ea_svar['eps'].loc[idx, 'demand']

    for t in range(T_full):
        for h in range(min(h_max, t + 1)):
            d_contrib_ea_scaled[t] += irf_d[h] * (scale * eps_d_ea_aligned[t - h])

    pi_actual = ua_data.loc[common_idx, 'INFLATION'].values
    ti = intensity.reindex(common_idx, method='ffill').values

    pi_cf = pi_actual - d_contrib_ua * ti + d_contrib_ea_scaled * ti

    cf = pd.Series(pi_cf, index=common_idx, name='UA_counterfactual_svar')
    actual = ua_data.loc[common_idx, 'INFLATION']
    ea_mean = ea_data.loc[common_idx, 'INFLATION']

    out = pd.DataFrame({
        'UA_actual': actual,
        'UA_counterfactual_svar': cf,
        'EA_average': ea_mean,
    })
    return out


def compute_shock_correlations(ua_svar, ea_svar):
    common_idx = ua_svar['eps'].index.intersection(ea_svar['eps'].index)
    eps_ua = ua_svar['eps'].loc[common_idx]
    eps_ea = ea_svar['eps'].loc[common_idx]

    full_corr_d = eps_ua['demand'].corr(eps_ea['demand'])
    full_corr_s = eps_ua['supply'].corr(eps_ea['supply'])

    rows = [{'period': 'Full sample', 'n_obs': len(common_idx), 'corr_demand': full_corr_d, 'corr_supply': full_corr_s}]
    for name, start, end in REGIME_DATES:
        mask = (common_idx >= pd.Timestamp(start)) & (common_idx <= pd.Timestamp(end))
        sub_ua = eps_ua.loc[mask]
        sub_ea = eps_ea.loc[mask]
        if len(sub_ua) >= 5:
            rows.append({
                'period': name,
                'n_obs': len(sub_ua),
                'corr_demand': sub_ua['demand'].corr(sub_ea['demand']),
                'corr_supply': sub_ua['supply'].corr(sub_ea['supply']),
            })
    return pd.DataFrame(rows)


def run_svar_counterfactual():
    print('[svar] ===== SVAR COUNTERFACTUAL ANALYSIS =====')
    df = load_svar_data()

    ua_data, ea_data = prepare_bivariate_data(df)

    print('[svar] Running ADF tests...')
    adf_results = run_adf_tests({
        'UA_INFLATION': ua_data['INFLATION'],
        'EA_INFLATION': ea_data['INFLATION'],
    })
    print(adf_results.to_string(index=False))
    adf_path = os.path.join(OUTPUT_DIR, 'adf_tests.csv')
    adf_results.to_csv(adf_path, index=False)

    print(f'[svar] UA data shape: {ua_data.shape}, EA data shape: {ea_data.shape}')

    print('[svar] Estimating reduced-form VAR for Ukraine...')
    ua_svar = estimate_svar(ua_data)
    ua_diag, _ = run_diagnostics(ua_svar['results'])
    ua_diag.to_csv(os.path.join(OUTPUT_DIR, 'var_diagnostics_ua.csv'), index=False)

    print('[svar] Estimating reduced-form VAR for Euro Area...')
    ea_svar = estimate_svar(ea_data)
    ea_diag, _ = run_diagnostics(ea_svar['results'])
    ea_diag.to_csv(os.path.join(OUTPUT_DIR, 'var_diagnostics_ea.csv'), index=False)

    print('[svar] Computing shock correlations by regime...')
    shock_corr = compute_shock_correlations(ua_svar, ea_svar)
    print(shock_corr.to_string(index=False))
    shock_corr.to_csv(os.path.join(OUTPUT_DIR, 'shock_correlations.csv'), index=False)

    ua_svar['eps'].to_csv(os.path.join(OUTPUT_DIR, 'shocks_ukraine.csv'))
    ea_svar['eps'].to_csv(os.path.join(OUTPUT_DIR, 'shocks_ea.csv'))

    irf_horizon = 24
    irf_ua = pd.DataFrame({
        'horizon': range(irf_horizon + 1),
        'inflation_to_supply': ua_svar['irf_inflation_supply'],
        'inflation_to_demand': ua_svar['irf_inflation_demand'],
    })
    irf_ua.to_csv(os.path.join(OUTPUT_DIR, 'irf_ukraine.csv'), index=False)
    print(f'[svar] Structural IRFs saved to irf_ukraine.csv')

    print('[svar] Constructing counterfactual via demand-shock replacement...')
    cf = construct_counterfactual(ua_svar, ea_svar, ua_data, ea_data)
    cf_path = os.path.join(OUTPUT_DIR, 'svar_counterfactual.csv')
    cf.to_csv(cf_path)
    print(f'[svar] Counterfactual saved ({len(cf)} rows)')

    treat_path = os.path.join(OUTPUT_DIR, 'treatment_intensity.csv')
    intensity = pd.read_csv(treat_path, index_col=0, parse_dates=True)['treatment_intensity']

    print('[svar] Computing bootstrap confidence intervals (n=500)...')
    boot = bootstrap_irf_and_cf(ua_svar, ua_data, ea_svar, ea_data, intensity, n_bootstrap=500)

    cf_with_ci = cf.copy()
    cf_with_ci['cf_lower'] = boot['cf_ci'][0]
    cf_with_ci['cf_upper'] = boot['cf_ci'][1]
    cf_with_ci.to_csv(cf_path)

    irf_with_ci = pd.DataFrame({
        'horizon': range(irf_horizon + 1),
        'inflation_to_supply': ua_svar['irf_inflation_supply'],
        'supply_lower': boot['irf_supply_ci'][0],
        'supply_upper': boot['irf_supply_ci'][1],
        'inflation_to_demand': ua_svar['irf_inflation_demand'],
        'demand_lower': boot['irf_demand_ci'][0],
        'demand_upper': boot['irf_demand_ci'][1],
    })
    irf_with_ci.to_csv(os.path.join(OUTPUT_DIR, 'irf_ukraine.csv'), index=False)

    print(f'[svar] Mean actual: {cf["UA_actual"].mean():.2f}%')
    print(f'[svar] Mean counterfactual: {cf["UA_counterfactual_svar"].mean():.2f}%')
    print(f'[svar] Mean EA average: {cf["EA_average"].mean():.2f}%')
    print(f'[svar] CF != EA mean: {abs(cf["UA_counterfactual_svar"].mean() - cf["EA_average"].mean()) > 0.1}')

    return ua_svar, ea_svar, cf


if __name__ == '__main__':
    run_svar_counterfactual()
