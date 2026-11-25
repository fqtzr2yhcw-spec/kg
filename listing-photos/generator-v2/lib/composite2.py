import json, sys, os, numpy as np, cv2
sys.path.insert(0, os.path.dirname(__file__))
from fitlib import project, cam_basis
"""usage: composite2.py prod.json render.png render.json out.png [rscale]"""
prod = json.load(open(sys.argv[1])); render_png, render_json, out_png = sys.argv[2:5]
SCALE = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
fitr = json.load(open(prod['fit'])); cam = fitr['cam']; T = fitr['T']
photo = cv2.imread(prod['photo']); PH, PW = photo.shape[:2]
mask = cv2.imread(prod['mask'], 0)
shadow = cv2.imread(prod['shadow'], 0).astype(np.float32) / 255 if prod.get('shadow') else np.zeros((PH, PW), np.float32)
R = json.load(open(render_json))
P3 = np.array([g['p'] for g in R['grid']], float); dst = np.array([g['s'] for g in R['grid']], float) * SCALE
src, _ = project(P3, T, cam)
Hm, _ = cv2.findHomography(src, dst, 0)
# soft alpha + colour decontamination
alpha = cv2.GaussianBlur(mask.astype(np.float32) / 255, (0, 0), prod.get('feather', 0.8))
alpha = np.clip((alpha - 0.15) / 0.85, 0, 1)
inner = cv2.erode(mask, np.ones((3, 3), np.uint8))
dec = cv2.inpaint(photo, 255 - inner, 4, cv2.INPAINT_TELEA); dec[inner > 0] = photo[inner > 0]
if prod.get('denoise', 0) > 0: dec = cv2.fastNlMeansDenoisingColored(dec, None, prod['denoise'], prod['denoise'], 5, 11)
lf = dec.astype(np.float32) / 255
lf = np.clip((lf - 0.5) * prod.get('contrast', 1.06) + 0.5 + prod.get('lift', 0.0), 0, 1)
dec = (lf * 255).astype(np.uint8)
rend = cv2.imread(render_png, cv2.IMREAD_UNCHANGED); RH, RW = rend.shape[:2]
flags = cv2.INTER_LANCZOS4 if abs(np.linalg.det(Hm[:2, :2])) > 1 else cv2.INTER_AREA
wl = cv2.warpPerspective(dec, Hm, (RW, RH), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)
wa = cv2.warpPerspective(alpha, Hm, (RW, RH), flags=cv2.INTER_LINEAR)
ws = cv2.warpPerspective(shadow, Hm, (RW, RH), flags=cv2.INTER_LINEAR)
sc = np.sqrt(abs(np.linalg.det(Hm[:2, :2])))
if sc > 1.05:
    blur = cv2.GaussianBlur(wl, (0, 0), 1.2 * sc); wl = cv2.addWeighted(wl, 1.3, blur, -0.3, 0)
# depth of field on render
dpath = render_png.replace('r_', 'd_')
dof = prod.get('dof')
if dof and os.path.exists(dpath):
    dimg = cv2.imread(dpath, cv2.IMREAD_UNCHANGED).astype(np.float32)
    rc = json.load(open(prod['rcfg'])); dd = rc['cam']['d']; KS = rc['car'].get('scale', 1)
    DN, DF = dd - 14 * KS, dd + 14 * KS
    depth = ((dimg[..., 2] * 256 + dimg[..., 1]) / 65535.0) * (DF - DN) + DN
    valid = dimg[..., 3] > 0
    C, fw, _, _ = cam_basis(rc['cam']['T'], rc['cam']['az'], rc['cam']['el'], dd)
    zof = lambda p: float((np.array(p) - C) @ fw)
    zf = zof(dof['focus']); zb = zof(dof['pt']); K = dof['px'] / (abs(zb - zf) / zb)
    sig = np.where(valid, K * np.abs(depth - zf) / np.maximum(depth, 1e-3), 0).astype(np.float32)
    w = valid.astype(np.float32); sb = cv2.GaussianBlur(sig * w, (0, 0), 25); wb = cv2.GaussianBlur(w, (0, 0), 25)
    sig = np.clip(np.where(valid, sig, sb / np.maximum(wb, 1e-4)), 0, dof.get('max', 9))
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
rgb = rend[..., :3].astype(np.float32); ra = rend[..., 3:4].astype(np.float32) / 255
rgb *= (1 - prod.get('shadow_k', 0.8) * ws[..., None])
a3 = wa[..., None]
out_rgb = rgb * (1 - a3) + wl.astype(np.float32) * a3
out = np.dstack([np.clip(out_rgb, 0, 255), np.maximum(ra, a3) * 255]).astype(np.uint8)
cv2.imwrite(out_png, out)
print('scale %.3f' % sc, 'load bbox', cv2.boundingRect((wa > 0.5).astype(np.uint8)))
