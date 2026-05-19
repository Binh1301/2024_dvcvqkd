import numpy as np
import matplotlib.pyplot as plt
import math
from scipy.linalg import sqrtm

# =====================================================
# 1. PARAMETERS
# =====================================================

N = 20              # Fock cutoff
alpha = 1.0         # modulation amplitude
M = 4               # QPSK example

# =====================================================
# 2. CREATE COHERENT STATE |alpha>
# =====================================================

def coherent_state(alpha, N):
    """
    Return coherent state in Fock basis.
    |alpha> = exp(-|alpha|^2/2) sum alpha^n/sqrt(n!) |n>
    """

    vec = np.zeros(N, dtype=complex)

    for n in range(N):
        vec[n] = (
            np.exp(-abs(alpha)**2 / 2)
            * alpha**n
            / np.sqrt(math.factorial(n))
        )

    return vec

# =====================================================
# 3. QPSK CONSTELLATION
# =====================================================

states = []

for k in range(M):
    phase = 2 * np.pi * k / M
    a_k = alpha * np.exp(1j * phase)
    states.append(coherent_state(a_k, N))

# =====================================================
# 4. DENSITY MATRIX rho
# rho = sum p_k |alpha_k><alpha_k|
# =====================================================

rho = np.zeros((N, N), dtype=complex)

for psi in states:
    rho += np.outer(psi, np.conjugate(psi)) / M

# =====================================================
# 5. EIGEN-DECOMPOSITION
# rho = V D V^†
# =====================================================

eigvals, V = np.linalg.eigh(rho)

# Remove tiny negative numerical noise
# due to floating point precision

eigvals[eigvals < 0] = 0

D = np.diag(eigvals)

# =====================================================
# 6. sqrt(D)
# =====================================================

sqrt_D = np.diag(np.sqrt(eigvals))
plt.show()
