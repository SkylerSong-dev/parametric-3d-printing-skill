---
name: parametric-3d-printing
description: Design and validate parametric CadQuery models for FDM manufacture, including functional parts, enclosures, brackets, mounts, cases, and Gridfinity storage. Use when the user wants printable geometry or print-oriented design advice. Do not use for digital-only 3D art, rendering, animation, sculpting, or editing an existing STL supplied by the user.
---

# Parametric 3D Printing

Create dimensionally explicit, editable CadQuery models and verify that their
meshes are suitable for the user's printer and intended load. Prefer a small,
reliable design over unsupported detail or guessed fit.

## Route The Task

Read only the references needed for the request:

- Read [references/fdm-design-rules.md](references/fdm-design-rules.md) when
  choosing wall thickness, orientation, load paths, holes, bridges, supports,
  materials, or slicer recommendations.
- Read [references/fit-and-calibration.md](references/fit-and-calibration.md)
  for mating parts, pockets, lids, fasteners, snap fits, press fits, or any
  dimension whose fit matters.
- Read [references/cadquery-patterns.md](references/cadquery-patterns.md) when
  implementing or debugging CadQuery geometry.
- Read [references/gridfinity.md](references/gridfinity.md) only for
  Gridfinity bins, inserts, or cradles.
- Read [references/validation.md](references/validation.md) before validating
  or delivering any model.

## Establish The Design Contract

Get the object, purpose, and must-fit dimensions first. Then collect only the
details that change the geometry: attachment method, expected load, environment,
printer/nozzle, material, and access needs. Defaults for an unspecified ordinary
prototype are a 0.4 mm nozzle, PLA, and 0.20 mm layers.

For objects that already exist, prefer the user's caliper measurements and note
their measurement references. Manufacturer drawings and datasheets are useful
for nominal dimensions; web listings are not a substitute for measuring the
specific object. Never silently invent a critical dimension.

Use a known printer/material calibration profile for fits. If none exists and
fit is critical, design a small coupon before committing to a long print.

## Choose Checkpoints By Risk

Proceed in one pass when the part is simple, fully specified, and cheap to
print. Show a preview and pause before finalizing when any of these are true:

- the overall form or aesthetics are ambiguous;
- a mating fit, snap, hinge, or device outline is uncertain;
- the part is load-bearing, safety-relevant, large, or expensive to print;
- several plausible orientations materially change strength or support use.

For complex work, use checkpoints after the base form and after functional
features. Do not require ceremonial approval between phases when no meaningful
decision remains.

## Build

1. Put user-tunable and critical dimensions in a parameters section with units.
   Keep derived dimensions as formulas rather than duplicate parameters.
2. Set the intended print orientation before shaping holes, bridges, chamfers,
   and load-bearing features.
3. Build the simplest valid solid, then add functional features and finishing
   geometry. Avoid zero-thickness contacts and disconnected bodies.
4. Export STL for broad slicer compatibility. Also export native 3MF when the
   installed CadQuery version supports it, and STEP when editable CAD is useful.
5. Run the model and mesh checks:

   ```bash
   python3 run_cadquery_model.py model.py --preview --strict
   ```

6. Inspect every preview. Confirm visible features, bounding dimensions, print
   orientation, bed contact, unsupported regions, and whether separate parts
   were exported separately.
7. When a support-free result is required, set an explicit unsupported-area
   limit rather than relying on visual intuition alone:

   ```bash
   python3 run_cadquery_model.py model.py --preview --strict \
     --max-unsupported-area-pct 5
   ```

8. Fix the model and rerun validation until it passes. Do not weaken checks to
   hide invalid geometry.

## Deliver

Deliver the model source, STL files, preview images, and any generated 3MF or
STEP files. For multipart designs, name and export each printable part
separately.

Include:

- the critical dimensions and assumed calibration profile;
- orientation and support guidance;
- a concise slicer recipe covering material, layer height, perimeters, infill,
  and any exceptional setting;
- uncertainties that still require a measurement or test print.

For a routine functional PLA part with a 0.4 mm nozzle, a reasonable starting
recipe is 0.20 mm layers, 3 perimeters, 15% infill, and no supports only when the
geometry review supports that claim. Increase perimeters and orient the layer
lines around the actual load path before increasing infill.

Offer the small set of parameters a user is likely to adjust; omit internal
construction constants.
