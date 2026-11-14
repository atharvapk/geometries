"""
RGG — Random Geometry Generator
Generates random 3D primitives (Box, Sphere, Cylinder) using OpenCASCADE.
Each shape is centered at the origin and fits within a 30×30×30 mm bounding box.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal, Union

import random

from OCC.Core.BRepPrimAPI import (
    BRepPrimAPI_MakeBox,
    BRepPrimAPI_MakeSphere,
    BRepPrimAPI_MakeCylinder,
)
from OCC.Core.gp import gp_Pnt, gp_Ax1, gp_Ax2, gp_Dir, gp_Vec, gp_Trsf, gp_XYZ
from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.BRepCheck import BRepCheck_Analyzer
from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCC.Core.Interface import Interface_Static


ShapeType = Literal["Box", "Sphere", "Cylinder"]


@dataclass
class RGGConfig:
    """Configuration for the Random Geometry Generator."""

    shape_type: Union[ShapeType, None] = None  # None = random choice
    bounding_box: tuple[float, float, float] = (30.0, 30.0, 30.0)  # mm
    center: tuple[float, float, float] = (0.0, 0.0, 0.0)  # mm
    min_size: float = 1.0  # mm — minimum dimension
    export_format: Literal["STEP"] = "STEP"
    output_dir: str = "RGGoutputs"
    launch_viewer: bool = False


def _pick_shape_type(types: Union[list[ShapeType], None] = None) -> ShapeType:
    """Randomly pick a shape type from the available options."""
    if types is None:
        types = ["Box", "Sphere", "Cylinder"]
    return random.choice(types)


def _random_dim(max_val: float, min_val: float = 1.0) -> float:
    """Generate a random dimension clamped within [min_val, max_val]."""
    return round(random.uniform(min_val, max_val), 2)


def _center_shape(shape: TopoDS_Shape) -> TopoDS_Shape:
    """Translate a shape so its bounding box center is at the origin."""
    from OCC.Core.BRepBndLib import brepbndlib
    from OCC.Core.Bnd import Bnd_Box
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform

    bb = Bnd_Box()
    brepbndlib.Add(shape, bb)
    xmin, ymin, zmin, xmax, ymax, zmax = bb.Get()

    cx = (xmin + xmax) / 2.0
    cy = (ymin + ymax) / 2.0
    cz = (zmin + zmax) / 2.0

    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(-cx, -cy, -cz))
    builder = BRepBuilderAPI_Transform(trsf)
    builder.Perform(shape)
    result = builder.Shape()
    return result


class RGGGenerator:
    """Generates random 3D primitives centered at the origin."""

    def __init__(self, config: RGGConfig):
        self.config = config

    def generate(self) -> TopoDS_Shape:
        """Generate a random shape and return it as a TopoDS_Shape."""
        shape_type = self.config.shape_type or _pick_shape_type()
        max_dim = min(self.config.bounding_box)

        if shape_type == "Box":
            width = _random_dim(max_dim, self.config.min_size)
            height = _random_dim(max_dim, self.config.min_size)
            depth = _random_dim(max_dim, self.config.min_size)
            shape = self._make_box(width, height, depth)

        elif shape_type == "Sphere":
            diameter = _random_dim(max_dim, self.config.min_size)
            radius = diameter / 2.0
            shape = self._make_sphere(radius)

        elif shape_type == "Cylinder":
            diameter = _random_dim(max_dim, self.config.min_size)
            height = _random_dim(max_dim, self.config.min_size)
            radius = diameter / 2.0
            shape = self._make_cylinder(radius, height)

        else:
            raise ValueError(f"Unknown shape type: {shape_type}")

        # Center the shape at origin
        shape = _center_shape(shape)

        # Validate the shape
        analyzer = BRepCheck_Analyzer(shape)
        if not analyzer.IsValid():
            raise RuntimeError(f"Generated {shape_type} is not valid")

        return shape

    def _make_box(self, width: float, height: float, depth: float) -> TopoDS_Shape:
        """Create a box centered at the origin using BRepPrimAPI_MakeBox with 3 points."""
        hx, hy, hz = width / 2.0, height / 2.0, depth / 2.0
        # Use 3-point constructor: corner1, corner2, corner3 define the box
        # This creates a box centered at origin
        box = BRepPrimAPI_MakeBox(
            gp_Pnt(-hx, -hy, -hz),
            gp_Pnt(hx, hy, hz),
        ).Shape()
        return box

    def _make_sphere(self, radius: float) -> TopoDS_Shape:
        """Create a sphere centered at the origin."""
        sphere = BRepPrimAPI_MakeSphere(gp_Pnt(0, 0, 0), radius).Shape()
        return sphere

    def _make_cylinder(self, radius: float, height: float) -> TopoDS_Shape:
        """Create a cylinder centered at the origin, aligned with Z axis."""
        center = gp_Pnt(0, 0, 0)
        axis = gp_Ax2(center, gp_Dir(0, 0, 1))
        # BRepPrimAPI_MakeCylinder with axis creates from z=0 to z=height
        # We need to center it: create from -height/2 to +height/2
        cylinder = BRepPrimAPI_MakeCylinder(axis, radius, height).Shape()
        return cylinder

    def compute_properties(self, shape: TopoDS_Shape) -> dict:
        """Compute volume and bounding box of the shape."""
        from OCC.Core.GProp import GProp_GProps
        from OCC.Core.BRepBndLib import brepbndlib
        from OCC.Core.Bnd import Bnd_Box
        from OCC.Core.BRepGProp import brepgprop

        # Volume
        props = GProp_GProps()
        brepgprop.VolumeProperties(shape, props)
        volume = props.Mass()

        # Bounding box
        bb = Bnd_Box()
        brepbndlib.Add(shape, bb)
        xmin, ymin, zmin, xmax, ymax, zmax = bb.Get()

        return {
            "volume": round(volume, 2),
            "bounding_box": {
                "min": (round(xmin, 2), round(ymin, 2), round(zmin, 2)),
                "max": (round(xmax, 2), round(ymax, 2), round(zmax, 2)),
            },
        }


class RGGExporter:
    """Export shapes to STEP format."""

    def __init__(self, config: RGGConfig):
        self.config = config
        self.output_path = Path(config.output_dir)
        self.output_path.mkdir(parents=True, exist_ok=True)

    def export(
        self,
        shape: TopoDS_Shape,
        shape_type: str,
        timestamp: Union[datetime, None] = None,
    ) -> Path:
        """Export a shape to STEP file."""
        if timestamp is None:
            timestamp = datetime.now()

        date_str = timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"rgg_{shape_type.lower()}_{date_str}.step"
        filepath = self.output_path / filename

        # Configure STEP writer
        Interface_Static.SetCVal("write.step.schema", "AP242")

        writer = STEPControl_Writer()
        writer.Transfer(shape, STEPControl_AsIs)

        status = writer.Write(str(filepath))

        if status != 1:
            raise RuntimeError(f"STEP export failed with status: {status}")

        return filepath


def launch_viewer(shape: TopoDS_Shape, title: str = "RGG Viewer") -> None:
    """Launch the OCC 3D viewer to display the shape."""
    try:
        from OCC.Display.SimpleGui import init_display

        display, start_display, add_menu, add_function_to_menu = init_display(
            size=(800, 600)
        )
        display.SetBackground(40, 40, 45)
        display.DisplayShape(shape, update=True)
        display.FitAll()
        start_display()

    except ImportError as e:
        print(f"[Viewer] Display module not available: {e}")
        print("[Viewer] Skipping 3D viewer.")

