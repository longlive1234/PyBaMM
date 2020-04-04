#
# Tests for the Casadi Algebraic Solver class
#
import casadi
import pybamm
import unittest
import numpy as np
from scipy.optimize import least_squares


class TestCasadiAlgebraicSolver(unittest.TestCase):
    def test_algebraic_solver_init(self):
        solver = pybamm.CasadiAlgebraicSolver(tol=1e-4)
        self.assertEqual(solver.tol, 1e-4)

        solver.tol = 1e-5
        self.assertEqual(solver.tol, 1e-5)

    def test_simple_root_find(self):
        # Simple system: a single algebraic equation
        var = pybamm.Variable("var")
        model = pybamm.BaseModel()
        model.algebraic = {var: var + 2}
        model.initial_conditions = {var: 2}

        # create discretisation
        disc = pybamm.Discretisation()
        disc.process_model(model)

        # Solve
        solver = pybamm.CasadiAlgebraicSolver()
        solution = solver.solve(model, np.linspace(0, 1, 10))
        np.testing.assert_array_equal(solution.y, -2)

    def test_root_find_fail(self):
        class Model:
            y0 = np.array([2])
            t = casadi.MX.sym("t")
            y = casadi.MX.sym("y")
            p = casadi.MX.sym("p")
            casadi_algebraic = casadi.Function("alg", [t, y, p], [y ** 2 + 1])

            def algebraic_eval(self, t, y, inputs):
                # algebraic equation has no real root
                return y ** 2 + 1

        model = Model()

        solver = pybamm.CasadiAlgebraicSolver()
        with self.assertRaisesRegex(
            pybamm.SolverError, "Could not find acceptable solution: .../casadi"
        ):
            solver._integrate(model, np.array([0]), {})
        solver = pybamm.CasadiAlgebraicSolver(error_on_fail=False)
        with self.assertRaisesRegex(
            pybamm.SolverError, "Could not find acceptable solution: solver terminated"
        ):
            solver._integrate(model, np.array([0]), {})

    def test_model_solver_with_time(self):
        # Create model
        model = pybamm.BaseModel()
        var1 = pybamm.Variable("var1")
        var2 = pybamm.Variable("var2")
        model.algebraic = {var1: var1 - 3 * pybamm.t, var2: 2 * var1 - var2}
        model.initial_conditions = {var1: pybamm.Scalar(1), var2: pybamm.Scalar(4)}
        model.variables = {"var1": var1, "var2": var2}

        disc = pybamm.Discretisation()
        disc.process_model(model)

        # Solve
        t_eval = np.linspace(0, 1)
        solver = pybamm.CasadiAlgebraicSolver()
        solution = solver.solve(model, t_eval)

        sol = np.vstack((3 * t_eval, 6 * t_eval))
        np.testing.assert_array_almost_equal(solution.y, sol)
        np.testing.assert_array_almost_equal(
            model.variables["var1"].evaluate(t=t_eval, y=solution.y).flatten(),
            sol[0, :],
        )
        np.testing.assert_array_almost_equal(
            model.variables["var2"].evaluate(t=t_eval, y=solution.y).flatten(),
            sol[1, :],
        )

    def test_solve_with_input(self):
        # Simple system: a single algebraic equation
        var = pybamm.Variable("var")
        model = pybamm.BaseModel()
        model.algebraic = {var: var + pybamm.InputParameter("param")}
        model.initial_conditions = {var: 2}

        # create discretisation
        disc = pybamm.Discretisation()
        disc.process_model(model)

        # Solve
        solver = pybamm.CasadiAlgebraicSolver()
        solution = solver.solve(model, np.linspace(0, 1, 10), inputs={"param": 7})
        np.testing.assert_array_equal(solution.y, -7)


class TestCasadiAlgebraicSolverSensitivity(unittest.TestCase):
    def test_solve_with_symbolic_input(self):
        # Simple system: a single algebraic equation
        var = pybamm.Variable("var")
        model = pybamm.BaseModel()
        model.algebraic = {var: var + pybamm.InputParameter("param")}
        model.initial_conditions = {var: 2}
        model.variables = {"var": var}

        # create discretisation
        disc = pybamm.Discretisation()
        disc.process_model(model)

        # Solve
        solver = pybamm.CasadiAlgebraicSolver()
        solution = solver.solve(model, [0], inputs={"param": "[sym]"})
        self.assertIsInstance(solution, pybamm.CasadiSolution)
        np.testing.assert_array_equal(solution["var"].value(7), -7)
        np.testing.assert_array_equal(solution["var"].value(3), -3)
        np.testing.assert_array_equal(solution["var"].sensitivity(3), -1)

    def test_least_squares_fit(self):
        # Simple system: a single algebraic equation
        var = pybamm.Variable("var")
        model = pybamm.BaseModel()
        model.algebraic = {var: (var - pybamm.InputParameter("param"))}
        model.initial_conditions = {var: 2}
        model.variables = {"objective": (var ** 2 - 3) ** 2}

        # create discretisation
        disc = pybamm.Discretisation()
        disc.process_model(model)

        # Solve
        solver = pybamm.CasadiAlgebraicSolver()
        solution = solver.solve(model, [0], inputs={"param": "[sym]"})
        sol_var = solution["objective"]

        def objective(x):
            return sol_var.value(x).full().flatten()

        # without jacobian
        lsq_sol = least_squares(objective, 1)
        np.testing.assert_array_almost_equal(lsq_sol.x, np.sqrt(3), decimal=3)

        def jac(x):
            return sol_var.sensitivity(x)

        # with jacobian
        lsq_sol = least_squares(objective, 1, jac=jac)
        np.testing.assert_array_almost_equal(lsq_sol.x, np.sqrt(3), decimal=3)


if __name__ == "__main__":
    print("Add -v for more debug output")
    import sys

    if "-v" in sys.argv:
        debug = True
    pybamm.settings.debug_mode = True
    unittest.main()
