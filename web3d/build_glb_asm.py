# -*- coding: utf-8 -*-
"""用 SW 装配坐标导出的组件 STL 构建彩色 GLB。

数据来源: .web3d/asm_stl/*.STL  —— 由 .web3d/AsmExport.cs 通过
SolidWorks 直接对总装 SaveAs STL 生成，每个组件一份，几何已在装配坐标系中，
因此不需要任何 MathTransform，彻底避免"零件原点 vs 网格坐标"错位。

单位: STL 为毫米 -> GLB 为米; 坐标系: SW Z-up -> glTF Y-up: (x,y,z)->(x,z,-y)
"""
import os
import re
import glob
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", ".web3d", "asm_stl")
OUT_FULL = os.path.join(HERE, "assets", "go2_full.glb")
OUT_SENS = os.path.join(HERE, "assets", "go2_sensors.glb")

# 配色 (r, g, b) 0-1
PALETTE = [
    ("D435i",              (0.14, 0.15, 0.17)),
    ("相机保护主壳",         (0.10, 0.10, 0.11)),
    ("相机前保护框",         (0.20, 0.21, 0.23)),
    ("相机支架与后盖一体件",   (0.16, 0.44, 0.72)),
    ("圆弧中间连接件",       (0.91, 0.62, 0.20)),
    ("雷达延长板",           (0.80, 0.24, 0.22)),
    ("雷达转接件",           (0.55, 0.38, 0.72)),
    ("雷达支撑件",           (0.62, 0.64, 0.66)),
    ("髋关节",              (0.74, 0.75, 0.77)),
    ("大腿",                (0.80, 0.81, 0.83)),
    ("小腿",                (0.80, 0.81, 0.83)),
    ("足端",                (0.55, 0.56, 0.58)),
]
SENSOR_KEYS = ("圆弧中间", "支架", "延长板", "转接", "雷达支撑", "保护", "D435i")
SKIP_KEYS = ("扫掠曲面", "包络")     # 运动包络参考件不放进展示模型


def color_of(name):
    for key, rgb in PALETTE:
        if key in name:
            return rgb
    return (0.75, 0.76, 0.78)


def _cluster_at(v, f, step):
    """按给定体素边长聚类，返回 (顶点, 面, 面数)."""
    key = np.floor((v - v.min(0)) / step).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    nf = inv[f].reshape(-1, 3)
    keep = (nf[:, 0] != nf[:, 1]) & (nf[:, 1] != nf[:, 2]) & (nf[:, 0] != nf[:, 2])
    nf = nf[keep]
    return inv, nf


def cluster_decimate(v, f, target):
    """二分搜索最大的体素步长，使简化后面数仍 >= target。

    与"步长递增直到低于目标"相比，本做法不会把薄壁件（几十微米到 2mm 壁厚）
    一次性压塌 —— 它会在刚好保持目标面数的步长处停下。
    """
    span = v.max(0) - v.min(0)
    lo, hi = 1e-7, float(span.max())
    inv = nf = None
    for _ in range(18):
        mid = (lo * hi) ** 0.5
        inv, nf = _cluster_at(v, f, mid)
        if len(nf) >= target:
            lo = mid
        else:
            hi = mid
    inv, nf = _cluster_at(v, f, lo)
    nv = len(inv)
    acc = np.zeros((nv, 3))
    cnt = np.zeros(nv)
    np.add.at(acc, inv, v)
    np.add.at(cnt, inv, 1.0)
    acc[cnt > 0] /= cnt[cnt > 0, None]
    used = np.unique(nf)
    remap = -np.ones(nv, dtype=np.int64)
    remap[used] = np.arange(len(used))
    return acc[used], remap[nf]


def load_instances():
    """返回 [(instance_name, vertices_m, faces)]，几何已在装配坐标系."""
    out = []
    for path in sorted(glob.glob(os.path.join(SRC, "*.STL"))):
        base = os.path.basename(path)
        name = re.sub(r"^ASM\s*-\s*", "", base)
        name = re.sub(r"\.STL$", "", name, flags=re.I).strip()
        if any(k in name for k in SKIP_KEYS):
            print("skip  %-40s (运动包络参考件)" % name[:40])
            continue
        mesh = trimesh.load(path, process=False)
        v = np.asarray(mesh.vertices, dtype=np.float64) / 1000.0
        f = np.asarray(mesh.faces, dtype=np.int64)
        n0 = len(f)
        if any(k in name for k in ("髋关节", "大腿")):
            tgt = 6000
        elif "D435i" in name:
            tgt = 15000
        elif any(k in name for k in ("圆弧中间", "雷达转接件")):
            tgt = 20000
        elif any(k in name for k in ("支架", "延长板", "前保护框")):
            tgt = 12000
        elif any(k in name for k in ("雷达支撑件", "保护主壳")):
            tgt = 9000
        else:
            tgt = 20000
        if n0 > tgt:
            v, f = cluster_decimate(v, f, tgt)
        print("%-40s %8d -> %7d faces" % (name[:40], n0, len(f)))
        out.append((name, v, f))
    return out


def build(instances, keep, out_path):
    scene = trimesh.Scene()
    tris = []
    for name, v, f in instances:
        if not keep(name):
            continue
        mat = trimesh.visual.material.PBRMaterial(
            baseColorFactor=[*color_of(name), 255],
            metallicFactor=0.15, roughnessFactor=0.55)
        mesh = trimesh.Trimesh(vertices=v, faces=f, process=False)
        mesh.visual.material = mat
        scene.add_geometry(mesh, node_name=name.replace("/", "_"),
                           geom_name=name.replace("/", "_"), transform=np.eye(4))
        tris.append(len(f))
    # Z-up -> Y-up, 然后整体居中
    scene.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]))
    lo, hi = scene.bounds
    center = (lo + hi) / 2.0
    scene.apply_transform(trimesh.transformations.translation_matrix(-center))
    glb = scene.export(file_type="glb")
    with open(out_path, "wb") as fh:
        fh.write(glb)
    lo2, hi2 = trimesh.load(out_path).bounds
    print("%s: %d parts, %d faces, %.1f MB, size=(%.2f, %.2f, %.2f) m"
          % (os.path.basename(out_path), len(tris), sum(tris), len(glb) / 1e6,
             hi2[0] - lo2[0], hi2[1] - lo2[1], hi2[2] - lo2[2]))


def main():
    inst = load_instances()
    print("unique instances: %d" % len(inst))
    build(inst, lambda n: True, OUT_FULL)
    build(inst, lambda n: any(k in n for k in SENSOR_KEYS), OUT_SENS)
    print("DONE")


if __name__ == "__main__":
    main()
