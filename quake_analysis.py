"""Pure analysis functions for QuakeMonitor (no Streamlit dependency)."""
import numpy as np


def seismic_energy(magnitude):
    """Gutenberg-Richter energy: log10(E) = 4.8 + 1.5*M (E in Joules)"""
    return 10 ** (4.8 + 1.5 * magnitude)


def format_energy(joules):
    if joules >= 1e18:
        return f"{joules/1e18:.2f} EJ"
    elif joules >= 1e15:
        return f"{joules/1e15:.2f} PJ"
    elif joules >= 1e12:
        return f"{joules/1e12:.2f} TJ"
    else:
        return f"{joules/1e9:.2f} GJ"


def compute_bvalue(magnitudes, mc=2.5):
    """Compute b-value using Maximum Likelihood method (Aki 1965)"""
    mags = magnitudes[magnitudes >= mc]
    if len(mags) < 20:
        return None, None
    denom = mags.mean() - mc
    if denom <= 0:
        return None, None
    b = np.log10(np.e) / denom
    se = b / np.sqrt(len(mags))
    return round(b, 2), round(se, 2)
