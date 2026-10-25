"""Find material that starts in the air. For each plate object and each 0.2 mm layer, it
takes the part of the layer with nothing under it (beyond a 0.6 mm overhang allowance). It
reports thin strands (narrower than 0.9 mm, the kind that print as loose lines), their layer
heights and how far they reach from support. A reach of about 1 mm is a ledge and prints.
A long reach on a thin strip is a fault: the Oakhurst's pediment fan and the Arroyo's
slotted porch walls.

usage: python3 -m hoarch.airstrands [--only name,...] <plate.3mf>...
       python3 -m hoarch.airstrands --building <key>...   (window and add-in plates skipped)"""
import json, os, re, sys, zipfile
import numpy as np
import manifold3d as m3

LH, OVER, MINW = 0.2, 0.6, 0.9
JT = m3.JoinType.Square
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")


def objects(path):
    zf = zipfile.ZipFile(path)
    xml = zf.read([n for n in zf.namelist() if n.endswith(".model")][0]).decode()
    for oid, attrs, body in re.findall(r'<object id="(\d+)"([^>]*)>(.*?)</object>', xml, re.S):
        V = np.array(re.findall(r'<vertex x="([-\d.e]+)" y="([-\d.e]+)" z="([-\d.e]+)"', body), dtype=np.float32)
        T = np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', body), dtype=np.uint32)
        if not len(V):
            continue
        nm = re.search(r'name="([^"]*)"', attrs)
        yield (nm.group(1) if nm else oid), m3.Manifold(m3.Mesh(vert_properties=V, tri_verts=T))


def scan(man, top):
    hits = []
    below = None
    for k in range(int(top / LH) + 1):
        z = (k + 0.5) * LH
        cur = man.slice(z)
        if below is not None and cur.area() > 0:
            un = cur - below.offset(OVER, JT)
            un = un.offset(-0.15, JT).offset(0.15, JT)          # drop overhang slivers under 0.3 mm
            if un.area() > 0.5:
                for c in un.decompose():
                    a = c.area()
                    if a < 0.5:
                        continue
                    thin = c - c.offset(-MINW / 2, JT).offset(MINW / 2, JT)
                    ta = thin.area()
                    if ta > 1.0:
                        bb = c.bounds()
                        reach = OVER
                        for d in (1.0, 1.5, 2.0, 3.0, 5.0, 8.0):
                            if (c - below.offset(d, JT)).area() > 0.05:
                                reach = d
                        hits.append((round(z, 2), round(a, 1), round(ta, 1), [round(v, 1) for v in bb], reach))
        below = cur
    return hits


ONLY = None


def run(paths):
    for p in paths:
        for name, man in objects(p):
            if ONLY and name not in ONLY:
                continue
            bb = man.bounding_box()
            hits = scan(man, bb[5])
            if hits and (max(h[2] for h in hits) >= 4.0 or sum(h[2] for h in hits) >= 20.0):
                tot = sum(h[2] for h in hits)
                print(f"{p.split('/')[-1]:40s} {name:40s} thin-in-air {tot:7.1f} mm2 over {len(hits)} layer-spots; "
                      f"reach {max(h[4] for h in hits)} worst {max(hits, key=lambda h: h[2])}")
            sys.stdout.flush()


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--only":
        ONLY = set(a[1].split(","))
        a = a[2:]
    if a and a[0] == "--building":
        for b in a[1:]:
            kd = os.path.join(OUT, b, "kit") + "/"
            pl = [kd + p_["file"] for p_ in json.load(open(kd + "manifest.json"))["plates"]]
            run([q for q in pl if "Windows" not in q and "Addins" not in q])     # frames print on supports
    else:
        run(a)
