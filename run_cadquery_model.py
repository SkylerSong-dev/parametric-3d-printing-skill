#!/usr/bin/env python3
"""
Run a generated CadQuery model script in a subprocess and emit a structured
JSON result so an agent can parse success/failure without the user copy-pasting
tracebacks.

Usage:
    python3 run_cadquery_model.py path/to/model.py
    python3 run_cadquery_model.py path/to/model.py --preview            # also render
    python3 run_cadquery_model.py path/to/model.py --preview --strict

3MF and STEP files produced by the script (via cq.exporters.export(result,
"name.3mf") / cq.exporters.export(result, "name.step")) are discovered
automatically and reported alongside the STLs.

Emits a single JSON object to stdout (key order matches the emitted JSON):
    {
      "success": true/false,
      "script": "model.py",
      "stls": ["a.stl", "b.stl"],          # every .stl written during this run
      "stl": "a.stl",                       # newest, for single-file convenience
      "previews": ["a_preview.png", ...],   # one per STL when --preview is set
      "preview": "a_preview.png",           # newest, for single-file convenience
      "threemfs": ["a.3mf", "b.3mf"],       # every .3mf produced by the script
      "threemf": "a.3mf",                   # newest, for single-file convenience
      "steps": ["a.step", "b.step"],        # every .step produced by the script
      "step": "a.step",                     # newest, for single-file convenience
      "watertight": true/false/null,        # true only if ALL meshes are watertight
      "winding_consistent": true/false/null,
      "valid_volume": true/false/null,
      "mesh_reports": [{...}],              # one geometry report per STL
      "stdout": "...",
      "stderr": "...",
      "returncode": 0,                      # -1 on timeout / spawn failure
    }

Exit codes:
    0  success
    1  CadQuery script failed, preview failed, or --strict rejected output
    2  interpreter / script path could not be launched
    3  subprocess timed out
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time


def _sibling(path, suffix):
    return os.path.splitext(path)[0] + suffix


def _append_stderr(result, msg):
    result["stderr"] = (result["stderr"] or "") + msg + "\n"


def _new_files_by_ext(script_dir, after_mtime, exts):
    """Return {ext: [paths]} in script_dir matching each *.{ext}
    (case-insensitive) strictly newer than after_mtime, newest first.
    Dedupes case-variant hits that macOS's case-insensitive filesystem
    returns from both glob patterns.

    The threshold is strict (>=) rather than with a slack window because
    a backward slack would pull in stale files from a previous run started
    less than a second ago, silently reporting them as this run's output.
    Modern filesystems (APFS, ext4, NTFS) have sub-second mtimes, so a
    file written at exactly `after_mtime` is a valid hit.
    """
    buckets = {ext: {} for ext in exts}
    for ext in exts:
        for case in (ext.lower(), ext.upper()):
            for path in glob.glob(os.path.join(script_dir, f"*.{case}")):
                real = os.path.realpath(path)
                if real in buckets[ext]:
                    continue
                try:
                    mtime = os.path.getmtime(path)
                except OSError:
                    continue
                if mtime >= after_mtime:
                    buckets[ext][real] = (mtime, path)
    return {
        ext: [p for _, p in sorted(entries.values(), reverse=True)]
        for ext, entries in buckets.items()
    }


def _process_stls(stls, views, strict, want_preview, overhang_angle,
                  bed_tolerance, max_components,
                  max_unsupported_area_pct):
    """Load each STL once, analyze it, and optionally render a preview.

    Single pass so an STL is never loaded twice when both outputs are
    requested, and so all strict checks run on every mesh.

    `mesh_io` is imported lazily because the wrapper's common case (bare
    run, no --preview, no --strict) doesn't touch meshes at all. `preview`
    is imported only inside the rendering branch so that --strict by itself
    stays headless-safe (no pyrender / PyOpenGL required).

    Strict mode rejects invalid volume meshes, inconsistent winding, and too
    many connected components in addition to non-watertight output.
    """
    import mesh_io  # trimesh + numpy only

    out = {"previews": [], "mesh_reports": [], "error": None}

    for stl in stls:
        try:
            tm = mesh_io.load_mesh(stl)
        except ValueError as e:
            out["error"] = f"Mesh load failed ({stl}): {e}"
            return out

        report = mesh_io.analyze_mesh(
            tm,
            overhang_angle_deg=overhang_angle,
            bed_tolerance_mm=bed_tolerance,
        )
        report["path"] = stl
        out["mesh_reports"].append(report)

        strict_errors = []
        if strict and not report["watertight"]:
            strict_errors.append("not watertight")
        if strict and not report["winding_consistent"]:
            strict_errors.append("inconsistent face winding")
        if strict and not report["is_volume"]:
            strict_errors.append("not a positive closed volume")
        components = report["components"]
        if strict and components is not None and components > max_components:
            strict_errors.append(
                f"{components} connected components (maximum {max_components})"
            )
        unsupported_pct = report["unsupported_downward_area_pct"]
        if (max_unsupported_area_pct is not None
                and unsupported_pct > max_unsupported_area_pct):
            strict_errors.append(
                f"unsupported downward area {unsupported_pct:.2f}% "
                f"exceeds {max_unsupported_area_pct:.2f}%"
            )
        if strict_errors:
            out["error"] = f"Mesh {stl} failed validation: " + "; ".join(strict_errors)
            return out

        if want_preview:
            import preview  # heavy: trimesh + pyrender, only here
            preview_path = _sibling(stl, "_preview.png")
            try:
                if views == "multi":
                    preview.render_multi_view(tm, preview_path)
                else:
                    preview.render_single(tm, preview_path)
            except Exception as e:
                out["error"] = f"Preview render failed ({stl}): {e}"
                return out
            out["previews"].append(preview_path)

    return out


def main():
    parser = argparse.ArgumentParser(
        description="Run a CadQuery model script and report a JSON result",
        epilog="Exit codes: 0 success, 1 script/preview/--strict failure, "
               "2 interpreter not launchable, 3 timeout.",
    )
    parser.add_argument("script", help="Path to the CadQuery .py file")
    parser.add_argument("--preview", action="store_true",
                        help="Render a multi-view preview PNG for every STL the script wrote")
    parser.add_argument("--strict", action="store_true",
                        help="Fail if no STL is produced or a mesh is not a "
                             "watertight, consistently wound positive volume")
    parser.add_argument("--views", choices=["iso", "multi"], default="multi",
                        help="Preview layout: 'iso' (single isometric) or 'multi' (6-view) (default: multi)")
    parser.add_argument("--timeout", type=int, default=180,
                        help="Seconds before killing the model script (default: 180)")
    parser.add_argument("--max-components", type=int, default=1,
                        help="Maximum connected components per STL in strict mode (default: 1)")
    parser.add_argument("--overhang-angle", type=float, default=45.0,
                        help="Unsupported-face boundary measured from straight down (default: 45)")
    parser.add_argument("--bed-tolerance", type=float, default=0.05,
                        help="Z tolerance in mm for excluding bed-contact faces (default: 0.05)")
    parser.add_argument("--max-unsupported-area-pct", type=float, default=None,
                        help="Fail when area-weighted unsupported downward faces exceed this percent")
    args = parser.parse_args()

    if args.max_components < 1:
        parser.error("--max-components must be >= 1")
    if not 0.0 <= args.overhang_angle <= 90.0:
        parser.error("--overhang-angle must be between 0 and 90")
    if args.bed_tolerance < 0.0:
        parser.error("--bed-tolerance must be >= 0")
    if (args.max_unsupported_area_pct is not None
            and not 0.0 <= args.max_unsupported_area_pct <= 100.0):
        parser.error("--max-unsupported-area-pct must be between 0 and 100")

    script_path = os.path.abspath(args.script)
    script_dir = os.path.dirname(script_path) or "."

    result = {
        "success": False,
        "script": args.script,
        "stls": [],
        "stl": None,
        "previews": [],
        "preview": None,
        "threemfs": [],
        "threemf": None,
        "steps": [],
        "step": None,
        "watertight": None,
        "winding_consistent": None,
        "valid_volume": None,
        "mesh_reports": [],
        "stdout": "",
        "stderr": "",
        "returncode": -1,
    }

    started = time.time()

    try:
        proc = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=args.timeout,
            cwd=script_dir,
        )
    except subprocess.TimeoutExpired as e:
        _append_stderr(result, f"Timeout after {args.timeout}s: {e}")
        print(json.dumps(result, indent=2))
        sys.exit(3)
    except FileNotFoundError as e:
        _append_stderr(result, f"Cannot launch interpreter: {e}")
        print(json.dumps(result, indent=2))
        sys.exit(2)

    result["stdout"] = proc.stdout
    result["stderr"] = proc.stderr
    result["returncode"] = proc.returncode
    result["success"] = proc.returncode == 0

    if result["success"]:
        found = _new_files_by_ext(script_dir, started, ("stl", "3mf", "step", "stp"))
        result["stls"] = found["stl"]
        result["threemfs"] = found["3mf"]
        # CadQuery writes .step by convention; .stp is accepted too. Both
        # are merged into one list (newest-first within each extension).
        result["steps"] = found["step"] + found["stp"]

    # --strict implies the run must produce at least one STL. A script that
    # exits 0 but forgot to call cq.exporters.export() would otherwise slip
    # through with an empty stls list and a null watertight claim.
    if args.strict and result["success"] and not result["stls"]:
        _append_stderr(result, "No STL files produced by the script (--strict set).")
        result["success"] = False

    needs_mesh_pass = (
        args.preview or args.strict
        or args.max_unsupported_area_pct is not None
    )
    if needs_mesh_pass and result["success"] and result["stls"]:
        processed = _process_stls(
            result["stls"], args.views, args.strict,
            want_preview=args.preview,
            overhang_angle=args.overhang_angle,
            bed_tolerance=args.bed_tolerance,
            max_components=args.max_components,
            max_unsupported_area_pct=args.max_unsupported_area_pct,
        )
        result["previews"] = processed["previews"]
        result["mesh_reports"] = processed["mesh_reports"]
        if processed["mesh_reports"]:
            result["watertight"] = all(
                report["watertight"] for report in processed["mesh_reports"]
            )
            result["winding_consistent"] = all(
                report["winding_consistent"]
                for report in processed["mesh_reports"]
            )
            result["valid_volume"] = all(
                report["is_volume"] for report in processed["mesh_reports"]
            )
        if processed["error"]:
            _append_stderr(result, processed["error"])
            result["success"] = False

    result["stl"] = result["stls"][0] if result["stls"] else None
    result["preview"] = result["previews"][0] if result["previews"] else None
    result["threemf"] = result["threemfs"][0] if result["threemfs"] else None
    result["step"] = result["steps"][0] if result["steps"] else None

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
