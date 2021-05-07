"""This module implements the VariableLocationGate."""
from __future__ import annotations

from typing import Sequence

import numpy as np

from bqskit.ir.gate import Gate
from bqskit.qis.permutation import PermutationMatrix
from bqskit.qis.unitary.unitarymatrix import UnitaryMatrix
from bqskit.utils.math import softmax
from bqskit.utils.typing import is_valid_location


class VariableLocationGate(Gate):
    """
    The VariableLocationGate class.

    A VariableLocationGate continuously encodes multiple locations for another
    gate.

    """

    def __init__(self, gate: Gate, locations: Sequence[Sequence[int]]) -> None:
        """
        Create a gate that has parameterized location.

        Args:
            gate (Gate): The gate to parameterize location for.

            locations (Sequence[Sequence[int]]): A sequence of locations.
                Each location represents a valid placement for gate.

        Raises:
            ValueError: If there are not enough locations or the locations
                are incorrectly sized.

        Notes:
            The locations are calculated in their own space and are not
            relative to a circuit. This means you should consider the
            VariableLocationGate as its own circuit when deciding the
            locations. For example, if you want to multiplex the (2, 3)
            and (3, 5) placements of a CNOT on a 6-qubit circuit, then
            you would give the VariableLocationGate the (0, 1) and (1, 2)
            locations and place the VariableLocationGate on qubits
            (2, 3, 5) on the circuit.

        """
        if not isinstance(gate, Gate):
            raise TypeError('Expected gate object, got %s' % type(gate))

        if not all(is_valid_location(l) for l in locations):
            raise TypeError('Expected a sequence of valid locations.')

        if not all(len(l) == gate.get_size() for l in locations):
            raise ValueError('Invalid sized location.')

        if len(locations) < 1:
            raise ValueError('VLGs require at least 1 locations.')

        self.gate = gate
        self.name = 'VariableLocationGate(%s)' % gate.get_name()
        self.size = max(max(l) for l in locations) + 1
        self.locations = list(locations)

        # Calculate radixes and
        # Ensure that the gate can be applied to all locations
        radix_map: dict[int, int | None] = {i: None for i in range(self.size)}
        for l in locations:
            for radix, qudit_index in zip(gate.get_radixes(), l):
                if radix_map[qudit_index] is None:
                    radix_map[qudit_index] = radix
                elif radix_map[qudit_index] != radix:
                    raise ValueError(
                        'Gate cannot be applied to all locations'
                        ' due to radix mismatch.',
                    )

        if any(radix is None for radix in radix_map.values()):
            for idx, radix in radix_map.items():
                if radix is None:
                    radix_map[idx] = 2  # TODO: Re-evaluate
            # raise ValueError(
            #     'Unable to determine radix for qudit: %d.'
            #     % [radix is None for radix in radix_map.values()].index(True)
            #     + 'If a qudit is not included in the specified locations,'
            #     ' you should leave it out, see the attached note in the'
            #     " constructor's docstring for more info.",
            # )

        self.radixes = tuple(radix_map.values())
        self.num_params = self.gate.get_num_params() + len(locations)

        self.extension_size = self.size - self.gate.get_size()
        # TODO: This needs to changed for radixes
        self.I = np.identity(2 ** self.extension_size)
        self.perms = np.array([
            PermutationMatrix.from_qubit_location(self.size, l)
            for l in self.locations
        ])

    def get_location(self, params: Sequence[float]) -> tuple[int, ...]:
        """Returns the gate's location."""
        idx = np.argmax(self.split_params(params)[1])
        return self.locations[idx]

    def split_params(
            self, params: Sequence[float],
    ) -> tuple[Sequence[float], Sequence[float]]:
        """Split params into subgate params and location params."""
        return (
            params[:self.gate.get_num_params()],
            params[self.gate.get_num_params():],
        )

    def get_unitary(self, params: Sequence[float] = []) -> UnitaryMatrix:
        """Returns the unitary for this gate, see Unitary for more info."""
        self.check_parameters(params)
        a, l = self.split_params(params)
        l = softmax(l, 10)

        P = np.sum([a * s.get_numpy() for a, s in zip(l, self.perms)], 0)
        G = self.gate.get_unitary(a)
        PGPT = P @ np.kron(G.get_numpy(), self.I) @ P.T
        return UnitaryMatrix.closest_to(PGPT, self.get_radixes())

    def get_grad(self, params: Sequence[float] = []) -> np.ndarray:
        """Returns the gradient for this gate, see Unitary for more info."""
        return self.get_unitary_and_grad(params)[1]

    def get_unitary_and_grad(
        self,
        params: Sequence[float] = [],
    ) -> tuple[UnitaryMatrix, np.ndarray]:
        """Returns the unitary and gradient for this gate."""
        self.check_parameters(params)
        a, l = self.split_params(params)
        l = softmax(l, 10)

        P = np.sum([a * s.get_numpy() for a, s in zip(l, self.perms)], 0)
        G = np.kron(self.gate.get_unitary(a).get_numpy(), self.I)
        PG = P @ G
        GPT = G @ P.T
        PGPT = P @ GPT

        dG = self.gate.get_grad(a)
        dG = np.kron(dG, self.I)
        dG = P @ dG @ P.T

        perm_array = np.array([perm.get_numpy() for perm in self.perms])
        dP = perm_array @ GPT + PG @ perm_array.transpose((0, 2, 1)) - 2 * PGPT
        dP = np.array([10 * x * y for x, y in zip(l, dP)])
        return PGPT, np.concatenate([dG, dP])
