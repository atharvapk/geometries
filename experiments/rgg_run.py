"""
RGG — Random Geometry Generator CLI
Generate random 3D primitives and export to STEP files.
"""

import argparse
import sys
import os
import warnings

# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Redirect stdout/stderr to /dev/null to suppress OCC STEP writer statistics.
# OCC's C++ streams are bound at import time to the original fd 1/2.
# We redirect at import time to suppress any OCC init output, then restore
# before printing. We re-redirect during export() to suppress the STEP writer
# statistics (which are C++ std::cout bypassing Python streams).
_old_stdout_fd = os.dup(1)
_old_stderr_fd = os.dup(2)
_devnull_fd = os.open(os.devnull, os.O_WRONLY)
os.dup2(_devnull_fd, 1)
os.dup2(_devnull_fd, 2)

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from rgg import RGGConfig, RGGGenerator, RGGExporter, launch_viewer, _pick_shape_type


def _restore_stdout():
    """Restore original stdout/stderr after suppressing OCC output."""
    os.dup2(_old_stdout_fd, 1)
    os.dup2(_old_stderr_fd, 2)


def _suppress_stdout():
    """Redirect stdout/stderr to /dev/null to suppress OCC C++ output."""
    os.dup2(_devnull_fd, 1)
    os.dup2(_devnull_fd, 2)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="rgg_run",
        description="RGG — Random Geometry Generator. "
        "Generates random 3D primitives (Box, Sphere, Cylinder) "
        "and exports them as STEP files.",
    )
    parser.add_argument(
        "--shape",
        type=str,
        choices=["Box", "Sphere", "Cylinder"],
        default=None,
        help="Force a specific shape type (default: random)",
    )
    parser.add_argument(
        "--viewer",
        action="store_true",
        help="Launch OCC 3D viewer after export",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="RGGoutputs",
        help="Output directory for STEP files (default: RGGoutputs)",
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Determine shape type
    shape_type = args.shape or _pick_shape_type()

    # Build config
    config = RGGConfig(
        shape_type=shape_type,
        output_dir=args.output_dir,
        launch_viewer=args.viewer,
    )

    # Print header
    _restore_stdout()
    print("=" * 44)
    print("  RGG — Random Geometry Generator")
    print("=" * 44)
    print(f"  Shape type:    {shape_type}")
    print(f"  Bounding box:  30 x 30 x 30 mm")
    print(f"  Center:        (0, 0, 0)")
    print(f"  Export format: STEP (AP242)")
    print("-" * 44)

    # Generate
    try:
        generator = RGGGenerator(config)
        shape = generator.generate()

        # Compute properties
        props = generator.compute_properties(shape)
        bb_min = props["bounding_box"]["min"]
        bb_max = props["bounding_box"]["max"]

        dim_x = bb_max[0] - bb_min[0]
        dim_y = bb_max[1] - bb_min[1]
        dim_z = bb_max[2] - bb_min[2]

        print(f"  Generated:     {shape_type}")
        print(f"  Dimensions:    {dim_x:.1f} x {dim_y:.1f} x {dim_z:.1f} mm")
        print(f"  Volume:        {props['volume']:.1f} mm³")

    except Exception as e:
        print(f"\n[Error] Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Export
    try:
        exporter = RGGExporter(config)

        # Suppress OCC STEP writer statistics (C++ std::cout bypasses Python streams)
        _suppress_stdout()
        filepath = exporter.export(shape, shape_type)
        _restore_stdout()

        print("-" * 44)
        print(f"  Exporting to:  {filepath}")
        print("-" * 44)
        print(f"  ✓ Export successful!")

    except Exception as e:
        print(f"\n[Error] Export failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Viewer
    if args.viewer:
        print(f"\n  Launching 3D viewer...")
        launch_viewer(shape, title=f"RGG — {shape_type}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
