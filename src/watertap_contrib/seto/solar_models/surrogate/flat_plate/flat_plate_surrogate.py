###############################################################################
# WaterTAP Copyright (c) 2021, The Regents of the University of California,
# through Lawrence Berkeley National Laboratory, Oak Ridge National
# Laboratory, National Renewable Energy Laboratory, and National Energy
# Technology Laboratory (subject to receipt of any required approvals from
# the U.S. Dept. of Energy). All rights reserved.
#
# Please see the files COPYRIGHT.md and LICENSE.md for full copyright and license
# information, respectively. These files are also available online at the URL
# "https://github.com/watertap-org/watertap/"
#
###############################################################################

import os
import sys
from io import StringIO

from pyomo.environ import Var, Constraint, Suffix, units as pyunits

from idaes.core import declare_process_block_class
import idaes.core.util.scaling as iscale
from idaes.core.surrogate.surrogate_block import SurrogateBlock
from idaes.core.surrogate.pysmo_surrogate import PysmoSurrogate

from watertap_contrib.seto.core import SolarEnergyBase

__author__ = "Matthew Boyd"


@declare_process_block_class("FlatPlateSurrogate")
class FlatPlateSurrogateData(SolarEnergyBase):
    """
    Surrogate model for flat plate.
    """

    def build(self):
        super().build()

        self._tech_type = "flat_plate"

        self.heat_load = Var(
            initialize=1000,
            bounds=[100, 1000],
            units=pyunits.MW,
            doc="Rated plant heat capacity in MWt",
        )
        self.hours_storage = Var(
            initialize=20,
            bounds=[0, 26],
            units=pyunits.hour,
            doc="Rated plant hours of storage",
        )
        self.temperature_hot = Var(
            initialize=70,
            bounds=[50, 100],
            units=pyunits.C,
            doc="Hot outlet temperature",
        )

        self.heat_annual = Var(
            initialize=1000,
            units=pyunits.kWh,
            doc="Annual heat generated by flat plate",
        )
        self.electricity_annual = Var(
            initialize=20,
            units=pyunits.kWh,
            doc="Annual electricity consumed by flat plate",
        )

        stream = StringIO()
        oldstdout = sys.stdout
        sys.stdout = stream

        self.surrogate_inputs = [
            self.heat_load,
            self.hours_storage,
            self.temperature_hot,
        ]
        self.surrogate_outputs = [self.heat_annual, self.electricity_annual]

        self.input_labels = ["heat_load", "hours_storage", "temperature_hot"]
        self.output_labels = ["heat_annual", "electricity_annual"]

        self.surrogate_file = os.path.join(
            os.path.dirname(__file__), "flat_plate_surrogate.json"
        )
        self.surrogate_blk = SurrogateBlock(concrete=True)
        self.surrogate = PysmoSurrogate.load_from_file(self.surrogate_file)
        self.surrogate_blk.build_model(
            self.surrogate,
            input_vars=self.surrogate_inputs,
            output_vars=self.surrogate_outputs,
        )

        self.heat_constraint = Constraint(
            expr=self.heat_annual
            == self.heat * pyunits.convert(1 * pyunits.year, to_units=pyunits.hour)
        )

        self.electricity_constraint = Constraint(
            expr=self.electricity_annual
            == self.electricity
            * pyunits.convert(1 * pyunits.year, to_units=pyunits.hour)
        )

        # Revert back to standard output
        sys.stdout = oldstdout

        self.dataset_filename = os.path.join(
            os.path.dirname(__file__), "data/flat_plate_data.pkl"
        )
        self.n_samples = 100
        self.training_fraction = 0.8

    def calculate_scaling_factors(self):

        if iscale.get_scaling_factor(self.hours_storage) is None:
            sf = iscale.get_scaling_factor(self.hours_storage, default=1)
            iscale.set_scaling_factor(self.hours_storage, sf)

        if iscale.get_scaling_factor(self.heat_load) is None:
            sf = iscale.get_scaling_factor(self.heat_load, default=1e-2, warning=True)
            iscale.set_scaling_factor(self.heat_load, sf)

        if iscale.get_scaling_factor(self.temperature_hot) is None:
            sf = iscale.get_scaling_factor(
                self.temperature_hot, default=1e-1, warning=True
            )
            iscale.set_scaling_factor(self.temperature_hot, sf)

        if iscale.get_scaling_factor(self.heat_annual) is None:
            sf = iscale.get_scaling_factor(self.heat_annual, default=1e-4, warning=True)
            iscale.set_scaling_factor(self.heat_annual, sf)

        if iscale.get_scaling_factor(self.heat) is None:
            sf = iscale.get_scaling_factor(self.heat, default=1e-4, warning=True)
            iscale.set_scaling_factor(self.heat, sf)

        if iscale.get_scaling_factor(self.electricity_annual) is None:
            sf = iscale.get_scaling_factor(
                self.electricity_annual, default=1e-3, warning=True
            )
            iscale.set_scaling_factor(self.electricity_annual, sf)

        if iscale.get_scaling_factor(self.electricity) is None:
            sf = iscale.get_scaling_factor(self.electricity, default=1e-3, warning=True)
            iscale.set_scaling_factor(self.electricity, sf)

    def initialize_build(self):
        pass
