import numpy as np, cv2
from fitlib import project

def hull_mask(shape, parts, T, cam, dil=0):
    H, W = shape[:2]; m = np.zeros((H, W), np.uint8)
    for P in parts:
        uv, _ = project(np.asarray(P, float), T, cam)
        cv2.fillPoly(m, [cv2.convexHull(uv.astype(np.float32)).astype(np.int32)], 255)
    if dil > 0: m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * dil + 1, 2 * dil + 1)))
    if dil < 0: m = cv2.erode(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (-2 * dil + 1, -2 * dil + 1)))
    return m

def box_pts(x0, x1, y0, y1, z0, z1):
    return [[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]

def cyl_pts(c, r, h, axis='y', n=72):
    out = []
    for t in np.linspace(0, 2 * np.pi, n, endpoint=False):
        a, b = r * np.cos(t), r * np.sin(t)
        for k in (0, h):
            if axis == 'y': out.append([c[0] + a, c[1] + k, c[2] + b])
            elif axis == 'x': out.append([c[0] + k, c[1] + a, c[2] + b])
            else: out.append([c[0] + a, c[1] + b, c[2] + k])
    return out

def grabcut(img, fg_sure, prob_fg, bg_sure=None, iters=8):
    mask = np.full(img.shape[:2], cv2.GC_BGD, np.uint8)
    mask[prob_fg > 0] = cv2.GC_PR_FGD
    mask[fg_sure > 0] = cv2.GC_FGD
    if bg_sure is not None: mask[bg_sure > 0] = cv2.GC_BGD
    b = np.zeros((1, 65)); f = np.zeros((1, 65))
    cv2.grabCut(img, mask, None, b, f, iters, cv2.GC_INIT_WITH_MASK)
    return np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)

def keep_big(m, min_area=200, fill_holes=400):
    n, lbl, st, _ = cv2.connectedComponentsWithStats(m); k = np.zeros_like(m)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] >= min_area: k[lbl == i] = 255
    if fill_holes:
        inv = 255 - k; n, lbl, st, _ = cv2.connectedComponentsWithStats(inv)
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] < fill_holes: k[lbl == i] = 255
    return k

def photo_shadow(img, objmask, near_px=60, fade_px=45, hole_dil=41, scale=4):
    """luminance ratio of pixels vs. inpainted clean background, near the object."""
    H, W = img.shape[:2]
    Lr = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)[..., 0].astype(np.float32)
    small = cv2.resize(Lr, (W // scale, H // scale), interpolation=cv2.INTER_AREA)
    hole = cv2.resize(cv2.dilate(objmask, np.ones((hole_dil, hole_dil), np.uint8)), (W // scale, H // scale), interpolation=cv2.INTER_NEAREST)
    est = cv2.inpaint(np.clip(small, 0, 255).astype(np.uint8), hole, 12, cv2.INPAINT_TELEA).astype(np.float32)
    est = cv2.GaussianBlur(cv2.resize(est, (W, H), interpolation=cv2.INTER_CUBIC), (0, 0), 6)
    sh = np.clip(1.0 - Lr / np.maximum(est, 1), 0, 1)
    dist = cv2.distanceTransform(255 - objmask, cv2.DIST_L2, 5)
    sh *= np.clip(1 - dist / float(fade_px), 0, 1)
    sh[objmask > 0] = 0
    return cv2.GaussianBlur(sh, (0, 0), 1.5)

def viz(img, m, col=(255, 0, 255)):
    v = img.copy(); v[m == 0] = (v[m == 0] * 0.3 + np.array(col) * 0.7).astype(np.uint8); return v
