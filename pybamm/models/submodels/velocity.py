#
# Equation classes for the electrolyte velocity
#
import pybamm


class Velocity(pybamm.SubModel):
    """Electrolyte velocity

    Parameters
    ----------
    set_of_parameters : parameter class
        The parameters to use for this submodel

    *Extends:* :class:`pybamm.SubModel`
    """

    def __init__(self, set_of_parameters):
        super().__init__(set_of_parameters)

    def get_explicit_leading_order(self, reactions):
        """
        Provides explicit velocity for the leading-order models, as a post-processing
        step.

        Parameters
        ----------
        reactions : dict
            Dictionary of reaction variables
        """
        # Set up
        param = self.set_of_parameters
        l_n = pybamm.geometric_parameters.l_n
        l_s = pybamm.geometric_parameters.l_s
        x_n = pybamm.standard_spatial_vars.x_n
        x_s = pybamm.standard_spatial_vars.x_s
        x_p = pybamm.standard_spatial_vars.x_p

        j_n = reactions["main"]["neg"]["aj"]
        j_p = reactions["main"]["pos"]["aj"]

        # Volume-averaged velocity
        v_box_n = param.beta_n * pybamm.outer(j_n, x_n)
        v_box_p = param.beta_p * pybamm.outer(j_p, (1 - x_p))
        v_box_n_right = pybamm.boundary_value(v_box_n, "right")
        v_box_p_left = pybamm.boundary_value(v_box_p, "left")
        v_box_s = (v_box_p_left - v_box_n_right) / l_s * (x_s - l_n) + v_box_n_right

        return self.get_variables((v_box_n, v_box_s, v_box_p))

    def get_variables(self, v_box_tuple):
        """
        Calculate dimensionless and dimensional variables for the electrolyte current
        submodel

        Parameters
        ----------
        v_box_tuple : tuple
            Tuple of mass-averaged velocities

        Returns
        -------
        dict
            Dictionary {string: :class:`pybamm.Symbol`} of relevant variables
        """
        vel_scale = self.set_of_parameters.velocity_scale
        v_box_n, v_box_s, v_box_p = v_box_tuple
        v_box = pybamm.Concatenation(v_box_n, v_box_s, v_box_p)

        return {
            "Negative electrode volume-averaged velocity": v_box_n,
            "Separator volume-averaged velocity": v_box_s,
            "Positive electrode volume-averaged velocity": v_box_p,
            "Volume-averaged velocity": v_box,
            "Negative electrode volume-averaged velocity [m.s-1]": vel_scale * v_box_n,
            "Separator volume-averaged velocity [m.s-1]": vel_scale * v_box_s,
            "Positive electrode volume-averaged velocity [m.s-1]": vel_scale * v_box_p,
            "Volume-averaged velocity [m.s-1]": vel_scale * v_box,
        }
