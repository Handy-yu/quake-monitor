import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from quake_analysis import compute_bvalue, format_energy, seismic_energy


class TestSeismicEnergy(unittest.TestCase):
    def test_energy_is_monotonic(self):
        self.assertGreater(seismic_energy(7.0), seismic_energy(6.0))

    def test_one_magnitude_unit_ratio(self):
        # +1 magnitude -> ~31.6x energy (10^1.5)
        self.assertAlmostEqual(seismic_energy(7.0) / seismic_energy(6.0), 10 ** 1.5, places=2)

    def test_known_energy_m0(self):
        self.assertAlmostEqual(seismic_energy(0.0), 10 ** 4.8, places=0)


class TestFormatEnergy(unittest.TestCase):
    def test_units(self):
        self.assertEqual(format_energy(1e18), "1.00 EJ")
        self.assertEqual(format_energy(5e15), "5.00 PJ")
        self.assertEqual(format_energy(2.5e12), "2.50 TJ")
        self.assertEqual(format_energy(1e9), "1.00 GJ")


class TestComputeBvalue(unittest.TestCase):
    def test_too_few_samples_returns_none(self):
        self.assertEqual(compute_bvalue(np.array([3.0, 3.1, 3.2])), (None, None))

    def test_known_b_value(self):
        mags = np.array([3.0] * 10 + [4.0] * 10)
        b, se = compute_bvalue(mags, mc=2.5)
        self.assertAlmostEqual(b, 0.43, places=2)
        self.assertAlmostEqual(se, 0.10, places=1)

    def test_mean_equals_mc_does_not_divide_by_zero(self):
        mags = np.array([2.5] * 20)
        self.assertEqual(compute_bvalue(mags, mc=2.5), (None, None))


if __name__ == "__main__":
    unittest.main()
