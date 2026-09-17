import pytest
import mesh_io
import trimesh


def test_load_mesh_valid(tmp_stl):
    tm = mesh_io.load_mesh(str(tmp_stl))
    assert len(tm.vertices) > 0
    assert len(tm.faces) > 0
    assert tm.is_watertight


def test_load_mesh_missing_file(tmp_path):
    with pytest.raises(ValueError, match="Failed to load STL"):
        mesh_io.load_mesh(str(tmp_path / "nope.stl"))


def test_load_mesh_empty_file(tmp_path):
    empty = tmp_path / "empty.stl"
    empty.write_bytes(b"")
    with pytest.raises(ValueError):
        mesh_io.load_mesh(str(empty))


def test_load_mesh_no_pyrender_import():
    """mesh_io must not pull in pyrender (it's the whole point of the split)."""
    import sys
    assert "pyrender" not in dir(mesh_io), "mesh_io should not reference pyrender"


def test_box_overhang_excludes_bed_contact():
    tm = trimesh.creation.box(extents=(10, 10, 10))
    report = mesh_io.analyze_mesh(tm)
    assert report["watertight"] is True
    assert report["is_volume"] is True
    assert report["components"] == 1
    assert report["bed_contact_area_mm2"] == pytest.approx(100.0)
    assert report["unsupported_downward_area_pct"] == pytest.approx(0.0)


def test_overhang_is_area_weighted_and_above_bed():
    lower = trimesh.creation.box(extents=(10, 10, 2))
    upper = trimesh.creation.box(extents=(4, 4, 2))
    upper.apply_translation((0, 0, 4))
    tm = trimesh.util.concatenate((lower, upper))
    report = mesh_io.analyze_mesh(tm)
    assert report["components"] == 2
    assert report["unsupported_downward_area_mm2"] == pytest.approx(16.0)
    assert report["unsupported_downward_area_pct"] > 0.0


def test_analysis_rejects_invalid_thresholds():
    tm = trimesh.creation.box(extents=(1, 1, 1))
    with pytest.raises(ValueError, match="between 0 and 90"):
        mesh_io.analyze_mesh(tm, overhang_angle_deg=91)
