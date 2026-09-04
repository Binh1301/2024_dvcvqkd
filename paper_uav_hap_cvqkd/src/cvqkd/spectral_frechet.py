"""Cluster-safe Hermitian matrix functions with explicit Fréchet VJPs."""

from __future__ import annotations

import torch


def _validate_hpd(matrix: torch.Tensor) -> None:
    if matrix.dtype != torch.complex128 or matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise TypeError("matrix must be a square complex128 tensor")
    if not bool(torch.allclose(matrix, matrix.mH, atol=1e-12, rtol=1e-12)):
        raise ValueError("matrix must be Hermitian")


def _frechet_vjp(
    values: torch.Tensor,
    vectors: torch.Tensor,
    upstream: torch.Tensor,
    *,
    inverse: bool,
) -> torch.Tensor:
    roots = torch.sqrt(values)
    denominator = roots[:, None] + roots[None, :]
    loewner = (
        -1.0 / (roots[:, None] * roots[None, :] * denominator)
        if inverse
        else 1.0 / denominator
    )
    hermitian_upstream = 0.5 * (upstream + upstream.mH)
    local = vectors.mH @ hermitian_upstream @ vectors
    gradient = vectors @ (loewner * local) @ vectors.mH
    return 0.5 * (gradient + gradient.mH)


class _HermitianInverseSqrt(torch.autograd.Function):
    @staticmethod
    def forward(ctx, matrix: torch.Tensor) -> torch.Tensor:
        _validate_hpd(matrix)
        values, vectors = torch.linalg.eigh(matrix)
        if not bool(torch.all(values > 0.0)):
            raise ValueError("inverse square root requires a positive definite matrix")
        ctx.save_for_backward(values, vectors)
        return vectors @ torch.diag(torch.rsqrt(values)).to(torch.complex128) @ vectors.mH

    @staticmethod
    def backward(ctx, upstream: torch.Tensor) -> tuple[torch.Tensor]:
        values, vectors = ctx.saved_tensors
        return (_frechet_vjp(values, vectors, upstream, inverse=True),)


class _HermitianSqrt(torch.autograd.Function):
    @staticmethod
    def forward(ctx, matrix: torch.Tensor) -> torch.Tensor:
        _validate_hpd(matrix)
        values, vectors = torch.linalg.eigh(matrix)
        if not bool(torch.all(values > 0.0)):
            raise ValueError("square root requires a positive definite matrix")
        ctx.save_for_backward(values, vectors)
        return vectors @ torch.diag(torch.sqrt(values)).to(torch.complex128) @ vectors.mH

    @staticmethod
    def backward(ctx, upstream: torch.Tensor) -> tuple[torch.Tensor]:
        values, vectors = ctx.saved_tensors
        return (_frechet_vjp(values, vectors, upstream, inverse=False),)


def hermitian_inverse_sqrt(matrix: torch.Tensor) -> torch.Tensor:
    """Return ``matrix**-1/2`` with the EVID-0031 custom VJP."""

    return _HermitianInverseSqrt.apply(matrix)


def hermitian_sqrt(matrix: torch.Tensor) -> torch.Tensor:
    """Return ``matrix**1/2`` with a cluster-safe Loewner VJP."""

    return _HermitianSqrt.apply(matrix)
