"""This module implements the CZGate."""
from __future__ import annotations

import numpy as np

from bqskit.ir.gates.constantgate import ConstantGate
from bqskit.ir.gates.qubitgate import QubitGate
from bqskit.qis.unitarymatrix import UnitaryMatrix


class CZGate(ConstantGate, QubitGate):
    """The controlled-Z gate."""

    size = 2
    qasm_name = "cz"
    utry = UnitaryMatrix(
        [
            [1, 0, 0,  0],
            [0, 1, 0,  0],
            [0, 0, 1,  0],
            [0, 0, 0, -1],
        ]
    )
