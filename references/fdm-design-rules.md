# FDM Design Rules

Use these rules as decision criteria, not universal constants. Printer tuning,
line width, material, orientation, and feature shape all affect the result.

## Start From The Load Path

- Choose print orientation before detailed geometry. FDM parts are weakest
  between layers; keep primary tensile and bending loads within layers when
  practical.
- Add material where stress flows: generous internal radii, gussets, ribs, and
  wider attachment regions usually help more than high global infill.
- Prefer 3 perimeters for ordinary functional parts and 4 or more around
  brackets, bosses, hinges, and threaded hardware. Use infill mainly to support
  top surfaces and distribute loads between shells.
- Avoid sharp internal corners at loaded transitions. Add fillets where they do
  not create an unsupported lower surface.

## Geometry Relative To The Nozzle

Treat the slicer's actual extrusion width as the design unit. With a typical
0.4 mm nozzle, start near these values only when no calibrated profile exists:

| Feature | Starting point |
| --- | --- |
| Functional wall | 3 line widths, usually about 1.2-1.35 mm minimum |
| Robust enclosure wall | 1.8-2.4 mm |
| Freestanding rib or pin | at least 2 line widths; more if loaded |
| Embossed/debossed detail | at least 1 line width and 2 layers deep/high |
| First-layer relief | 0.2-0.4 mm chamfer when elephant foot affects fit |

Do not specify a nominal wall that the slicer resolves into an unstable partial
line. When possible, inspect the sliced toolpaths.

## Unsupported Geometry

- State angle conventions explicitly. In this skill, an underside at 0 degrees
  from straight down is a horizontal ceiling and usually needs support; a
  vertical wall is 90 degrees and is self-supporting.
- Bridge capability depends on cooling, material, speed, and span. Treat any
  fixed span limit as a profile value, not a law.
- Use chamfers, arches, teardrop horizontal holes, split parts, or changed
  orientation before adding supports.
- Bed-contacting downward faces are not overhangs. Automated analysis must
  exclude faces at the lowest Z plane.

## Holes And Hardware

- Horizontal circular holes often print undersized and sag at the crown. Use a
  calibrated diameter, a teardrop/diamond profile, or plan to drill/ream.
- Define screw clearance by the desired fit class and state whether compensation
  is diametral or per side.
- Give bosses enough radial material and connect them to nearby walls with ribs
  when loaded.
- For repeated assembly, prefer heat-set inserts, captive nuts, or through-bolts
  over threads cut directly into brittle plastic.

## Materials

- PLA is stiff and easy to print but is unsuitable for sustained heat or some
  impact applications.
- PETG is tougher and more heat resistant but can string and may bridge less
  cleanly on a given machine.
- ASA/ABS need controlled cooling and shrink calibration; do not compensate by
  blindly scaling all geometry.
- TPU fit depends strongly on hardness, wall count, and compression direction.
  Treat it as a separate calibration profile.

For food, medical, high-temperature, structural, or safety-critical use, state
the limitation instead of claiming that a generic coating makes the part safe.

## Slicer Review

For consequential parts, slice the final export and inspect layer view for:

- missing thin features or gaps;
- unexpected single-line walls;
- unsupported islands and bridges;
- first-layer contact and elephant-foot-sensitive fits;
- seam placement near loaded or sealing surfaces;
- perimeters around holes, bosses, and fasteners.

Use the user's established filament and process preset. Report only settings
that differ from that baseline or materially affect this model.
