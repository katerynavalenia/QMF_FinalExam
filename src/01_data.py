import os
import requests
import numpy as np
import pandas as pd
from io import StringIO

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJECT_DIR, 'data', 'raw')
PROC_DIR = os.path.join(PROJECT_DIR, 'data', 'processed')
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROC_DIR, exist_ok=True)

EA_COUNTRIES = ['AT', 'BE', 'DE', 'ES', 'FI', 'FR', 'GR', 'IE', 'IT', 'NL', 'PT']


def load_ecb_hicp_panel():
    csv_path = os.path.join(RAW_DIR, 'data_ecb_hicp_panel.csv')
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['TIME_PERIOD'])
    df = df.set_index('date')
    df.index = df.index.to_period('M').to_timestamp(how='start')
    print(f'[data] ECB HICP panel: {df.shape[0]} months, {df.shape[1] - 1} countries')
    return df


def load_ukraine_cpi_raw():
    csv_path = os.path.join(RAW_DIR, 'data_ukraine_cpi_raw.csv')
    df = pd.read_csv(csv_path)
    df['OBS_VALUE'] = df['OBS_VALUE'].astype(str).str.replace(',', '.').pipe(pd.to_numeric, errors='coerce')
    df = df.dropna(subset=['OBS_VALUE'])
    df['date'] = pd.to_datetime(df['TIME_PERIOD'].str.replace(r'^(\d{4})-M(\d{2})$', r'\1-\2-01', regex=True))
    df = df.sort_values('date').set_index('date')
    df.index = df.index.to_period('M').to_timestamp(how='start')
    df = df[~df.index.duplicated(keep='last')]
    return df[['OBS_VALUE']]


def cpi_mom_to_yoy(series):
    monthly_rates = series / 100.0
    yoy = monthly_rates.rolling(12).apply(lambda x: np.prod(x) - 1) * 100
    return yoy.rename('UA')


def fetch_with_fallback(url, cache_name, parse_fn=None):
    cache_path = os.path.join(RAW_DIR, cache_name)
    try:
        if parse_fn is None:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            df = pd.read_csv(StringIO(resp.text))
        else:
            df = parse_fn(url)
        if df is None or (hasattr(df, 'empty') and df.empty):
            raise ValueError(f'Empty result from API for {cache_name}')
        df.to_csv(cache_path, index=False)
        print(f'[data] Downloaded and cached {cache_name} ({len(df)} rows)')
        return df
    except Exception:
        if os.path.exists(cache_path):
            cached = pd.read_csv(cache_path)
            if len(cached) > 1:
                return cached
            os.remove(cache_path)
        return pd.DataFrame()


def fetch_ecb_exchange_rate():
    url = ('https://data-api.ecb.europa.eu/service/data/EXR/M.UAH.EUR.SP00.A'
           '?format=csvdata&startPeriod=2000-01&endPeriod=2025-12')
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text))
        df['date'] = pd.to_datetime(df['TIME_PERIOD'])
        df = df.dropna(subset=['OBS_VALUE']).set_index('date').sort_index()
        df.index = df.index.to_period('M').to_timestamp(how='start')
        df['EUR_UAH'] = pd.to_numeric(df['OBS_VALUE'], errors='coerce')
        return df[['EUR_UAH']]
    except Exception as e:
        return pd.DataFrame()


def fetch_ecb_policy_rate():
    url = ('https://data-api.ecb.europa.eu/service/data/FM/M.U2.EUR.4F.KR.MRR_FR.LEV'
           '?format=csvdata&startPeriod=2000-01&endPeriod=2025-12')
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text))
        df['date'] = pd.to_datetime(df['TIME_PERIOD'])
        df = df.dropna(subset=['OBS_VALUE']).set_index('date').sort_index()
        df.index = df.index.to_period('M').to_timestamp(how='start')
        df['ECB_MRR'] = pd.to_numeric(df['OBS_VALUE'], errors='coerce')
        return df[['ECB_MRR']]
    except Exception as e:
        return pd.DataFrame()


def fetch_wb_ukraine_gdp():
    url = 'https://api.worldbank.org/v2/country/UKR/indicator/NY.GDP.MKTP.KD.ZG?format=json&per_page=100'
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if len(data) < 2:
            raise ValueError('Unexpected World Bank API response')
        records = [(int(entry['date']), entry['value']) for entry in data[1] if entry['value'] is not None]
        df = pd.DataFrame(records, columns=['year', 'UA_GDP_growth']).set_index('year').sort_index()
        df.to_csv(os.path.join(RAW_DIR, 'ua_gdp_growth.csv'))
        print(f'[data] World Bank GDP downloaded ({len(df)} years)')
        return df
    except Exception as e:
        cache_path = os.path.join(RAW_DIR, 'ua_gdp_growth.csv')
        if os.path.exists(cache_path):
            print(f'[data] Loading cached GDP: {cache_path}')
            return pd.read_csv(cache_path, index_col=0)
        return pd.DataFrame()


def fetch_fred_series(series_id, name):
    url = f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd=1999-01-01&coed=2025-12-01'
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text))
        df['date'] = pd.to_datetime(df['observation_date'])
        df = df.dropna(subset=[series_id]).set_index('date').sort_index()
        df = df[~df.index.duplicated(keep='last')]
        df[name] = pd.to_numeric(df[series_id], errors='coerce')
        monthly_idx = pd.date_range('2000-01-01', '2025-12-01', freq='MS')
        df = df.reindex(df.index.union(monthly_idx))
        df = df.ffill().bfill().reindex(monthly_idx)
        df.index.name = 'date'
        cache_path = os.path.join(RAW_DIR, f'{name}.csv')
        df[[name]].to_csv(cache_path)
        print(f'[data] FRED {name} downloaded ({len(df)} monthly rows)')
        return df[[name]]
    except Exception as e:
        cache_path = os.path.join(RAW_DIR, f'{name}.csv')
        if os.path.exists(cache_path):
            print(f'[data] Loading cached FRED {name}')
            return pd.read_csv(cache_path, index_col=0, parse_dates=True)
        print(f'[data] FRED {name} unavailable: {e}')
        return pd.DataFrame()


def compute_ip_growth(ip_index):
    """Convert IP index to 12-month % growth rate."""
    return (ip_index / ip_index.shift(12) - 1) * 100


def fetch_fred_ea_ip():
    """Download EA IP index from FRED, compute 12-month growth on extended history."""
    series_id = 'EA19PRINTO01IXOBM'
    url = f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd=1999-01-01&coed=2025-12-01'
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text))
        df['date'] = pd.to_datetime(df['observation_date'])
        df = df.dropna(subset=[series_id]).set_index('date').sort_index()
        df = df[~df.index.duplicated(keep='last')]
        df['EA_IP_index'] = pd.to_numeric(df[series_id], errors='coerce')
        extended_idx = pd.date_range('1999-01-01', '2025-12-01', freq='MS')
        df = df.reindex(df.index.union(extended_idx))
        df = df.ffill().reindex(extended_idx)
        df['EA_IP_growth'] = (df['EA_IP_index'] / df['EA_IP_index'].shift(12) - 1) * 100
        df = df.loc['2000-01-01':]
        df.index.name = 'date'
        cache_path = os.path.join(RAW_DIR, 'EA_IP.csv')
        df[['EA_IP_index', 'EA_IP_growth']].to_csv(cache_path)
        print(f'[data] FRED EA IP downloaded with growth ({len(df)} monthly rows)')
        return df[['EA_IP_index', 'EA_IP_growth']]
    except Exception as e:
        cache_path = os.path.join(RAW_DIR, 'EA_IP.csv')
        if os.path.exists(cache_path):
            print(f'[data] Loading cached EA IP data')
            return pd.read_csv(cache_path, index_col=0, parse_dates=True)
        print(f'[data] EA IP unavailable: {e}')
        return pd.DataFrame()


def interpolate_gdp_to_monthly(gdp_annual, start='2000-01-01', end='2025-12-01'):
    """Interpolate annual GDP growth rates to monthly frequency using quadratic spline."""
    monthly_idx = pd.date_range(start=start, end=end, freq='MS')
    monthly = pd.DataFrame(index=monthly_idx)
    monthly['year'] = monthly.index.year
    monthly = monthly.join(gdp_annual, on='year')
    monthly = monthly.drop(columns='year')
    monthly['UA_GDP_growth'] = monthly['UA_GDP_growth'].interpolate(method='quadratic', limit_direction='both')
    monthly.columns = ['UA_GDP_growth']
    return monthly


def build_master_panel():
    ecb = load_ecb_hicp_panel()
    ecb = ecb.drop(columns=[c for c in ecb.columns if c not in EA_COUNTRIES])

    ukr_raw = load_ukraine_cpi_raw()
    ukr_yoy = cpi_mom_to_yoy(ukr_raw['OBS_VALUE'])
    ukr_yoy = ukr_yoy.to_frame()

    combined = ecb.join(ukr_yoy, how='outer')

    ea_ip = fetch_fred_ea_ip()
    if not ea_ip.empty:
        combined = combined.join(ea_ip, how='left')
        print(f'[data] EA IP growth joined ({ea_ip.columns.tolist()})')

    gdp_annual = fetch_wb_ukraine_gdp()
    if not gdp_annual.empty and 'UA_GDP_growth' in gdp_annual.columns:
        monthly_gdp = interpolate_gdp_to_monthly(gdp_annual)
        combined = combined.join(monthly_gdp, how='left')
        print('[data] UA GDP growth (interpolated from annual) added')

    exr_df = fetch_with_fallback(
        None, 'eur_uah.csv',
        parse_fn=lambda _: fetch_ecb_exchange_rate().reset_index()
    )
    if not exr_df.empty and 'EUR_UAH' in exr_df.columns:
        exr_df['date'] = pd.to_datetime(exr_df['date'])
        exr_df = exr_df.set_index('date')
        combined = combined.join(exr_df[['EUR_UAH']], how='left')

    mrr_df = fetch_with_fallback(
        None, 'ecb_mrr.csv',
        parse_fn=lambda _: fetch_ecb_policy_rate().reset_index()
    )
    if not mrr_df.empty and 'ECB_MRR' in mrr_df.columns:
        mrr_df['date'] = pd.to_datetime(mrr_df['date'])
        mrr_df = mrr_df.set_index('date')
        combined = combined.join(mrr_df[['ECB_MRR']], how='left')

    eur_usd = fetch_fred_series('DEXUSEU', 'EUR_USD')
    if not eur_usd.empty:
        combined = combined.join(eur_usd[['EUR_USD']], how='left')

    ecb_rate = fetch_fred_series('ECBMRRFR', 'ECB_MRR')
    if not ecb_rate.empty:
        combined = combined.join(ecb_rate[['ECB_MRR']], how='left')

    print(f'[data] Master panel columns: {list(combined.columns)}')
    print(f'[data] Combined inflation panel shape: {combined.shape}')
    combined.to_csv(os.path.join(PROC_DIR, 'master_panel.csv'))
    combined[EA_COUNTRIES + ['UA']].to_csv(os.path.join(PROC_DIR, 'inflation_panel.csv'))

    return combined


if __name__ == '__main__':
    master = build_master_panel()
    print(f'[data] Master panel columns: {list(master.columns)}')
    print(f'[data] Date range: {master.index[0]} to {master.index[-1]}')
