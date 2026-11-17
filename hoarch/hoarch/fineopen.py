"""Fine openings in window and door parts: per object, the most openings narrower than
WMIN mm on any 0.2 mm layer up to ZTOP (holes a 0.4 nozzle closes up, the way the
Oakhurst's first door lattice printed as a blur).

usage: python3 -m hoarch.fineopen <plate.3mf>...
       python3 -m hoarch.fineopen --building <key>...   (window, door and add-in plates)"""
import json, os, re, sys, zipfile
import numpy as np
import manifold3d as m3

WMIN, ZTOP = 1.5, 3.0          # glazing openings are 1.6 mm or more (NOTES.md); 1.5 allows for the slicing
JT = m3.JoinType.Round
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")


def objects(path):
    xml = zipfile.ZipFile(path).read("3D/3dmodel.model").decode()
    for oid, attrs, body in re.findall(r'<object id="(\d+)"([^>]*)>(.*?)</object>', xml, re.S):
        V = np.array(re.findall(r'<vertex x="([-\d.e]+)" y="([-\d.e]+)" z="([-\d.e]+)"', body), dtype=np.float32)
        T = np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', body), dtype=np.uint32)
        if len(V):
            nm = re.search(r'name="([^"]*)"', attrs)
            yield (nm.group(1) if nm else oid), m3.Manifold(m3.Mesh(vert_properties=V, tri_verts=T))


def fine(man):
    best = (0, 0.0)
    top = min(ZTOP, man.bounding_box()[5])
    for z in np.arange(0.1, top, 0.2):
        cs = man.slice(float(z))
        if cs.area() <= 0:
            continue
        holes = cs.offset(3.0, JT).offset(-3.0, JT) - cs
        n = 0
        for c in holes.decompose():
            if c.area() > 0.05 and c.offset(-WMIN / 2, JT).area() < 1e-6:
                n += 1
        if n > best[0]:
            best = (n, round(float(z), 1))
    return best


def run(paths, label=""):
    for p in paths:
        seen = set()
        for name, man in objects(p):
            if name in seen:
                continue
            seen.add(name)
            n, z = fine(man)
            if n >= 6:
                print(f"{label:11s} {name:44s} {n:4d} fine openings (layer {z})")
                sys.stdout.flush()


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--building":
        for b in a[1:]:
            kd = os.path.join(OUT, b, "kit") + "/"
            pl = [kd + p_["file"] for p_ in json.load(open(kd + "manifest.json"))["plates"]]
            run([q for q in pl if "Windows" in q or "Addins" in q or "Door" in q], b)
    else:
        run(a)
