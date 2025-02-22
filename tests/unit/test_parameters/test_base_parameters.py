"""
Tests for the base_parameters.py
"""
import pybamm
import unittest


class TestBaseParameters(unittest.TestCase):
    def test_getattr__(self):
        param = pybamm.GeometricParameters()
        # ending in _n / _s / _p
        with self.assertRaisesRegex(AttributeError, "param.n.l"):
            getattr(param, "l_n")
        with self.assertRaisesRegex(AttributeError, "param.s.l"):
            getattr(param, "l_s")
        with self.assertRaisesRegex(AttributeError, "param.p.l"):
            getattr(param, "l_p")
        # _n_ in the name
        with self.assertRaisesRegex(AttributeError, "param.n.c_max"):
            getattr(param, "c_n_max")
        # _p_ in the name, function
        with self.assertRaisesRegex(AttributeError, "param.p.U_dimensional"):
            getattr(param, "U_p_dimensional")

    def test__setattr__(self):
        param = pybamm.ElectricalParameters()
        self.assertEqual(param.I_typ.print_name, r"I{}^{typ}")

        # domain gets added as a subscript
        param = pybamm.GeometricParameters()
        self.assertEqual(param.n.L.print_name, r"L_n")


if __name__ == "__main__":
    print("Add -v for more debug output")
    import sys

    if "-v" in sys.argv:
        debug = True
    pybamm.settings.debug_mode = True
    unittest.main()
