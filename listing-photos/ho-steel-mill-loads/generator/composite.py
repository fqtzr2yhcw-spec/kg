import json, sys, numpy as np, cv2

import os
SCALE = float(os.environ.get('RSCALE','1.0'))
render_png = sys.argv[1] if len(sys.argv) > 1 else 'r_full_2k.png'
render_json = sys.argv[2] if len(sys.argv) > 2 else 'r_full.json'
out_png = sys.argv[3] if len(sys.argv) > 3 else 'hero.png'
NUDGE = (float(sys.argv[4]), float(sys.argv[5])) if len(sys.argv) > 5 else (0.0, 0.0)

p = json.load(open('fit.json'))['p']
Lg, Hh, ff, g = p[:4]
cam = list(p[4:11]) + [Lg / 2, -(2 + g) / 2]


def project(P, cam):
    az, el, d, roll, s, tx, ty, cx, cz = cam
    T = np.array([cx, 0.5, cz])
    C = T + d * np.array([np.cos(el) * np.cos(az), np.sin(el), np.cos(el) * np.sin(az)])
    fw = (T - C) / np.linalg.norm(T - C); up = np.array([0, 1, 0.])
    rt = np.cross(fw, up); rt /= np.linalg.norm(rt); u2 = np.cross(rt, fw)
    V = P - C; xc = V @ rt; yc = V @ u2; zc = V @ fw
    u = xc / zc; w = -yc / zc
    cr, sr = np.cos(roll), np.sin(roll)
    return np.stack([s * (cr * u - sr * w) + tx, s * (sr * u + cr * w) + ty], 1)


photo = cv2.imread('p1.png'); PH, PW = photo.shape[:2]
mask2 = cv2.imread('mask2.png', 0)
R = json.load(open(render_json))

# ---- homography photo -> render (same camera centre => exact homography) ----
P3 = np.array([gp['p'] for gp in R['grid']], float)
dst = np.array([gp['s'] for gp in R['grid']], float) * SCALE
src = project(P3, cam)
Hm, _ = cv2.findHomography(src, dst, 0)
Hm = np.array([[1, 0, NUDGE[0]], [0, 1, NUDGE[1]], [0, 0, 1]]) @ Hm


# ---- silhouettes in photo space ----
def box_sil(y0, y1, dil):
    m = np.zeros((PH, PW), np.uint8)
    for z0, z1 in [(0, -1), (-1 - g, -2 - g)]:
        corners = np.array([[x, y, z] for x in (0, Lg) for y in (y0, y1) for z in (z0, z1)], float)
        uv = project(corners, cam).astype(np.float32)
        hull = cv2.convexHull(uv).astype(np.int32)
        cv2.fillPoly(m, [hull], 255)
    if dil: m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * dil + 1, 2 * dil + 1)))
    return m

body = box_sil(ff, ff + Hh, 9)
withfeet = box_sil(ff - 0.16, ff + Hh, 9)
band = cv2.subtract(withfeet, body)

lab = cv2.cvtColor(cv2.medianBlur(photo, 5), cv2.COLOR_BGR2LAB).astype(np.float32)
L = lab[..., 0]; A = lab[..., 1] - 128; B = lab[..., 2] - 128
SIL = json.load(open('sil.json'))
SS = 4
big = np.zeros((PH * SS, PW * SS), np.uint8)
polyL = np.array(SIL['L']['verts'])
fR = SIL['R']['fit']; polyR = np.array(SIL['R']['verts'] + [fR['fbn'], fR['bbn']])
for poly in (polyL, polyR):
    cv2.fillPoly(big, [np.round(poly * SS).astype(np.int32)], 255, lineType=cv2.LINE_AA, shift=0)
body_soft = cv2.resize(big, (PW, PH), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
body_hard = (body_soft > 0.5).astype(np.uint8) * 255
# feet: dark, non-yellow pixels from the grabcut mask, just below the body
feetzone = cv2.subtract(cv2.dilate(withfeet, np.ones((5, 5), np.uint8)), cv2.erode(body_hard, np.ones((3, 3), np.uint8)))
yellowish = ((B - 1.6 * A) > 4.5) | (L > 140)
feet = ((mask2 > 0) & (feetzone > 0) & (~yellowish)).astype(np.uint8) * 255
feet = cv2.morphologyEx(feet, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
n, lbl, st, _ = cv2.connectedComponentsWithStats(feet)
fk = np.zeros_like(feet)
for i in range(1, n):
    if st[i, cv2.CC_STAT_AREA] > 25: fk[lbl == i] = 255
feet = fk
feet_soft = cv2.GaussianBlur(feet.astype(np.float32) / 255, (0, 0), 0.7)
alpha_soft = np.maximum(body_soft, feet_soft * (1 - body_soft))
alpha = (alpha_soft > 0.5).astype(np.uint8) * 255
cv2.imwrite('alpha_final.png', alpha)

# ---- photo contact shadow (luminance ratio vs. estimated clean board) ----
near = cv2.dilate(withfeet, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (91, 91)))
Lraw = cv2.cvtColor(photo, cv2.COLOR_BGR2LAB)[..., 0].astype(np.float32)
small = cv2.resize(Lraw, (PW // 4, PH // 4), interpolation=cv2.INTER_AREA)
hole = cv2.resize(cv2.dilate(withfeet, np.ones((61, 61), np.uint8)), (PW // 4, PH // 4), interpolation=cv2.INTER_NEAREST)
est = cv2.inpaint(np.clip(small, 0, 255).astype(np.uint8), hole, 12, cv2.INPAINT_TELEA).astype(np.float32)
est = cv2.GaussianBlur(cv2.resize(est, (PW, PH), interpolation=cv2.INTER_CUBIC), (0, 0), 6)
shadow = np.clip(1.0 - Lraw / np.maximum(est, 1), 0, 1)
shadow[near == 0] = 0
shadow[alpha > 0] = np.maximum(shadow[alpha > 0], 0.0)
# only keep shadow that hugs the load base: fade with distance from load silhouette
dist = cv2.distanceTransform(255 - withfeet, cv2.DIST_L2, 5)
shadow *= np.clip(1 - dist / 45.0, 0, 1)
shadow = cv2.GaussianBlur(shadow, (0, 0), 1.5)
cv2.imwrite('shadow_photo.png', (shadow * 255).astype(np.uint8))

# ---- colour decontamination: extend interior colours outward before feathering ----
inner = cv2.erode(alpha, np.ones((3, 3), np.uint8))
dec = cv2.inpaint(photo, 255 - inner, 4, cv2.INPAINT_TELEA)
dec[inner > 0] = photo[inner > 0]
a_f = np.clip((alpha_soft - 0.12) / 0.88, 0, 1)

# mild tone shaping on the load: a touch more contrast + crispness
dec = cv2.fastNlMeansDenoisingColored(dec, None, 1.5, 1.5, 5, 11)
lf = dec.astype(np.float32) / 255
lf = np.clip((lf - 0.5) * 1.08 + 0.5 + 0.01, 0, 1)
dec2 = (lf * 255).astype(np.uint8)

# ---- warp to render space ----
rend = cv2.imread(render_png, cv2.IMREAD_UNCHANGED)
RH, RW = rend.shape[:2]
wl = cv2.warpPerspective(dec2, Hm, (RW, RH), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)
wa = cv2.warpPerspective(a_f, Hm, (RW, RH), flags=cv2.INTER_LINEAR)
ws = cv2.warpPerspective(shadow, Hm, (RW, RH), flags=cv2.INTER_LINEAR)
# sharpen the upscaled load
blur = cv2.GaussianBlur(wl, (0, 0), 1.3)
wl = cv2.addWeighted(wl, 1.3, blur, -0.3, 0)

# ---- depth of field on the render, matched to the photo (sharp front of load, soft rear) ----
DOFK = float(os.environ.get('DOFK', '1.0'))
dpath = render_png.replace('r_', 'd_')
if DOFK > 0 and os.path.exists(dpath):
    dimg = cv2.imread(dpath, cv2.IMREAD_UNCHANGED).astype(np.float32)
    DN, DF = p[6] - 14, p[6] + 14
    depth = ((dimg[..., 2] * 256 + dimg[..., 1]) / 65535.0) * (DF - DN) + DN
    valid = dimg[..., 3] > 0
    T = np.array([Lg / 2, 0.5, -(2 + g) / 2]); az, el, dd = p[4], p[5], p[6]
    Cc = T + dd * np.array([np.cos(el) * np.cos(az), np.sin(el), np.cos(el) * np.sin(az)]); fw = (T - Cc) / np.linalg.norm(T - Cc)
    zof = lambda P: float((np.array(P) - Cc) @ fw)
    zf = zof([Lg * 0.8, Hh, -1.2]); zb = zof([0.0, Hh / 2, -1.2])
    K = 4.2 / (abs(zb - zf) / zb)
    sig = np.where(valid, K * np.abs(depth - zf) / np.maximum(depth, 1) * DOFK, 0).astype(np.float32)
    # extend sigma into empty background
    w = valid.astype(np.float32)
    sb = cv2.GaussianBlur(sig * w, (0, 0), 25); wb = cv2.GaussianBlur(w, (0, 0), 25)
    sig = np.where(valid, sig, sb / np.maximum(wb, 1e-4))
    sig = np.clip(sig, 0, 9)
    a0 = rend[..., 3:4].astype(np.float32) / 255
    prem = np.dstack([rend[..., :3].astype(np.float32) * a0, a0[..., 0] * 255])
    levels = [0, 1, 2, 3, 4.5, 6, 9]
    stack = [prem if l == 0 else cv2.GaussianBlur(prem, (0, 0), l) for l in levels]
    outp = np.zeros_like(prem)
    for i in range(len(levels) - 1):
        l0, l1 = levels[i], levels[i + 1]
        t = np.clip((sig - l0) / (l1 - l0), 0, 1)[..., None]
        sel = ((sig >= l0) & (sig < l1))[..., None] if i < len(levels) - 2 else (sig >= l0)[..., None]
        outp += sel * (stack[i] * (1 - t) + stack[i + 1] * t)
    aa = np.clip(outp[..., 3:4] / 255, 1e-4, 1)
    rend = np.dstack([np.clip(outp[..., :3] / aa, 0, 255), np.clip(outp[..., 3], 0, 255)]).astype(np.uint8)
    cv2.imwrite('sigma_map.png', np.clip(sig * 28, 0, 255).astype(np.uint8))
rgb = rend[..., :3].astype(np.float32); ra = rend[..., 3:4].astype(np.float32) / 255
# apply photo contact shadow onto whatever is rendered (deck)
k = 0.85
rgb *= (1 - k * ws[..., None])
# composite load
a3 = wa[..., None]
out_rgb = rgb * (1 - a3) + wl.astype(np.float32) * a3
out_a = np.maximum(ra, a3)
out = np.dstack([np.clip(out_rgb, 0, 255), out_a * 255]).astype(np.uint8)
cv2.imwrite(out_png, out)
print('H', Hm.round(3).tolist())
print('load bbox in render', cv2.boundingRect((wa > 0.5).astype(np.uint8)))
