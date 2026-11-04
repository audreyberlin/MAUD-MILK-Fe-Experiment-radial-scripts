# Load dataset metadata
# Setup the integration jsons
json_2d = {
    "poni_file": [],
    "do_mask": True,
    "mask_file": [],
    "do_dark": True,
    "dark_file": [],
    "dark_norm": 1.0,
    "do_bright": False,
    "bright_file": [],
    "bright_norm": 1.0,
    "data_ops": [],
    "do_polarization": False,
    "polarization_factor": 0.99,
    "do_2D": False,
    "unit": "2th_deg",
    "npt_radial": 2048,
    "do_radial_range": True,
    "radial_range": [5, 30],
    "npt_azimuth": 72,
    "do_azimuthal_range": False,
    "azimuth_range": [0, 360],
    "chi_discontinuity_at_0": True,
    "do_solid_angle": False,
    "do_remove_nan": True,
    "error_model": "Poisson",
    "method": [
        "full",
        "histogram",
        "cython"
    ],
    "opencl_device": "cpu"
}


json_1d = {
    "poni_file": [],
    "do_mask": True,
    "mask_file": [],
    "do_dark": True,
    "dark_file": [],
    "dark_norm": 1.0,
    "do_bright": False,
    "bright_file": [],
    "bright_norm": 1.0,
    "data_ops": [],
    "do_polarization": False,
    "polarization_factor": 0.99,
    "do_2D": False,
    "unit": "2th_deg",
    "npt_radial": 2048,
    "do_radial_range": True,
    "radial_range": [5, 30],
    "npt_azimuth": 1,
    "do_azimuthal_range": False,
    "azimuth_range": [0, 360],
    "chi_discontinuity_at_0": True,
    "do_solid_angle": False,
    "do_remove_nan": True,
    "error_model": "Poisson",
    "method": [
        "full",
        "histogram",
        "cython"
    ],
    "opencl_device": "cpu"
}


from MILK.integration.integrate import main as int_main
# from MILK.bin.esg_loader import main as esg_loader_main
from tqdm import tqdm
from pathlib import Path
import json

def update_json(j, **d):
    """Take json dictionary and replace items using keyword arguments **d."""
    for k, v in d.items():
        j[k] = v
    return j


def write_json(j, file):
    """Write json dictionary to file."""
    with open(file, "w") as f:
        f.write(json.dumps(j,indent=4))


ndet = 1
# data_ops = ['rotccw flipud', 'rotccw fliplr',
#             'rotccw fliplr', 'rotccw flipud']
data_ops = [""]*ndet
bright_file = [""]*ndet
default_mask_file = ["mask.edf"]
do_dark = False
do_bright = False
data_files = ["CeO2*.edf"]
mask_file = ["mask.edf"]
poni_file = ["detector.poni"]
dark_file=["CeO2_20_04_2024-00003.dark.tif"]

json_1d_file = f"1d.azimint.json"
json_2d_file = f"2d.azimint.json"
write_json(update_json(json_1d,
                        data_ops=data_ops,
                        bright_file=bright_file,
                        mask_file=mask_file,
                        do_dark=do_dark,
                        do_bright=do_bright,
                        poni_file=poni_file,
                        dark_file=dark_file), json_1d_file)
write_json(update_json(json_2d,
                        data_ops=data_ops,
                        bright_file=bright_file,
                        mask_file=mask_file,
                        do_dark=do_dark,
                        do_bright=do_bright,
                        poni_file=poni_file,
                        dark_file=dark_file), json_2d_file)

# Perform the integration 1D
int_main(files=data_files,
            json_file=json_1d_file,
            output=Path(""),
            overwrite=True,
            poolsize=1,
            formats=['esg'],
            histogram_plot=True,
            quiet=False,
            use_glob=True)

# Perform the integration 2D for visualization only
int_main(files=data_files,
            json_file=json_2d_file,
            output=Path(""),
            overwrite=True,
            poolsize=1,
            formats=["esg1"],
            histogram_plot=True,
            quiet=False,
            use_glob=True)

