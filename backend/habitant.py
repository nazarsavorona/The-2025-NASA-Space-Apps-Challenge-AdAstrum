import pandas as pd

def compute_hz_boundaries(teff):
    def seff_coeffs_inner():
        Seff_sun = 1.107
        a = 1.332e-4
        b = 1.580e-8
        c = -8.308e-12
        d = -1.931e-15
        return Seff_sun, a, b, c, d

    def seff_coeffs_outer():
        Seff_sun = 0.356
        a = 6.171e-5
        b = 1.698e-9
        c = -3.198e-12
        d = -5.575e-16
        return Seff_sun, a, b, c, d

    Tstar = teff - 5780.0

    Seff0, a, b, c, d = seff_coeffs_inner()
    S_inner = Seff0 + a * Tstar + b * Tstar**2 + c * Tstar**3 + d * Tstar**4

    Seff0_o, ao, bo, co, do_ = seff_coeffs_outer()
    S_outer = Seff0_o + ao * Tstar + bo * Tstar**2 + co * Tstar**3 + do_ * Tstar**4

    return S_inner, S_outer

def classify_hz(row, buffer_frac=0.2):

    S = row["insolation_flux"]
    teff = row["stellar_temp"]

    S_in, S_out = compute_hz_boundaries(teff)

    S_in_opt = S_in * 0.9
    S_out_opt = S_out * 1.1

    if (S >= S_in) and (S <= S_out):
        width = S_out - S_in
        inner_core = S_in + buffer_frac * width
        outer_core = S_out - buffer_frac * width
        if (S >= inner_core) and (S <= outer_core):
            return "Conservative"
        else:
            return "Edge"
    elif (S >= S_in_opt) and (S <= S_out_opt):
        return "Optimistic"
    else:
        return "outside"

def is_habitable_zone(df: pd.DataFrame):
    df = df.copy()
    df["predicted_habitable"] = df.apply(classify_hz, axis=1)
    return df

def is_habitable_zone_simplest(features_df: pd.DataFrame):
    optimistic_inner = 1.78
    conservative_inner = 1.06
    conservative_outer = 0.36
    optimistic_outer = 0.32

    def classify(flux):
        if flux is None or pd.isna(flux):
            return "Unknown"
        if conservative_outer <= flux <= conservative_inner:
            return "Conservative"
        elif optimistic_outer <= flux <= optimistic_inner:
            return "Optimistic"
        else:
            return "Outside"

    features_df = features_df.copy()
    features_df["predicted_habitable"] = features_df["insolation_flux"].apply(classify)

    return features_df