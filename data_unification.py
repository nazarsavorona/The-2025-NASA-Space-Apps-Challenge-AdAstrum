"""
Data Unification Script for Kepler, K2, and TESS datasets
Creates a unified dataset from three different exoplanet detection missions
"""

import pandas as pd
import numpy as np
from pathlib import Path

def load_datasets():
    """Load all three datasets"""
    print("Loading datasets...")
    kepler = pd.read_csv('data/input/kepler.csv', comment='#')
    k2 = pd.read_csv('data/input/k2.csv', comment='#')
    toi = pd.read_csv('data/input/toi.csv', comment='#')
    
    print(f"Kepler: {len(kepler)} rows")
    print(f"K2: {len(k2)} rows")
    print(f"TOI (TESS): {len(toi)} rows")
    
    return kepler, k2, toi

def normalize_disposition(value, source):
    """
    Normalize disposition values to binary classification:
    - CANDIDATE (1): True planet candidates
    - FALSE POSITIVE (0): False positives or non-planets
    """
    if pd.isna(value):
        return np.nan
    
    value_str = str(value).upper()
    
    if source == 'kepler':
        # Kepler: CANDIDATE vs FALSE POSITIVE
        if 'CANDIDATE' in value_str:
            return 1
        elif 'FALSE POSITIVE' in value_str:
            return 0
        else:
            return np.nan
    
    elif source == 'k2':
        # K2: CONFIRMED and CANDIDATE are positives, FALSE POSITIVE and REFUTED are negatives
        if 'CONFIRMED' in value_str or 'CANDIDATE' in value_str:
            return 1
        elif 'FALSE POSITIVE' in value_str or 'REFUTED' in value_str:
            return 0
        else:
            return np.nan
    
    elif source == 'toi':
        # TOI: CP (Confirmed Planet), PC (Planet Candidate), KP (Known Planet) are positives
        # FP (False Positive), FA (False Alarm) are negatives
        # APC (Ambiguous Planet Candidate) is treated as positive but with lower confidence
        if value_str in ['CP', 'PC', 'KP', 'APC']:
            return 1
        elif value_str in ['FP', 'FA']:
            return 0
        else:
            return np.nan
    
    return np.nan

def create_unified_kepler(kepler):
    """Create unified dataframe from Kepler dataset"""
    print("\nProcessing Kepler dataset...")
    
    unified = pd.DataFrame({
        'source': 'kepler',
        'object_id': kepler['kepid'],
        'disposition_raw': kepler['koi_disposition'],
        
        # Transit/Orbital Properties
        'orbital_period': kepler['koi_period'],
        'orbital_period_err': kepler[['koi_period_err1', 'koi_period_err2']].abs().mean(axis=1),
        'transit_duration': kepler['koi_duration'],
        'transit_duration_err': kepler[['koi_duration_err1', 'koi_duration_err2']].abs().mean(axis=1),
        'transit_depth': kepler['koi_depth'],
        'transit_depth_err': kepler[['koi_depth_err1', 'koi_depth_err2']].abs().mean(axis=1),
        'impact_parameter': kepler['koi_impact'],
        'impact_parameter_err': kepler[['koi_impact_err1', 'koi_impact_err2']].abs().mean(axis=1),
        'eccentricity': kepler['koi_eccen'],
        'eccentricity_err': kepler[['koi_eccen_err1', 'koi_eccen_err2']].abs().mean(axis=1),
        'inclination': kepler['koi_incl'],
        'inclination_err': kepler[['koi_incl_err1', 'koi_incl_err2']].abs().mean(axis=1),
        'longitude_periastron': kepler['koi_longp'],
        
        # Planet Properties
        'planet_radius': kepler['koi_prad'],
        'planet_radius_err': kepler[['koi_prad_err1', 'koi_prad_err2']].abs().mean(axis=1),
        'planet_equilibrium_temp': kepler['koi_teq'],
        'planet_equilibrium_temp_err': kepler[['koi_teq_err1', 'koi_teq_err2']].abs().mean(axis=1),
        'insolation_flux': kepler['koi_insol'],
        'insolation_flux_err': kepler[['koi_insol_err1', 'koi_insol_err2']].abs().mean(axis=1),
        'semimajor_axis': kepler['koi_sma'],
        'dist_over_stellar_radius': kepler['koi_dor'],
        'radius_ratio': kepler['koi_ror'],
        
        # Stellar Properties
        'stellar_temp': kepler['koi_steff'],
        'stellar_temp_err': kepler[['koi_steff_err1', 'koi_steff_err2']].abs().mean(axis=1),
        'stellar_logg': kepler['koi_slogg'],
        'stellar_logg_err': kepler[['koi_slogg_err1', 'koi_slogg_err2']].abs().mean(axis=1),
        'stellar_radius': kepler['koi_srad'],
        'stellar_radius_err': kepler[['koi_srad_err1', 'koi_srad_err2']].abs().mean(axis=1),
        'stellar_mass': kepler['koi_smass'],
        'stellar_mass_err': kepler[['koi_smass_err1', 'koi_smass_err2']].abs().mean(axis=1),
        'stellar_metallicity': kepler['koi_smet'],
        'stellar_metallicity_err': kepler[['koi_smet_err1', 'koi_smet_err2']].abs().mean(axis=1),
        
        # Additional useful features (REMOVED fp_flags - DATA LEAKAGE!)
        # False positive flags are derived from disposition analysis and cause data leakage
        'signal_to_noise': kepler['koi_model_snr'],
        'num_transits': kepler['koi_num_transits'],
    })
    
    # Apply disposition normalization
    unified['disposition'] = unified['disposition_raw'].apply(lambda x: normalize_disposition(x, 'kepler'))
    
    print(f"Unified Kepler: {len(unified)} rows, {len(unified.columns)} columns")
    return unified

def create_unified_k2(k2):
    """Create unified dataframe from K2 dataset"""
    print("\nProcessing K2 dataset...")
    
    unified = pd.DataFrame({
        'source': 'k2',
        'object_id': k2['epic_hostname'].fillna(k2['epic_candname']),
        'disposition_raw': k2['disposition'],
        
        # Transit/Orbital Properties
        'orbital_period': k2['pl_orbper'],
        'orbital_period_err': k2[['pl_orbpererr1', 'pl_orbpererr2']].abs().mean(axis=1),
        'transit_duration': k2['pl_trandur'],
        'transit_duration_err': k2[['pl_trandurerr1', 'pl_trandurerr2']].abs().mean(axis=1),
        'transit_depth': k2['pl_trandep'],
        'transit_depth_err': k2[['pl_trandeperr1', 'pl_trandeperr2']].abs().mean(axis=1),
        'impact_parameter': k2['pl_imppar'],
        'impact_parameter_err': k2[['pl_impparerr1', 'pl_impparerr2']].abs().mean(axis=1),
        'eccentricity': k2['pl_orbeccen'],
        'eccentricity_err': k2[['pl_orbeccenerr1', 'pl_orbeccenerr2']].abs().mean(axis=1),
        'inclination': k2['pl_orbincl'],
        'inclination_err': k2[['pl_orbinclerr1', 'pl_orbinclerr2']].abs().mean(axis=1),
        'longitude_periastron': np.nan,  # Not available in K2
        
        # Planet Properties
        'planet_radius': k2['pl_rade'],
        'planet_radius_err': k2[['pl_radeerr1', 'pl_radeerr2']].abs().mean(axis=1),
        'planet_equilibrium_temp': k2['pl_eqt'],
        'planet_equilibrium_temp_err': k2[['pl_eqterr1', 'pl_eqterr2']].abs().mean(axis=1),
        'insolation_flux': k2['pl_insol'],
        'insolation_flux_err': k2[['pl_insolerr1', 'pl_insolerr2']].abs().mean(axis=1),
        'semimajor_axis': k2['pl_orbsmax'],
        'dist_over_stellar_radius': k2['pl_ratdor'],
        'radius_ratio': k2['pl_ratror'],
        
        # Stellar Properties
        'stellar_temp': k2['st_teff'],
        'stellar_temp_err': k2[['st_tefferr1', 'st_tefferr2']].abs().mean(axis=1),
        'stellar_logg': k2['st_logg'],
        'stellar_logg_err': k2[['st_loggerr1', 'st_loggerr2']].abs().mean(axis=1),
        'stellar_radius': k2['st_rad'],
        'stellar_radius_err': k2[['st_raderr1', 'st_raderr2']].abs().mean(axis=1),
        'stellar_mass': k2['st_mass'],
        'stellar_mass_err': k2[['st_masserr1', 'st_masserr2']].abs().mean(axis=1),
        'stellar_metallicity': k2['st_met'],
        'stellar_metallicity_err': k2[['st_meterr1', 'st_meterr2']].abs().mean(axis=1),
        
        # Additional useful features (REMOVED fp_flags - not available and would cause data leakage)
        'signal_to_noise': np.nan,
        'num_transits': np.nan,
        
        # K2-specific features
        'planet_mass': k2['pl_masse'],
        'discovery_method': k2['discoverymethod'],
        'discovery_year': k2['disc_year'],
    })
    
    # Apply disposition normalization
    unified['disposition'] = unified['disposition_raw'].apply(lambda x: normalize_disposition(x, 'k2'))
    
    print(f"Unified K2: {len(unified)} rows, {len(unified.columns)} columns")
    return unified

def create_unified_toi(toi):
    """Create unified dataframe from TOI (TESS) dataset"""
    print("\nProcessing TOI (TESS) dataset...")
    
    # Note: TOI uses 'pl_trandurh' (hours), need to convert or handle appropriately
    unified = pd.DataFrame({
        'source': 'toi',
        'object_id': toi['tid'],
        'disposition_raw': toi['tfopwg_disp'],
        
        # Transit/Orbital Properties
        'orbital_period': toi['pl_orbper'],
        'orbital_period_err': toi[['pl_orbpererr1', 'pl_orbpererr2']].abs().mean(axis=1),
        'transit_duration': toi['pl_trandurh'] * 24 if 'pl_trandurh' in toi.columns else np.nan,  # Convert hours to same unit
        'transit_duration_err': toi[['pl_trandurherr1', 'pl_trandurherr2']].abs().mean(axis=1) * 24 if 'pl_trandurh' in toi.columns else np.nan,
        'transit_depth': toi['pl_trandep'],
        'transit_depth_err': toi[['pl_trandeperr1', 'pl_trandeperr2']].abs().mean(axis=1),
        'impact_parameter': np.nan,  # Not available in TOI
        'impact_parameter_err': np.nan,
        'eccentricity': np.nan,  # Not available in TOI
        'eccentricity_err': np.nan,
        'inclination': np.nan,  # Not available in TOI
        'inclination_err': np.nan,
        'longitude_periastron': np.nan,  # Not available in TOI
        
        # Planet Properties
        'planet_radius': toi['pl_rade'],
        'planet_radius_err': toi[['pl_radeerr1', 'pl_radeerr2']].abs().mean(axis=1),
        'planet_equilibrium_temp': toi['pl_eqt'],
        'planet_equilibrium_temp_err': toi[['pl_eqterr1', 'pl_eqterr2']].abs().mean(axis=1),
        'insolation_flux': toi['pl_insol'],
        'insolation_flux_err': toi[['pl_insolerr1', 'pl_insolerr2']].abs().mean(axis=1),
        'semimajor_axis': np.nan,
        'dist_over_stellar_radius': np.nan,
        'radius_ratio': np.nan,
        
        # Stellar Properties
        'stellar_temp': toi['st_teff'],
        'stellar_temp_err': toi[['st_tefferr1', 'st_tefferr2']].abs().mean(axis=1),
        'stellar_logg': toi['st_logg'],
        'stellar_logg_err': toi[['st_loggerr1', 'st_loggerr2']].abs().mean(axis=1),
        'stellar_radius': toi['st_rad'],
        'stellar_radius_err': toi[['st_raderr1', 'st_raderr2']].abs().mean(axis=1),
        'stellar_mass': np.nan,  # Not available in TOI
        'stellar_mass_err': np.nan,
        'stellar_metallicity': np.nan,  # Not available in TOI
        'stellar_metallicity_err': np.nan,
        
        # Additional useful features (REMOVED fp_flags - not available and would cause data leakage)
        'signal_to_noise': np.nan,
        'num_transits': np.nan,
        
        # TOI-specific features
        'stellar_distance': toi['st_dist'],
        'tess_magnitude': toi['st_tmag'],
    })
    
    # Apply disposition normalization
    unified['disposition'] = unified['disposition_raw'].apply(lambda x: normalize_disposition(x, 'toi'))
    
    print(f"Unified TOI: {len(unified)} rows, {len(unified.columns)} columns")
    return unified

def combine_datasets(kepler_unified, k2_unified, toi_unified):
    """Combine all three unified datasets"""
    print("\nCombining datasets...")
    
    # Concatenate all datasets
    combined = pd.concat([kepler_unified, k2_unified, toi_unified], ignore_index=True)
    
    # Remove rows with missing disposition (unable to classify)
    combined = combined.dropna(subset=['disposition'])
    
    print(f"\nCombined dataset: {len(combined)} rows, {len(combined.columns)} columns")
    print(f"\nDisposition distribution:")
    print(f"  CANDIDATE (1): {(combined['disposition'] == 1).sum()} ({(combined['disposition'] == 1).sum() / len(combined) * 100:.1f}%)")
    print(f"  FALSE POSITIVE (0): {(combined['disposition'] == 0).sum()} ({(combined['disposition'] == 0).sum() / len(combined) * 100:.1f}%)")
    
    print(f"\nSource distribution:")
    print(combined['source'].value_counts())
    
    return combined

def add_derived_features(df):
    """Add derived features that can be computed from existing ones"""
    print("\nAdding derived features...")
    
    # Signal strength (similar to what was in original kepler notebook)
    df['signal_strength'] = df['transit_depth'] * df['num_transits']
    
    # Duty cycle (if orbital period and transit duration available)
    df['duty_cycle'] = df['transit_duration'] / (df['orbital_period'] * 24)  # period in days, duration in hours
    
    # Planet-to-star radius ratio (if not already available)
    if df['radius_ratio'].isna().all():
        df['radius_ratio'] = df['planet_radius'] / df['stellar_radius']
    
    # Relative error metrics (uncertainty as fraction of measurement)
    df['orbital_period_rel_err'] = df['orbital_period_err'] / df['orbital_period']
    df['transit_depth_rel_err'] = df['transit_depth_err'] / df['transit_depth']
    df['planet_radius_rel_err'] = df['planet_radius_err'] / df['planet_radius']
    
    return df

def analyze_unified_data(df):
    """Analyze the unified dataset"""
    print("\n" + "="*80)
    print("UNIFIED DATASET ANALYSIS")
    print("="*80)
    
    print(f"\nTotal samples: {len(df)}")
    print(f"Total features: {len(df.columns)}")
    
    print(f"\n\nFeature completeness (% non-null):")
    completeness = (df.notna().sum() / len(df) * 100).sort_values(ascending=False)
    for feature, pct in completeness.items():
        if feature not in ['source', 'object_id', 'disposition_raw', 'disposition']:
            print(f"  {feature:35s}: {pct:5.1f}%")
    
    print(f"\n\nMissing value statistics:")
    missing = df.isna().sum().sort_values(ascending=False)
    missing_pct = (missing / len(df) * 100)
    for feature, count in missing[missing > 0].items():
        print(f"  {feature:35s}: {count:5d} ({missing_pct[feature]:5.1f}%)")

def save_unified_data(df, output_path='data/input/unified_exoplanets.csv'):
    """Save the unified dataset"""
    print(f"\nSaving unified dataset to {output_path}...")
    df.to_csv(output_path, index=False)
    print("Done!")

def main():
    # Load datasets
    kepler, k2, toi = load_datasets()
    
    # Create unified versions
    kepler_unified = create_unified_kepler(kepler)
    k2_unified = create_unified_k2(k2)
    toi_unified = create_unified_toi(toi)
    
    # Combine datasets
    combined = combine_datasets(kepler_unified, k2_unified, toi_unified)
    
    # Add derived features
    combined = add_derived_features(combined)
    
    # Analyze
    analyze_unified_data(combined)
    
    # Save
    save_unified_data(combined)
    
    return combined

if __name__ == '__main__':
    unified_data = main()
