"""Explicit random-stream construction."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import random

import numpy as np
import torch


@dataclass(frozen=True)
class SplitSeeds:
    train_channel: int
    train_awgn: int
    validation_channel: int
    validation_awgn: int
    test_channel: int
    test_awgn: int

    def validate(self) -> None:
        values = tuple(self.__dict__.values())
        if len(set(values)) != len(values):
            raise ValueError("Train/validation/test seeds must be distinct.")
        if any(not isinstance(value, int) or value < 0 for value in values):
            raise ValueError("Seeds must be nonnegative integers.")


def seed_process(seed: int) -> None:
    if not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a nonnegative integer.")
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def derive_seed(base_seed: int, namespace: str, index: int = 0) -> int:
    """Derive a stable namespaced seed without split/epoch arithmetic collisions."""

    if not isinstance(base_seed, int) or base_seed < 0:
        raise ValueError("base_seed must be a nonnegative integer.")
    if not isinstance(namespace, str) or not namespace:
        raise ValueError("namespace must be a nonempty string.")
    if not isinstance(index, int) or index < 0:
        raise ValueError("index must be a nonnegative integer.")
    material = f"paper-uav-hap-cvqkd\0{base_seed}\0{namespace}\0{index}".encode("utf-8")
    value = int.from_bytes(hashlib.blake2b(material, digest_size=8).digest(), "big")
    return value & ((1 << 63) - 1)


def numpy_generator(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def torch_generator(seed: int, device: torch.device | str = "cpu") -> torch.Generator:
    device_type = torch.device(device).type
    return torch.Generator(device=device_type).manual_seed(seed)


def array_sha256(values: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(values)
    return hashlib.sha256(contiguous.view(np.uint8)).hexdigest()
