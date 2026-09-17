# Gridfinity

Use the bundled `gridfinity.py`; do not recreate the base profile from memory.
Copy the module beside the generated model so the delivered script remains
runnable.

```python
import cadquery as cq
from gridfinity import GridfinityBin

bin = GridfinityBin(
    grid_x=3,
    grid_y=2,
    height_units=3,
    stacking_lip=True,
    magnets=False,
)
bin.add_pocket(length=88.6, width=72.6, corner_r=(12.0, 1.0))
result = bin.build()

cq.exporters.export(result, "gridfinity_bin.stl",
                    tolerance=0.05, angularTolerance=0.1)
print(bin.summary())
```

The builder owns the 42 mm pitch, 7 mm height unit, base profile, lip, magnet
bores, and screw-hole pattern. Read `bin.outer_w`, `bin.outer_d`, `bin.total_h`,
`bin.floor_z`, and `bin.max_depth` rather than recomputing them.

## Object-Fitting Inserts

- Measure the actual object's maximum envelope and contact shape. For calipers,
  include the closed jaws, depth rod, thumb wheel, display housing, and an
  ergonomic finger-removal region.
- Use a named per-side clearance from the printer profile. Add extra removal
  room separately instead of folding it into an unexplained fit constant.
- Use `outline_from_scan.py` and `add_polygon_pocket` when a measured or scanned
  outline matters more than a rectangular pocket.
- Let contents protrude when that improves access, but keep the bin stable and
  protect delicate surfaces.
- Use `add_finger_notch` or an overlapping cylinder pocket for removal access.

Available construction methods include `add_pocket`, `add_polygon_pocket`,
`add_cylinder_pocket`, `add_compartments`, and `add_finger_notch`. Let
`GridfinityError` expose invalid walls, depths, or feature positions; fix the
parameters rather than bypassing validation.

Use magnets only when the user's baseplate needs them. For ordinary drawer bins,
omitting magnets and screws saves print time and material.

For unsupported baseplates or nonstandard profiles, custom geometry is allowed,
but retain the constants in `gridfinity.py` as the source of truth and clearly
label departures from the standard.
