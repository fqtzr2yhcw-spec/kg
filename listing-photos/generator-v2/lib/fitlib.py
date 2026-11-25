import numpy as np, json
from scipy.optimize import least_squares

def cam_basis(T, az, el, d):
    T = np.asarray(T, float)
    C = T + d * np.array([np.cos(el) * np.cos(az), np.sin(el), np.cos(el) * np.sin(az)])
    fw = (T - C) / np.linalg.norm(T - C); up = np.array([0, 1, 0.])
    rt = np.cross(fw, up); rt /= np.linalg.norm(rt); u2 = np.cross(rt, fw)
    return C, fw, rt, u2

def project(P, T, cam):
    az, el, d, roll, s, tx, ty = cam
    C, fw, rt, u2 = cam_basis(T, az, el, d)
    V = np.atleast_2d(P) - C; xc = V @ rt; yc = V @ u2; zc = V @ fw
    u = xc / zc; w = -yc / zc
    cr, sr = np.cos(roll), np.sin(roll)
    return np.stack([s * (cr * u - sr * w) + tx, s * (sr * u + cr * w) + ty], 1), zc

def fit(model, obs, dims0, dbounds, az_grid, el_grid, d_grid, img_wh, weights=None, extra=None):
    """model(dims) -> (P3 [N,3], T). obs [N,2]. returns dict."""
    obs = np.asarray(obs, float); N = len(obs); w = np.ones(N) if weights is None else np.asarray(weights, float)
    nd = len(dims0); W_, H_ = img_wh
    def resid(p):
        dims = p[:nd]; cam = p[nd:]
        P, T = model(dims)
        uv, zc = project(P, T, cam)
        r = ((uv - obs) * w[:, None]).ravel()
        if np.any(zc <= 0): r = r + 1e4
        if extra is not None: r = np.concatenate([r, extra(dims, cam)])
        return r
    best = None
    lo = list(dbounds[0]) + [-10, 0.02, 1.0, -1, 50, -5 * W_, -5 * H_]
    hi = list(dbounds[1]) + [10, 1.56, 500, 1, 50000, 6 * W_, 6 * H_]
    for az0 in az_grid:
        for el0 in el_grid:
            for d0 in d_grid:
                p0 = list(dims0) + [az0, el0, d0, 0, max(W_, H_), W_ / 2, H_ / 2]
                try:
                    r = least_squares(resid, p0, bounds=(lo, hi), max_nfev=4000)
                except Exception:
                    continue
                if best is None or r.cost < best.cost: best = r
    p = best.x; dims = p[:nd]; cam = p[nd:]
    P, T = model(dims); uv, _ = project(P, T, cam)
    rms = float(np.sqrt(np.mean(np.sum((uv - obs) ** 2, 1))))
    return {'dims': dims.tolist(), 'cam': cam.tolist(), 'T': list(map(float, T)), 'rms': rms, 'uv': uv.tolist()}
