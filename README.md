# Parametric 3D Printing Skill

A reconstructed Codex skill for designing and validating parametric,
FDM-printable parts with CadQuery. It supports functional parts, enclosures,
brackets, mounts, cases, Gridfinity storage, fit calibration, preview rendering,
and structured mesh validation.

## What Changed

- A 108-line `SKILL.md` routes to focused references instead of loading one
  large instruction file for every task.
- Checkpoints are risk-based: simple, fully specified parts can proceed in one
  pass, while uncertain fits and costly prints pause for review.
- Fit guidance uses named per-side or diametral values and printer/material
  calibration profiles.
- Validation checks watertightness, winding, positive volume, connected
  components, bed contact, and area-weighted unsupported geometry.
- The previous volume-ratio wall-thickness estimate and incorrect overhang
  calculation are removed.

## Install

Clone the repository into your Codex skills directory:

```bash
git clone https://github.com/SkylerSong-dev/parametric-3d-printing-skill.git \
  ~/.codex/skills/cad-skill
```

Do not keep two installed folders that both declare the skill name
`parametric-3d-printing`; replace or rename an existing copy first.

Install the optional CAD and test dependencies in a project environment:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
```

Use a Python version for which the selected CadQuery release provides wheels.

## Use

Ask Codex for a printable object, for example:

```text
Design a 3x1 Gridfinity cradle for my 150 mm digital calipers. Use a loose
storage fit, add a thumb notch, and make it printable without supports.
```

Validate a generated model with:

```bash
python3 run_cadquery_model.py model.py --preview --strict
```

For a support-free requirement, add an explicit threshold:

```bash
python3 run_cadquery_model.py model.py --preview --strict \
  --max-unsupported-area-pct 5
```

## Layout

- `SKILL.md`: compact workflow and reference router
- `references/`: FDM, calibration, CadQuery, Gridfinity, and validation guidance
- `run_cadquery_model.py`: model runner and structured mesh report
- `preview.py`: multi-view model previews
- `gridfinity.py`: vendored Gridfinity builder
- `tests/`: geometry, runner, Gridfinity, and export tests

## Upstream And License

This project is a reconstructed derivative of
[flowful-ai/cad-skill](https://github.com/flowful-ai/cad-skill). It retains the
upstream PolyForm Noncommercial License 1.0.0 in `LICENSE`.

Required Notice: Copyright Nicolas Chourrout (https://github.com/nchourrout)
