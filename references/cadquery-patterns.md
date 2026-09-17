# CadQuery Patterns

## Environment

Check for an existing compatible environment before installing anything. This
skill is tested with the versions in `requirements.txt`; use
`requirements-dev.txt` when running the bundled tests.

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
```

## Script Shape

Expose user-tunable and critical inputs, then derive internal dimensions. Keep
the bottom at Z=0 when that is the intended print orientation.

```python
import cadquery as cq

# User and calibration inputs (mm)
width = 60.0
depth = 40.0
height = 25.0
wall = 2.0
sliding_clearance_per_side = 0.25

# Derived dimensions
inner_w = width - 2 * wall
inner_d = depth - 2 * wall
assert wall >= 1.2
assert inner_w > 0 and inner_d > 0

outer = cq.Workplane("XY").box(
    width, depth, height, centered=(True, True, False)
)
inner = (
    cq.Workplane("XY")
    .workplane(offset=wall)
    .box(inner_w, inner_d, height, centered=(True, True, False))
)
result = outer.cut(inner)

assert result.val().isValid()
bb = result.val().BoundingBox()
assert abs(bb.xlen - width) < 0.05
assert abs(bb.ylen - depth) < 0.05

cq.exporters.export(result, "model.stl",
                    tolerance=0.05, angularTolerance=0.1)
cq.exporters.export(result, "model.step")
try:
    cq.exporters.export(result, "model.3mf")
except Exception as exc:
    print(f"3MF export unavailable: {exc}")
```

Use a tessellation tolerance appropriate to the process. Around 0.05 mm is a
reasonable FDM starting point; use finer values only for small curved features
that need them.

## Reliable Construction

- Prefer boolean subtraction for enclosure cavities when `.shell()` becomes
  fragile.
- Apply large fillets before dense cut patterns when that simplifies topology;
  select edges explicitly and validate after every risky operation.
- Use a small overlap epsilon for through-cuts so coplanar faces do not create
  zero-thickness results.
- Export each printable part separately. Do not hide disconnected bodies in one
  STL unless the user explicitly needs that arrangement.
- Check `result.val().isValid()`, expected solid count, critical dimensions, and
  positive volume before export.

## Risky Operations

Fillets, shells, lofts, and near-tangent booleans can fail after small parameter
changes. Do not silently catch a failure and shrink a requested dimension.
Report the conflict or revise the underlying geometry.

For loft-like transitions between similar profiles, a tapered extrusion is
often more stable. Use true lofts only when the profiles genuinely differ.

## Functional Features

- Model counterbores and countersinks explicitly with the intended screw fit.
- Connect bosses to the body; add ribs when loads require them.
- Give snap-fit beams an intentional root radius, deflection direction, and
  print orientation. Calibrate the material rather than using a generic clip.
- Use chamfers or teardrops for horizontal holes that must print without
  support.
- Add first-layer relief only to bed-facing fit surfaces, not globally.

## Exports

- STL: compatibility output; units are implicit, so keep the entire project in
  millimeters and report dimensions.
- 3MF: preferred slicer handoff when native CadQuery export is available.
- STEP: editable source geometry for downstream CAD.

Never convert a cavity-bearing STL to 3MF through the bundled fallback converter;
export 3MF directly from the CadQuery solid so cavity orientation is preserved.
