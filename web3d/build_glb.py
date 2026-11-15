# -*- coding: utf-8 -*-
"""SW 提取的逐件 STL+装配矩阵 -> 两个带颜色 GLB (full / sensors)"""
import json, os
import numpy as np
import trimesh


ROOT = r"C:\Users\21508\Desktop\Go2_SW_Project\.web3d"
parts = json.load(open(os.path.join(ROOT, "parts.json"), encoding="utf-8"))
_seen, _u = set(), []
for p in parts:
    if p["name"] in _seen:
        continue
    _seen.add(p["name"]); _u.append(p)
parts = _u
print("unique parts:", len(parts))

def color_of(n):
    if any(k in n for k in ["足端", "大腿", "小腿", "髋关节"]):
        return (0.30, 0.30, 0.33, 1.0)
    if "圆弧中间连接件" in n: return (0.91, 0.62, 0.20, 1.0)
    if "相机支架" in n:      return (0.16, 0.44, 0.72, 1.0)
    if "雷达延长板" in n:    return (0.82, 0.33, 0.26, 1.0)
    if "雷达转接件" in n:    return (0.52, 0.40, 0.76, 1.0)
    if "雷达支撑件" in n:    return (0.58, 0.58, 0.60, 1.0)
    if "保护主壳" in n:      return (0.13, 0.15, 0.17, 1.0)
    if "前保护框" in n:      return (0.22, 0.24, 0.27, 1.0)
    if "D435i" in n:         return (0.10, 0.11, 0.13, 1.0)
    return (0.75, 0.75, 0.78, 1.0)

def target_faces(name):
    if any(k in name for k in ["圆弧中间", "支架", "延长板", "转接", "保护", "D435i"]):
        return 60000
    return 15000

def cluster_decimate(v, f, target):
    span = v.max(0) - v.min(0)
    step = (float(np.prod(np.maximum(span, 1e-6))) / max(target, 1)) ** (1.0 / 3.0) * 0.9
    nf = f
    for _ in range(24):
        key = np.floor((v - v.min(0)) / step).astype(np.int64)
        _, inv = np.unique(key, axis=0, return_inverse=True)
        nf = inv[f].reshape(-1, 3)
        keep = (nf[:, 0] != nf[:, 1]) & (nf[:, 1] != nf[:, 2]) & (nf[:, 0] != nf[:, 2])
        nf = nf[keep]
        if len(nf) <= target * 1.15 or step > span.max() * 4:
            break
        step *= 1.22
    nv = len(inv)
    acc = np.zeros((nv, 3)); cnt = np.zeros(nv)
    np.add.at(acc, inv, v); np.add.at(cnt, inv, 1.0)
    acc[cnt > 0] /= cnt[cnt > 0, None]
    used = np.unique(nf)
    remap = -np.ones(nv, dtype=np.int64); remap[used] = np.arange(len(used))
    return acc[used], remap[nf]

cache = {}
def load_decimated(stl_name, name):
    key = stl_name
    if key in cache:
        return cache[key]
    me = trimesh.load(os.path.join(ROOT, "meshes", stl_name), process=False)
    if isinstance(me, trimesh.Scene):
        me = trimesh.util.concatenate(tuple(me.geometry.values()))
    v = np.asarray(me.vertices, dtype=np.float64)
    f = np.asarray(me.faces, dtype=np.int64)
    n0 = len(f)
    if n0 > 300000:
        v, f = cluster_decimate(v, f, 150000)
    elif n0 > 150000:
        v, f = cluster_decimate(v, f, 90000)
    mesh = trimesh.Trimesh(vertices=v / 1000.0, faces=f, process=True)  # mm->m, merge verts+normals
    r, g, b, al = color_of(name)
    mat = trimesh.visual.material.PBRMaterial(baseColorFactor=[int(r*255), int(g*255), int(b*255), 255],
                      metallicFactor=0.15, roughnessFactor=0.55)
    mesh.visual.material = mat
    cache[key] = mesh
    print("%-30s %7d -> %6d faces" % (name, n0, len(f)))
    return mesh

def to_mat16(m):
    a = np.array(m, dtype=float)
    axes = a[0:9].reshape(3, 3)
    t = a[9:12]
    M = np.eye(4); M[:3, :3] = axes.T; M[:3, 3] = t
    return M

def build(filt, out_path):
    scene = trimesh.Scene()
    tot = 0
    for p in parts:
        if not filt(p["name"]):
            continue
        mesh = load_decimated(os.path.basename(p["stl"]), p["name"])
        M = to_mat16(p["m"])
        scene.add_geometry(mesh, node_name=p["name"].replace("/", "_"), transform=M,
                           geom_name=os.path.basename(p["stl"]))
        tot += 1
    glb = scene.export(file_type="glb")
    with open(out_path, "wb") as fh:
        fh.write(glb)
    print("%s: %d parts, %.1f MB" % (out_path, tot, len(glb) / 1e6))

SENSOR_KEYS = ["圆弧中间", "支架", "延长板", "转接", "雷达支撑", "保护", "D435i"]
build(lambda n: True, os.path.join(ROOT, "go2_full.glb"))
build(lambda n: any(k in n for k in SENSOR_KEYS), os.path.join(ROOT, "go2_sensors.glb"))
print("DONE")