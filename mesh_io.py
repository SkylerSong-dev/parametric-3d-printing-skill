"""Pure trimesh mesh loading and print-orientation analysis.

Kept separate from preview.py so consumers that only need mesh loading
(stl_to_3mf.py, run_cadquery_model.py's --strict watertight check) don't
pay the pyrender + PyOpenGL import cost. Only depends on trimesh + numpy.
"""
import numpy as np
import trimesh


def load_mesh(path):
    """Load an STL file via trimesh.

    Raises ValueError if the file cannot be parsed, contains no geometry,
    has zero faces, or has non-finite vertex coordinates. Callers handle
    the failure in-process instead of being killed by sys.exit, and silent
    garbage (zero-face or NaN meshes) is stopped before it reaches pyrender.
    """
    try:
        tm = trimesh.load(path, force="mesh")
    except Exception as e:
        raise ValueError(f"Failed to load STL: {e}") from e
    if not hasattr(tm, "vertices") or len(tm.vertices) == 0:
        raise ValueError("STL file contains no vertices")
    if not hasattr(tm, "faces") or len(tm.faces) == 0:
        raise ValueError("STL file contains no triangles")
    if not np.isfinite(tm.vertices).all():
        raise ValueError("STL file has non-finite vertex coordinates (NaN or inf)")
    # OCC's tessellator emits zero-area triangles at the poles of
    # spherical faces (and similar degenerate spots). They carry no
    # surface, but their zero-length open edges make an otherwise
    # closed mesh read as non-watertight. Drop them before any checks.
    tm.update_faces(tm.nondegenerate_faces())
    tm.merge_vertices()
    return tm


def _component_count(tm):
    """Return connected shell count without making it a hard dependency."""
    try:
        return int(tm.body_count)
    except Exception:
        try:
            return len(tm.split(only_watertight=False))
        except Exception:
            return None


def analyze_mesh(tm, overhang_angle_deg=45.0, bed_tolerance_mm=0.05):
    """Return geometry and print-orientation metrics for a mesh.

    ``overhang_angle_deg`` is measured from straight down: 0 degrees is a
    horizontal downward ceiling, 45 degrees is a typical profile-dependent
    boundary, and 90 degrees is a vertical wall. Downward faces whose vertices
    all lie at the minimum Z plane are bed contact and are excluded.

    Unsupported percentages are weighted by triangle area rather than triangle
    count. They are a screening metric, not a substitute for slicing.
    """
    if not 0.0 <= overhang_angle_deg <= 90.0:
        raise ValueError("overhang_angle_deg must be between 0 and 90")
    if bed_tolerance_mm < 0.0:
        raise ValueError("bed_tolerance_mm must be >= 0")

    normals = np.asarray(tm.face_normals)
    areas = np.asarray(tm.area_faces)
    triangles = np.asarray(tm.triangles)
    z_min = float(tm.bounds[0, 2])

    downward = normals[:, 2] < -1e-9
    angle_from_down = np.degrees(
        np.arccos(np.clip(-normals[:, 2], -1.0, 1.0))
    )
    face_max_z = triangles[:, :, 2].max(axis=1)
    bed_contact = downward & (face_max_z <= z_min + bed_tolerance_mm)
    unsupported = (
        downward
        & ~bed_contact
        & (angle_from_down < float(overhang_angle_deg))
    )

    total_area = float(areas.sum())
    unsupported_area = float(areas[unsupported].sum())
    bed_contact_area = float(areas[bed_contact].sum())
    unsupported_pct = (
        unsupported_area / total_area * 100.0 if total_area > 0.0 else 0.0
    )
    signed_volume = float(tm.volume)

    return {
        "vertices": int(len(tm.vertices)),
        "faces": int(len(tm.faces)),
        "extents_mm": [float(value) for value in tm.extents],
        "signed_volume_mm3": signed_volume,
        "surface_area_mm2": total_area,
        "watertight": bool(tm.is_watertight),
        "winding_consistent": bool(tm.is_winding_consistent),
        "is_volume": bool(tm.is_volume),
        "components": _component_count(tm),
        "bed_contact_area_mm2": bed_contact_area,
        "unsupported_downward_area_mm2": unsupported_area,
        "unsupported_downward_area_pct": unsupported_pct,
        "overhang_angle_from_down_deg": float(overhang_angle_deg),
        "bed_tolerance_mm": float(bed_tolerance_mm),
    }
