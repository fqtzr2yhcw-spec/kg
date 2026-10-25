# Build and release tools

Everything from a building's code to the files that go to the printers: a full check, then the
release (zip, build guide, version, Bambu Studio project). Run them from the `hoarch` folder.

## Setting up a machine (a Mac, or any Linux box)

1. Install Git, Python 3.11 (python.org or `brew install python@3.11`), and PrusaSlicer.
   On a Mac, put PrusaSlicer's command line on the PATH once:

       sudo ln -s /Applications/PrusaSlicer.app/Contents/MacOS/PrusaSlicer /usr/local/bin/prusa-slicer

   On Ubuntu: `sudo apt install prusa-slicer`.
2. Get the project and its Python packages:

       git clone https://github.com/fqtzr2yhcw-spec/kg.git
       cd kg/hoarch
       python3.11 -m venv .venv
       source .venv/bin/activate
       pip install -r requirements.txt

   (`bpy` is Blender as a Python module, about 400 MB; it only runs on Python 3.11.)
3. Each time you open a new terminal: `cd kg/hoarch && source .venv/bin/activate`.

## Checking a building

    python3 tools/check.py ashgrove            # or several: tools/check.py marisol fevre bethel

1. builds it, checks for interfering parts, exports and slices the plates;
2. `tools/printcheck.py`: sub-nozzle detail, overhangs, faces on a slicing plane;
3. `tools/glue_audit.py`: every part's glue face; SMALL marks a part on too small a spot;
4. `hoarch.audit`: the owner's rules (size, window runs, cornices, towers);
5. the showcase renders, every view in the building's palette (`--no-render` to skip; they
   take 10 to 30 minutes).

It writes one line per building to `out/progress.log`, for example

    ashgrove checked 14:38 | interfering pairs: 0 | glue small: 0 | == ashgrove: OK

and the details to `out/<building>/u/` (`final.log`, `printcheck.log`, `glue_audit.txt`,
`audit.txt`). Fix anything it finds before releasing.

## Releasing a building

    python3 tools/release.py ashgrove

1. the build-stage pictures for the guide (`hoarch.stages`);
2. the showcase renders copied in as the package's renders;
3. the build guide PDF (`hoarch.guide`);
4. `tools/package.py`: the plates, PRINT_NOTES.txt (from `hoarch/assembly.py`: the assembly
   steps, the print notes, the one-line joinery summary), the renders and the guide, zipped;
5. the version (`hoarch.versions`): `out/<Name>_Print_Files_vX.Y.zip` with its VERSION.txt, the
   older zip removed;
6. the Bambu Studio project for the P2S (`hoarch.bambu`): `out/<Name>_P2S_vX.Y.3mf`.

For an update to a building already sent, add a line to `HISTORY` in `hoarch/versions.py`
first, so the version goes up (v1.1, v1.2, ...).

## A new building

1. its module in `hoarch/buildings/` (and its new parts in the batch's library module);
2. its entry in `BUILDINGS` in `hoarch/guide.py` and `HOUSES` in `hoarch/audit.py`;
3. its assembly notes in `NOTES` in `hoarch/assembly.py`, its joinery line in `JOINERY`, and its
   zip name in `ZIPNAME` if it isn't just the key capitalised;
4. its row in `COLLECTION.md`;
5. `tools/check.py`, fix, then `tools/release.py`.

The packs and flatcar loads have their own pipeline: `python3 -m hoarch.packs <key> render export`.
