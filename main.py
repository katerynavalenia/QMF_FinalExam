import os
import sys
import importlib.util
import traceback
import warnings
warnings.filterwarnings('ignore')

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_DIR, 'src')
sys.path.insert(0, SRC_DIR)


def import_src(name):
    path = os.path.join(SRC_DIR, f'{name}.py')
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


print('=' * 70)
print('  QMF Final Exam: Counterfactual Inflation Analysis for Ukraine')
print('  What If Ukraine Had Been Part of the Euro Area?')
print('=' * 70)

try:
    print('\n[main] === PHASE 1: Data Loading & Harmonisation ===')
    data_mod = import_src('01_data')
    master = data_mod.build_master_panel()
    print(f'[main] Master panel: {master.shape[0]} rows x {master.shape[1]} columns')
except Exception as e:
    print(f'[main] ERROR in Phase 1 (Data): {e}')
    traceback.print_exc()
    master = None

try:
    print('\n[main] === PHASE 2: Part A - Monetary Regime Chronology ===')
    part_a_mod = import_src('02_part_a')
    regime_table, treatment_intensity = part_a_mod.run_part_a()
except Exception as e:
    print(f'[main] ERROR in Phase 2 (Part A): {e}')
    traceback.print_exc()
    regime_table, treatment_intensity = None, None

try:
    print('\n[main] === PHASE 3: Part B - SVAR Counterfactual (Core Method) ===')
    svar_mod = import_src('03_svar')
    ua_svar, ea_svar, cf_svar = svar_mod.run_svar_counterfactual()
except Exception as e:
    print(f'[main] ERROR in Phase 3 (SVAR): {e}')
    traceback.print_exc()
    ua_svar, ea_svar, cf_svar = None, None, None

try:
    print('\n[main] === PHASE 4: Part B - Factor Model Counterfactual (Robustness) ===')
    factor_mod = import_src('04_factor')
    cf_factor, loadings, explained = factor_mod.run_factor_counterfactual()
except Exception as e:
    print(f'[main] ERROR in Phase 4 (Factor Model): {e}')
    traceback.print_exc()
    cf_factor, loadings, explained = None, None, None

try:
    print('\n[main] === PHASE 5: Output Figures & Interpretation ===')
    fig_mod = import_src('05_figures')
    fig_mod.run_figures()
except Exception as e:
    print(f'[main] ERROR in Phase 5 (Figures): {e}')
    traceback.print_exc()

print('\n' + '=' * 70)
print('  ANALYSIS COMPLETE')
print('=' * 70)
print('  Output files:')
print('    - output/counterfactual_main.pdf (main figure)')
print('    - output/counterfactual_main.png')
print('    - output/inflation_panel.png')
print('    - output/structural_shocks.png')
print('    - output/irfs.png (structural BQ IRFs)')
print('    - output/svar_counterfactual.csv')
print('    - output/factor_counterfactual.csv')
print('    - output/shock_correlations.csv')
print('    - output/var_diagnostics_ua.csv / var_diagnostics_ea.csv')
print('    - output/adf_tests.csv')
print('    - output/variance_decomposition.csv')
print('    - output/shocks_ukraine.csv / shocks_ea.csv')
print('    - output/ea_common_factors.csv / ea_factor_loadings.csv')
print('    - output/part_a_regime_table.csv')
print('    - output/treatment_intensity.csv')
print('    - output/irf_ukraine.csv')
print('    - docs/part_a_argument.txt / part_b_interpretation.txt')
print('=' * 70)
