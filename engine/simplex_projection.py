def project_to_simplex(w):
    """Project vector w onto the probability simplex (sum = 1, all >= 0).
    Uses the O(N log N) algorithm from Wang & Carreira-Perpinan 2013."""
    n = len(w)
    if n == 0:
        return w
    u = sorted(w, reverse=True)
    rho = 0
    cum_sum = 0.0
    for j in range(n):
        cum_sum += u[j]
        if u[j] - (cum_sum - 1.0) / (j + 1) > 0:
            rho = j + 1
    theta = (sum(u[:rho]) - 1.0) / rho if rho > 0 else 0.0
    return [max(v - theta, 0.0) for v in w]
