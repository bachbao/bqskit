"""This module implements the FrozenParameterGate."""
from __future__ import annotations

from typing import Sequence

import numpy as np

from bqskit.ir import Gate
from bqskit.qis.unitarymatrix import UnitaryMatrix


class FrozenParameterGate(Gate):
    """A composed gate which fixes some parameters of another gate."""

    def __init__(self, gate: Gate, fixed_params: dict[int, float]) -> None:
        """
        Create a gate which fixes some of the parameters it takes.

        Args:
            gate (Gate): The Gate to fix the parameters of.
            fixed_params (dict[int, float]): A dictionary mapping parameters
                indices to the fixed value they should be.

        Raises:
            ValueError: If any of the `fixed_params` indices are greater
                than the number of parameters `gate` takes or less than 0
                or if the total amount of `fixed_params` is larger than
                the number of parameters `gate` takes.
        """
        if not isinstance(gate, Gate):
            raise TypeError('Expected gate, got %s.' % type(gate))
        if not isinstance(fixed_params, dict):
            raise TypeError(
                'Expected dict for fixed_params, got %s.' % type(fixed_params),
            )
        if not len(fixed_params) <= gate.get_num_params():
            raise ValueError(
                'Too many fixed parameters specified, expected at most'
                ' %d, got %d' % (gate.get_num_params(), len(fixed_params)),
            )
        keys = list(fixed_params.keys())
        values = list(fixed_params.values())
        if not all(isinstance(p, int) for p in keys):
            fail_idx = [isinstance(p, int) for p in keys].index(False)
            raise TypeError(
                'Expected fixed_params keys to be int, got %s.'
                % type(keys[fail_idx]),
            )
        if not all(isinstance(p, float) for p in values):
            fail_idx = [isinstance(p, float) for p in values].index(False)
            raise TypeError(
                'Expected fixed_params values to be float, got %s.'
                % type(values[fail_idx]),
            )
        if not all(0 <= p < gate.get_num_params() for p in keys):
            fail_idx = [
                0 <= p < gate.get_num_params()
                for p in keys
            ].index(False)
            raise ValueError(
                'Expected parameter index to be non-negative integer'
                ' < %d, got %d.' % (gate.get_num_params(), keys[fail_idx]),
            )

        self.gate = gate
        self.num_params = gate.get_num_params() - len(fixed_params)
        self.size = gate.get_size()
        self.radixes = gate.get_radixes()
        self.fixed_params = fixed_params
        self.unfixed_param_idxs = [
            i for i in range(gate.get_num_params())
            if i not in self.fixed_params.keys()
        ]

    def get_unitary(self, params: Sequence[float] = []) -> UnitaryMatrix:
        """Returns the unitary for this gate, see Unitary for more info."""
        return self.gate.get_unitary(self.get_full_params(params))

    def get_grad(self, params: Sequence[float] = []) -> np.ndarray:
        """Returns the gradient for this gate, see Gate for more info."""
        grads = self.gate.get_grad(self.get_full_params(params))
        return grads[self.unfixed_param_idxs, :, :]

    def optimize(self, env_matrix: np.ndarray) -> list[float]:
        """Returns optimal parameters with respect to an environment matrix."""
        params = self.gate.optimize(env_matrix)
        return [
            p for i, p in enumerate(params)
            if i in self.unfixed_param_idxs
        ]

    def get_name(self) -> str:
        """Returns the name of the gate, see Gate for more info."""
        return '%s(%s, %s)' % (
            self.__class__.__name__,
            self.gate.get_name(),
            str(self.fixed_params),
        )

    def get_full_params(self, params: Sequence[float]) -> list[float]:
        """Returns the full parameter list for the underlying gate."""
        self.check_parameters(params)
        args = list(params)
        for idx in sorted(self.fixed_params):
            args.insert(idx, self.fixed_params[idx])
        return args


def with_frozen_params(
        self: Gate,
        frozen_params: dict[int, float],
) -> FrozenParameterGate:
    return FrozenParameterGate(self, frozen_params)


def with_all_frozen_params(
    self: Gate,
    params: list[float],
) -> FrozenParameterGate:
    return FrozenParameterGate(self, {i: x for i, x in enumerate(params)})


Gate.with_frozen_params = with_frozen_params
Gate.with_all_frozen_params = with_all_frozen_params
