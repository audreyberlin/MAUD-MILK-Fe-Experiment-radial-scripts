#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import MILK
import pandas as pd
import build_cinema_database
from pathlib import Path
import copy
from tqdm import tqdm


def set_dataset_starting_values(editor, dataset, config_dataset) -> str:
    """Apply the dataset phase initialization from the config_dataset keys."""
    # Deep copy the editor object so no changes to editor leave this function
    editor = copy.deepcopy(editor)
    ifile = editor.ifile
    ofile = editor.ofile
    work_dir = editor.work_dir
    editor.work_dir = ''
    for datasetid, folder in enumerate(dataset["folder"]):
        file_path = Path(work_dir) / folder
        editor.ifile = str(file_path / ifile)
        editor.ofile = str(file_path / ofile)
        editor.read_par()
        editor.get_phases(use_stored_par=True)
        phase_names = editor.value
        for key in config_dataset["phase_initialization"].keys():
            for phaseid, phase_name in enumerate(phase_names):
                value = dataset[f"{key}_{phaseid}"][datasetid]
                if "_pd_phase_atom_" in key:
                    editor.set_val(
                        key=f"{key}", value=f"{value}", loopid=f"{phaseid}", use_stored_par=True)
                else:
                    editor.set_val(
                        key=f"{key}", value=f"{value}", sobj=phase_name, use_stored_par=True)
        editor.write_par()

    return ofile


def set_dataset_wild(run, editor, maudText):
    """From locical run array build wild."""
    wild = [i for i, x in enumerate(run) if x]
    editor.wild = wild
    maudText.wild = wild

def set_EWIMV(editor,resolution: float = 7.5, iterations: int = 10, refineable: bool = True, sobj=None):
           
        editor.texture(key='EWIMV', sobj=sobj)
        editor.set_val(key='_rita_wimv_iteration_max', value=f"{iterations}")
        editor.set_val(key='_rita_wimv_odf_resolution', value=f"{resolution}")
        if refineable:
            editor.set_val(key='_rita_odf_refinable', value='true')
        else:
            editor.set_val(key='_rita_odf_refinable', value='false')

def add_individual_background(nparameters,editor):
    for _ in range(0, nparameters):
        editor.add_datafile_bk_par()

if __name__ == '__main__':
    # Initialize environment
    #===================================================#
    config = MILK.load_json('milk.json')
    config_dataset = MILK.load_json('dataset.json')
    df = pd.read_csv("dataset2.csv")
    dataset = df.to_dict(orient='list')

    editor = MILK.parameterEditor.editor()
    editor.parseConfig(config, ifile='After_setup.par')
    maudText = MILK.maud.maudText()
    maudText.parseConfig(config, cur_step=2)
    #===================================================#

    # Set user parameters from dataset.csv (or not)
    #============================================================#
    set_dataset_wild(dataset["run"], editor, maudText)
    # editor.ifile = set_dataset_starting_values(editor, dataset, config_dataset)
    #=============================================

    #fix all parameters
    editor.fix_all()
    #======================================================
    # Setup phase fractions based on preidentified regions
    #===================================================#
    p = {'Copper': '0', 'Iron':'1'}
    #editor.set_val(key='_pd_phase_atom_', value='0.33')
    #editor.fix(key='_pd_phase_atom_')
    
    #If you want to adjust the pahse proportions prior to refining
    #editor.set_val(key='_pd_phase_atom_', loopid=p['Copper'], value='0.3')
    #editor.set_val(key='_pd_phase_atom_', loopid=p['Iron'], value='0.685')
    #editor.set_val(key='_pd_phase_atom_', loopid=p['Gasket'], value='0.02')
    #no_beta = list(range(0, 4))
    #for wild in no_beta:
        # editor.set_val(key='_pd_phase_atom_', loopid=p['alpha'],
        #                value='0.5', wild=[wild])
        # editor.set_val(key='_pd_phase_atom_', loopid=p['steel'],
        #                value='0.5', wild=[wild])
     #   editor.set_val(key='_pd_phase_atom_', loopid=p['beta'],
      #                 value='0.0', wild=[wild])

    #no_alpha = list(range(9, 19))
    #for wild in no_alpha:
     #   editor.set_val(key='_pd_phase_atom_', loopid=p['alpha'],
        #               value='0.0', wild=[wild])
        # editor.set_val(key='_pd_phase_atom_', loopid=p['steel'],
        #                value='0.5', wild=[wild])
        # editor.set_val(key='_pd_phase_atom_', loopid=p['beta'],
        #                value='0.5', wild=[wild])



    # Add backgrounds and free 
    #===================================================#
    set_dataset_wild(dataset["run"], editor, maudText)
    # for _ in range(0, 4):
    #     editor.add_loop_par(key='_riet_par_background_pol',
    #                         nsobj='chi(')  # Add shared background only
    add_individual_background(3,editor)
    editor.free(key='Background')

    # Sequential copy lattice parameters based on phase regions
    #===================================================#
    print("Starting sequential fit ...")
    wild_prev = editor.wild[0]  # Set wild_prev to the first element of the list
    for wild in tqdm(editor.wild, total=len(editor.wild)):
    #to run in reverse use the following
    #wild_prev = editor.wild[-1]  #-1 will start from from last element (reverse order)
    #for wild in tqdm(reversed(editor.wild), total=len(editor.wild)):
        # Copy lattice parameters from previous
        editor.get_val(key='cell_length_a', wild=[wild_prev])
        a = editor.value
        editor.get_val(key='cell_length_c', wild=[wild_prev])
        c = editor.value
        editor.set_val(key='cell_length', value=a[int(p['Copper'])], sobj='Copper', wild=[wild])
        editor.set_val(key='cell_length_a', value=a[int(p['Iron'])], sobj='Iron')
        editor.set_val(key='cell_length_c', value=c[int(p['Iron'])], sobj='Iron')
        #editor.set_val(key='cell_length', value=a[int(p['Gasket'])], sobj='Gasket')

        #if wild in no_alpha:
         #   editor.fix(key='_pd_phase_atom_', loopid=p['Iron'])
        #elif wild in no_beta:
        #    editor.fix(key='_pd_phase_atom_', loopid=p['beta'])

        # Free phase fractions and refine
        editor.free(key='_pd_phase_atom_', wild=[wild])
        editor.free(key='_pd_proc_intensity_incident')
        maudText.wild = [wild]
        maudText.refinement(itr='4', ifile=editor.ifile,
                            inc_step=False, simple_call=True) 

        # Conditionally free lattice parameters and refine
        #if wild not in no_alpha:
        print("starting unit cell refinements")
        editor.free(key='cell_length_a', sobj='Iron')
        editor.free(key='cell_length_c', sobj='Iron')
        editor.free(key='cell_length_a', sobj='Copper')

        #if wild not in no_beta:
        #    editor.free(key='cell_length_a', sobj='beta')
        
        maudText.refinement(itr='6', ifile=editor.ifile,
                            inc_step=False, simple_call=True) 
        
        #Set previous to current wild for sequential copy
        wild_prev = wild

    # Step 2: Consolodate results and refine stress step 2 in parallel
    #===============================================================#
    set_dataset_wild(dataset["run"], editor, maudText)
    #editor.free(key='_riet_par_background_peak_height')
    #editor.set_val(key='_riet_par_background_peak_hwhm',value='10.0')
    #editor.set_val(key='_riet_par_background_peak_hwhm',value='0.6')

    #fix all backgrounds then turn on global backgrounds
    editor.fix(key='Background')
    
    for x in range(0, 5): #free 5 global background polynomials
        editor.free(key='_riet_par_background_pol', nsobj='.esg', loopid=f'{x}')
   
    # Free phase fractions and refine
    print("starting phase proportion and incident intensity refinements")
    editor.free(key='_pd_phase_atom_', wild=[wild])
    editor.free(key='_pd_proc_intensity_incident')
    editor.free(key='_pd_meas_counts_monitor')
    
    #free Iron Q values
    #i controls which q factors are refined with 0 being the first in the list
    for i in [0, 1, 2, 3]:
        editor.free(key='_smlille_DAC_RDX_Qvalues', sobj='Iron', loopid=f'{i}')
    for j in [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]:
        editor.fix(key='_smlille_DAC_RDX_Qvalues', sobj='Iron', loopid=f'{j}')    
    
    #Free copper Q values
    #i controls which q factors are refined with 0 being the first in the list
    for i in [0, 1]:
        editor.free(key='_smlille_DAC_RDX_Qvalues', sobj='Copper', loopid=f'{i}')
    
    for j in [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]:
        editor.fix(key='_smlille_DAC_RDX_Qvalues', sobj='Copper', loopid=f'{j}')
    print("starting Q refinements")
                       
    #editor.free(key='_rista_macrostress_11', sobj='Copper')
    #editor.free(key='_rista_macrostress_11', sobj='Gasket')
    set_dataset_wild(dataset["run"], editor, maudText)

    # DEBUG before refinement
    print(f"\n=== DEBUG at line 181 ===")
    print(f"editor.work_dir = '{editor.work_dir}'")
    print(f"editor.ifile = '{editor.ifile}'")
    print(f"editor.wild = {editor.wild}")
    print(f"maudText.wild = {maudText.wild}")
    print(f"dataset['folder'] = {dataset['folder']}")
    print(f"=== END DEBUG ===\n")

    maudText.refinement(itr='8', ifile=editor.ifile,
                        inc_step=True, export_plots=True) #itr=8

    # Step 3: Free texture and broadening if phase fraction isn't too small
    #===================================================#
    #for wild in editor.wild:
     #   editor.get_val(key='_pd_phase_atom_', wild=[wild])
        #for vol,pname in zip(editor.value,p.keys()):
         #   if float(vol) > 0.01:
            #    editor.free(key='_rita_harmonic_parameter', sobj=pname)
    
    editor.fix(key='_pd_meas_counts_monitor')
    
    # set arbitrary texture for the gasket phase
    #editor.texture(key='Arbitrary', sobj='Gasket')

    #setting EWIMV for specific phases and imposing symmetry
    set_EWIMV(editor, sobj='Iron')
    set_EWIMV(editor, sobj='Copper')

    editor.set_val(key='_rita_generate_symmetry', value='fiber', sobj='Iron')
    editor.set_val(key='_rita_generate_symmetry', value='fiber', sobj='Copper')

    #Free Microstructure
    editor.free(key='MicroStrain', sobj='Iron')
    editor.free(key='CrystSize', sobj='Iron')
    editor.free(key='MicroStrain', sobj='Copper')
    editor.free(key='CrystSize', sobj='Copper')
    
    #free alpha and beta angles for radial diffraction in the DAC if you wish
    #editor.free(key='_smlille_DAC_RDX_offsetAlpha', sobj='Copper')
    #editor.free(key='_smlille_DAC_RDX_offsetBeta', sobj='Copper')
    #editor.free(key='_smlille_DAC_RDX_offsetAlpha', sobj='Iron')
    #editor.free(key='_smlille_DAC_RDX_offsetBeta', sobj='Iron')
    print("starting texture, crystallite size and microstrain refinements")
    maudText.refinement(itr='8', export_plots=True,
                        ifile=editor.ifile, ofile='After_seq_3_analysis_test2.par')

    # Build the cinema database and visualize
    #============================================================#
    build_cinema_database.main()
    MILK.cinema.main()
