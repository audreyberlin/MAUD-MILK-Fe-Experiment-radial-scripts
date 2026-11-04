# MAUD-MILK analysis of radial DAC iron (DESY 2024, experiment Fe2)

Scripts and raw data for the MILK/MAUD Rietveld analysis of a radial diamond anvil cell
compression of iron through the bcc → hcp transition (one ramp, `fe2_ramp1`, 20 diffraction
images, λ = 0.4855 Å, PerkinElmer detector). Everything needed to rerun the analysis from the raw
detector images is included.

The ramp is split into three sample folders by phase, each refined with its own template:

| Folder | Images | Phases in the template |
|---|---|---|
| `fe20_bccFe/` | `fe2_ramp1-00001` … `00006` | Copper (pressure standard), Iron-alpha (bcc) |
| `fe21_bcc_hcpCoexist/` | `00007` … `00009` | Copper, Iron (hcp), Iron-alpha (bcc) |
| `fe18_hcpFe/` | `00010` … `00020` | Copper, Iron (hcp) |

## Repository layout

```
calibration/                CeO2 calibrant image, mask, pyFAI geometry and the MAUD instrument file
  5_process_images.ipynb    CeO2 .tif -> .edf/.png
  6_integrate.py            CeO2 .edf -> .esg (pyFAI)
  detector.poni             detector geometry used for all integrations
  calibrated.par            MAUD instrument calibration (refined in the MAUD GUI on the CeO2 .esg)
process_data.ipynb          mask, image conversion and pyFAI 1D/2D integration for all three samples
milk_data_import_3.ipynb    optional: how a template .par is made (templates are already provided)
pco/                        sample-camera (PCO) images for the whole ramp; visualization only
fe20_bccFe/                 one folder per sample (same layout in each):
  data/diff/                raw detector images (.tif) and the hand-drawn mask (mask.edf)
  data/1d.azimint.json      pyFAI integration settings (rewritten by process_data.ipynb)
  data/2d.azimint.json
  template/template.par     MAUD starting model for this sample
  dataset.json              2θ range, data folder, starting phase values
  milk.json                 MILK settings (run folders, number of MAUD instances, Java memory)
  1_build_database.py       creates run000, run001, … (one per image) from the template
  2_setup.py                step 1: background, scale, cell, phase fractions
  3_analysis_Q.py           steps 2–3: sequential fit, Q(hkl), texture (EWIMV), size/strain
  build_cinema_database.py  collects the refined values into data.csv for Cinema
  run_cinema.py             rebuilds data.csv and opens the Cinema viewer
fe21_bcc_hcpCoexist/
fe18_hcpFe/
```

## Requirements

* **MAUD 2.9993** (the templates were written with this version). Download from
  <https://luttero.github.io/maud/>.
* **MILK** and its conda environment (`rietveld`, Python 3.9, includes pyFAI and fabio). Follow the
  [MILK installation wiki](https://github.com/lanl/MILK/wiki/Installation-Overview); the
  environment files are in `environments/` of the [MILK repository](https://github.com/lanl/MILK).
* **Cinema: Debye-Scherrer** viewer (optional, for browsing results):
  `git clone https://github.com/cinemascience/cinema_debye_scherrer.git`
* Point MILK at MAUD and Cinema once, inside the activated environment, then deactivate and
  reactivate it:

  ```
  conda activate rietveld
  milk-config "<full path to MAUD>" -c "<full path to cinema_debye_scherrer>"
  ```

Each sample's `milk.json` runs 8 MAUD instances at once with 8 GB Java memory each
(`"n_maud": 8`, `"java_opt": "mx8G"`). Lower these on a smaller machine.

## Running the analysis

All commands use the `rietveld` environment.

**0. Calibration (optional).** `calibration/detector.poni` and `calibration/calibrated.par` are
already provided. To reproduce them: open `calibration/5_process_images.ipynb` and run it, then
`cd calibration` and `python 6_integrate.py`. `calibrated.par` was refined interactively in the
MAUD GUI on `CeO2_20_04_2024-00003_2d.esg`.

**1. Integrate the images.** From the repository root, run all cells of `process_data.ipynb`.
For each sample this builds `data/diff/mask_full.edf` (hand-drawn mask plus a saturation
threshold), writes `.edf` and `.png` versions of each image, and integrates them into
`*_2d.esg` files (72 azimuthal sectors, 2θ 8–21°) next to the images. It also writes small
Cinema databases (`diff_cinema_db/`, `pco_cinema_db/`) for looking at the raw images.

**2. Refine each sample.** For each of `fe20_bccFe`, `fe21_bcc_hcpCoexist` and `fe18_hcpFe`:

```
cd fe20_bccFe
python 1_build_database.py
python 2_setup.py
python 3_analysis_Q.py
```

* `1_build_database.py` makes one run folder per image (`run000`, `run001`, …), each holding
  `Initial.par` and that image's `.esg`, and writes the run table (`dataset2.csv`, or
  `dataset_fe21.csv` in `fe21_bcc_hcpCoexist`).
* `2_setup.py` refines background, scale, cell parameters and phase fractions, ending in
  `After_setup*.par` in every run folder.
* `3_analysis_Q.py` does a sequential fit, refines the lattice-strain Q(hkl) values, then texture
  (EWIMV), crystallite size and microstrain. The final model in each run folder is
  `After_seq_3_analysis_*.par`. Each refinement stage is archived in `runNNN/step_N/` with
  MAUD's 1D and 2D fit plots, and Rwp for every run is in `results0N.txt`.
* At the end it builds `data.csv` and opens the Cinema viewer in the browser at
  <http://127.0.0.1:8080>. To reopen it later: `python run_cinema.py`.

**3. Optional: make a template.** `milk_data_import_3.ipynb` imports one sample's `.esg` files into
the calibrated instrument (`calibration/calibrated.par`) and writes them to
`<sample>/maud_import/runNNN/Initial.par`. That is the starting point for building a
`template.par` in the MAUD GUI. It is not needed to rerun the analysis.

## Notes

* Run the notebooks from the repository root and the `1_`/`2_`/`3_` scripts from inside their
  sample folder; all paths are relative to those locations.
* To start a sample over, delete its `run*/` folders, `dataset*.csv`, `results*.txt` and
  `data.csv`, then rerun from `1_build_database.py`.
* `calibration/CeO2_20_04_2024-00003.dark.tif` is included for completeness; dark subtraction is
  not used (`"do_dark": false`).
