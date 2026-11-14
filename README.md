# Geometries Monorepo
An exploration of geometric modelling for CAE, some conversion work, some automation work, and tinkering with opensource modelling engines.

## RGG — Random Geometry Generator

Generate random 3D primitives (Box, Sphere, Cylinder) using OpenCASCADE and export them as STEP files.

### Setup

```bash
# Install via conda (recommended for macOS ARM64)
conda create -n geometries python=3.9 -y
conda install -n geometries -c conda-forge pythonocc-core -y
conda activate geometries

# Or via pip on supported platforms
pip install -r requirements.txt
```

### Usage

```bash
# Generate a random shape
python experiments/rgg_run.py

# Force a specific shape
python experiments/rgg_run.py --shape Box
python experiments/rgg_run.py --shape Sphere
python experiments/rgg_run.py --shape Cylinder

# Launch 3D viewer after export
python experiments/rgg_run.py --viewer
python experiments/rgg_run.py --shape Cylinder --viewer

# Custom output directory
python experiments/rgg_run.py --output-dir my_output/
```

### Output

- One STEP file per run saved to `RGGoutputs/`
- Files named: `rgg_<shape>_<YYYYMMDD>_<HHMMSS>.step`
- All shapes centered at origin, fitting within 30×30×30 mm bounding box
- Export format: STEP AP242

## Research Questions
Some questions I want to explore:
1. How do we know there's something there? UV-net's trimming mask? Can we improve on that?
2. We can do planes and Signed Distance Field (SDF) enclosing, but what if we want to translate?
3. Can we encode multiple into one form? Carrying the SDF and the B-Rep? So that we can bypass user conversion for CAE prototyping.

Objectives for Self-Sufficient CAD Conversion Tools
1. Run the FreeCAD SolidWorks plugin (sw2fc) via CLI to extract raw Parasolid B-Rep geometry directly from .sldprt files on Linux.
2. Use OpenSW (WebAssembly) to unpack uncompressed Parasolid .x_t streams from .sldprt files without installing CAD software.
3. Write a headless C#/Python COM worker on Windows to batch export .sldprt files to STEP AP242 using silent OpenDoc6 and SaveAs3 calls.
4. Execute Creo Distributed Batch (ptcdbatch.bat) from the command line to automate bulk export of .prt files to STEP AP242.
5. Deploy a lightweight FastAPI service on Windows to accept remote conversion jobs and dispatch them to your local SolidWorks/Creo seats.
6. Ingest exported STEP files into Open CASCADE (pythonocc-core) to traverse topological faces, edges, and feature boundaries.
7. Run FreeCAD's headless Python Part module on Linux to compute volumes, bounding boxes, and surface areas directly from STEP files.