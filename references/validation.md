# Validation And Delivery

Validation has three layers: source/B-rep assertions, mesh checks, and visual or
slicer review. Passing one layer does not replace the others.

## Source And B-Rep Checks

In the model script, assert critical parameter relationships, CadQuery shape
validity, expected solid count, bounding dimensions, and positive volume. Check
known wall dimensions directly from parameters; do not infer minimum wall
thickness from model volume divided by bounding-box volume.

For fit-critical features, assert the final dimension after compensation. A
bounding box verifies only the outer envelope, not hole spacing or pocket depth.

## Mesh Checks

Run:

```bash
python3 run_cadquery_model.py model.py --preview --strict
```

Strict mode requires each STL to be watertight, consistently wound, a positive
volume, and no more than the allowed number of connected components. The JSON
`mesh_reports` includes dimensions, volume, components, bed-contact area, and an
area-weighted unsupported-downward percentage.

For one intentional multipart STL, raise the component allowance explicitly:

```bash
python3 run_cadquery_model.py model.py --strict --max-components 2
```

Prefer separate STLs for separate printable parts.

## Correct Overhang Convention

The runner measures face-normal angle from straight down:

- 0 degrees: horizontal downward ceiling, usually unsupported;
- 45 degrees: typical profile-dependent boundary;
- 90 degrees: vertical wall, self-supporting.

Faces lying on the lowest Z plane are counted as bed contact and excluded.
Results are weighted by triangle area, not triangle count. The percentage is a
screening metric: bridges, neighboring layers, feature width, and cooling still
require visual or slicer review.

When support-free printing is a requirement, choose a project-appropriate
threshold:

```bash
python3 run_cadquery_model.py model.py --preview --strict \
  --overhang-angle 45 --max-unsupported-area-pct 5
```

## Wall Thickness

There is no reliable general minimum-wall result from volume ratio. Validate
walls using this order:

1. Assert known wall, rib, floor, and boss dimensions in the parametric source.
2. Inspect the sliced perimeter toolpaths for missing or single-line regions.
3. For imported or freeform geometry, use a dedicated local-thickness/ray-cast
   tool and inspect the highlighted locations; do not reduce it to one global
   fill-ratio number.

## Visual Review

Inspect all preview views and confirm:

- requested features are present and positioned correctly;
- the bounding box and critical dimensions match the design contract;
- there are no floating or accidental components;
- the intended bed face is flat and sufficiently large;
- holes, pockets, bridges, and lower fillets suit the print orientation;
- assembly and removal paths are physically possible.

## Slicer Review

For fit-critical, load-bearing, large, or long prints, slice the actual final
export with the user's profile. Review warnings, first-layer contact, unsupported
islands, bridges, thin walls, and perimeters around loaded features. Record the
orientation and only the settings that materially differ from the user's preset.

## Delivery Checklist

- Model source runs from the delivered folder.
- Every STL passes strict mesh checks.
- Preview images were actually inspected.
- Critical fit assumptions and calibration profile are named.
- STL is delivered; native 3MF and STEP are included when useful and supported.
- Multipart files are clearly named.
- Print orientation, supports, material, layers, perimeters, and infill are
  summarized concisely.
- Remaining measurement or test-print uncertainty is explicit.
