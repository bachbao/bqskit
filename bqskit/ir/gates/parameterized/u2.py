"""This module implements the U2Gate."""
from __future__ import annotations

from typing import Sequence

import numpy as np

from bqskit.ir.gates.qubitgate import QubitGate
from bqskit.qis.unitary.differentiable import DifferentiableUnitary
from bqskit.qis.unitary.unitarymatrix import UnitaryMatrix


class U2Gate(QubitGate, DifferentiableUnitary):
    """The U2 single qubit gate."""

    size = 1
    num_params = 2
    qasm_name = 'u2'

    def get_unitary(self, params: Sequence[float] = []) -> UnitaryMatrix:
        """Returns the unitary for this gate, see Unitary for more info."""
        self.check_parameters(params)

        sq2 = np.sqrt(2) / 2
        eip = np.exp(1j * params[0])
        eil = np.exp(1j * params[1])

        return UnitaryMatrix(
            [
                [sq2, -eil * sq2],
                [eip * sq2, eip * eil * sq2],
            ],
        )

    def get_grad(self, params: Sequence[float] = []) -> np.ndarray:
        """Returns the gradient for this gate, see Gate for more info."""
        self.check_parameters(params)

        sq2 = np.sqrt(2) / 2
        eip = np.exp(1j * params[0])
        eil = np.exp(1j * params[1])
        deip = 1j * np.exp(1j * params[0])
        deil = 1j * np.exp(1j * params[1])

        return np.array(
            [
                [  # wrt params[0]
                    [0, 0],
                    [deip * sq2, deip * eil * sq2],
                ],

                [  # wrt params[1]
                    [0, -deil * sq2],
                    [0, eip * deil * sq2],
                ],
            ], dtype=np.complex128,
        )