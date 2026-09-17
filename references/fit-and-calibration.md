# Fit And Calibration

Dimensional compensation belongs to a printer, nozzle, material, layer-height,
and orientation combination. Do not encode one universal clearance table.

## Measurement Priority

1. Measure the user's actual object at the contact surfaces.
2. Use manufacturer drawings or component datasheets for nominal geometry.
3. Use reputable secondary sources only to fill non-critical gaps.
4. Label every unverified critical value and stop before a costly print when it
   could change the model materially.

Record measurement references such as overall envelope, center-to-center hole
spacing, maximum cross-section, and whether jaws, buttons, or cables move.

## Name The Fit Quantity

Use names that encode meaning and avoid double compensation:

```python
sliding_clearance_per_side = 0.25  # mm
bolt_hole_diametral_clearance = 0.30  # mm
press_fit_diametral_interference = 0.10  # mm
elephant_foot_relief = 0.25  # mm
```

For a pocket, add twice a per-side clearance to an overall width. For a round
hole, add a diametral clearance once. State the convention in comments and in
the delivery summary.

## Calibration Profile

Prefer a small project-local JSON file when the user has measured values:

```json
{
  "printer": "example-printer",
  "nozzle_mm": 0.4,
  "material": "PLA",
  "layer_height_mm": 0.2,
  "sliding_clearance_per_side_mm": 0.25,
  "bolt_hole_diametral_clearance_mm": 0.3,
  "press_fit_diametral_interference_mm": 0.08,
  "elephant_foot_relief_mm": 0.25,
  "horizontal_hole_extra_diameter_mm": 0.2,
  "bridge_limit_mm": 15,
  "unsupported_angle_from_down_deg": 45
}
```

Treat these as measured inputs, not defaults to copy between machines.

## Coupon Strategy

When fit is critical and no profile exists, make the smallest coupon that tests
the actual feature and orientation:

- sliding pockets: several per-side clearances around the expected range;
- pins and holes: stepped diameters, with vertical and horizontal holes tested
  separately;
- press fits: several small increments of diametral interference;
- snap fits: the real beam thickness, print orientation, and hook geometry;
- first-layer fits: include the same bed-facing chamfer used in the final part.

Emboss values directly on the coupon. Print it with the intended filament and
process preset, record the winning value, then update the profile.

## Fit Review

Before delivery, confirm:

- clearance is applied once and uses the stated convention;
- moving parts have travel and assembly clearance, not only static clearance;
- tolerances account for the selected orientation;
- the object can be inserted and removed ergonomically;
- brittle clips are not being treated as flexible snap fits;
- wear, heat, and repeated assembly are considered where relevant.
