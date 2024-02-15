from __future__ import annotations
import os
from unittest import mock
from pymatgen.core.structure import Structure
from autoplex.auto.phonons.jobs import (
    get_phonon_ml_calculation_jobs,
    get_iso_atom,
    dft_phonopy_gen_data,
    MLPhononMaker,
)
from atomate2.common.schemas.phonons import PhononBSDOSDoc

from jobflow import run_locally

mock.patch.dict(os.environ, {"OMP_NUM_THREADS": 1, "OPENBLAS_OMP_THREADS": 2})


def test_get_phonon_ml_calculation_jobs(test_dir, clean_dir, memory_jobstore):
    potential_file_dir = test_dir / "fitting" / "ref_files" / "gap.xml"
    path_to_struct = test_dir / "fitting" / "ref_files" / "POSCAR"
    structure = Structure.from_file(path_to_struct)

    gap_phonon_jobs = get_phonon_ml_calculation_jobs(
        ml_dir=potential_file_dir, structure=structure, min_length=20
    )

    responses = run_locally(
        gap_phonon_jobs, create_folders=True, ensure_success=True, store=memory_jobstore
    )

    ml_phonon_bs_doc = responses[gap_phonon_jobs.output.uuid][2].output.resolve(
        store=memory_jobstore
    )
    assert isinstance(ml_phonon_bs_doc, PhononBSDOSDoc)


def test_ml_phonon_maker(test_dir, clean_dir, memory_jobstore):
    potential_file_dir = test_dir / "fitting" / "ref_files" / "gap.xml"
    path_to_struct = test_dir / "fitting" / "ref_files" / "POSCAR"
    structure = Structure.from_file(path_to_struct)

    gap_phonon_jobs = MLPhononMaker(ml_dir=potential_file_dir, min_length=20).make(
        structure=structure
    )

    assert gap_phonon_jobs.jobs[0].name == "GAP relax"
    assert gap_phonon_jobs.jobs[4].name == "GAP static"

    responses = run_locally(
        gap_phonon_jobs, create_folders=True, ensure_success=True, store=memory_jobstore
    )

    ml_phonon_bs_doc = responses[gap_phonon_jobs.jobs[-1].output.uuid][1].output
    assert isinstance(ml_phonon_bs_doc, PhononBSDOSDoc)

    assert (
        responses[gap_phonon_jobs.jobs[0].output.uuid][1].output.forcefield_name
        == "GAP"
    )
    assert (
        responses[gap_phonon_jobs.jobs[4].output.uuid][1].output.forcefield_name
        == "GAP"
    )


def test_get_iso_atom(vasp_test_dir, mock_vasp, clean_dir, memory_jobstore):
    structure_list = [
        Structure(
            lattice=[[0, 2.73, 2.73], [2.73, 0, 2.73], [2.73, 2.73, 0]],
            species=["Si", "Si"],
            coords=[[0, 0, 0], [0.25, 0.25, 0.25]],
        ),
        Structure(
            lattice=[[0, 2.73, 2.73], [2.73, 0, 2.73], [2.73, 2.73, 0]],
            species=["Mo", "C", "K"],
            coords=[[0, 0, 0], [0.25, 0.25, 0.25], [0.55, 0.55, 0.55]],
        ),
        Structure(
            lattice=[[0, 2.73, 2.73], [2.73, 0, 2.73], [2.73, 2.73, 0]],
            species=["Mo", "K"],
            coords=[[0, 0, 0], [0.25, 0.25, 0.25]],
        ),
        Structure(
            lattice=[[0, 2.73, 2.73], [2.73, 0, 2.73], [2.73, 2.73, 0]],
            species=["Li", "Na", "K"],
            coords=[[0, 0, 0], [0.25, 0.25, 0.25], [0.55, 0.55, 0.55]],
        ),
        Structure(
            lattice=[[0, 2.73, 2.73], [2.73, 0, 2.73], [2.73, 2.73, 0]],
            species=["Li", "Li"],
            coords=[[0, 0, 0], [0.25, 0.25, 0.25]],
        ),
        Structure(
            lattice=[[0, 2.73, 2.73], [2.73, 0, 2.73], [2.73, 2.73, 0]],
            species=["Li", "Cl"],
            coords=[[0, 0, 0], [0.25, 0.25, 0.25]],
        ),
    ]

    ref_paths = {
        "Li-statisoatom": "Li_iso_atoms/Li-statisoatom/",
        "Cl-statisoatom": "Cl_iso_atoms/Cl-statisoatom/",
        "C-statisoatom": "Cl_iso_atoms/Cl-statisoatom/",
        "Mo-statisoatom": "Cl_iso_atoms/Cl-statisoatom/",
        "K-statisoatom": "Cl_iso_atoms/Cl-statisoatom/",
        "Si-statisoatom": "Cl_iso_atoms/Cl-statisoatom/",
        "Na-statisoatom": "Cl_iso_atoms/Cl-statisoatom/",
    }

    # settings passed to fake_run_vasp; adjust these to check for certain INCAR settings
    fake_run_vasp_kwargs = {
        "Li-statisoatom": {
            "incar_settings": ["NSW"],
            "check_inputs": ["incar", "kpoints"],
        },
        "Cl-statisoatom": {
            "incar_settings": ["NSW"],
            "check_inputs": ["incar", "kpoints"],
        },
        "C-statisoatom": {
            "incar_settings": ["NSW"],
            "check_inputs": ["incar", "kpoints"],
        },
        "Mo-statisoatom": {
            "incar_settings": ["NSW"],
            "check_inputs": ["incar", "kpoints"],
        },
        "K-statisoatom": {
            "incar_settings": ["NSW"],
            "check_inputs": ["incar", "kpoints"],
        },
        "Si-statisoatom": {
            "incar_settings": ["NSW"],
            "check_inputs": ["incar", "kpoints"],
        },
        "Na-statisoatom": {
            "incar_settings": ["NSW"],
            "check_inputs": ["incar", "kpoints"],
        },
    }

    # automatically use fake VASP and write POTCAR.spec during the test
    mock_vasp(ref_paths, fake_run_vasp_kwargs)

    isolated_atom = get_iso_atom(structure_list)

    # run the flow or job and ensure that it finished running successfully
    responses = run_locally(isolated_atom, create_folders=True, ensure_success=True)

    assert (
        "[Element Li, Element C, Element Mo, Element Na, Element Si, Element Cl, Element K]"
        == f"{responses[isolated_atom.output.uuid][2].output['species']}"
    )
    assert (
        "Li"
        and "C"
        and "Mo"
        and "Na"
        and "Si"
        and "Cl"
        and "K" in f"{responses[isolated_atom.output.uuid][2].output['species']}"
    )


def test_dft_task_doc(vasp_test_dir, mock_vasp, test_dir, memory_jobstore, clean_dir):
    path_to_struct = vasp_test_dir / "dft_ml_data_generation" / "POSCAR"
    structure = Structure.from_file(path_to_struct)
    dft_phonon_workflow = dft_phonopy_gen_data(structure, [0.01], 0.1, None, 10)

    ref_paths = {
        "tight relax 1": "dft_ml_data_generation/tight_relax_1/",
        "tight relax 2": "dft_ml_data_generation/tight_relax_2/",
        "static": "dft_ml_data_generation/static/",
        "phonon static 1/2": "dft_ml_data_generation/phonon_static_1/",
        "phonon static 2/2": "dft_ml_data_generation/phonon_static_2/",
        "phonon static 1/3": "dft_ml_data_generation/rand_static_1/",
        "phonon static 2/3": "dft_ml_data_generation/rand_static_2/",
        "phonon static 3/3": "dft_ml_data_generation/rand_static_3/",
    }

    fake_run_vasp_kwargs = {
        "tight relax 1": {"incar_settings": ["NSW", "ISMEAR"]},
        "tight relax 2": {"incar_settings": ["NSW", "ISMEAR"]},
        "phonon static 1/2": {"incar_settings": ["NSW"]},
        "phonon static 2/2": {"incar_settings": ["NSW"]},
        "phonon static 1/3": {
            "incar_settings": ["NSW"],
            "check_inputs": ["incar", "kpoints", "potcar"],
        },
        "phonon static 2/3": {
            "incar_settings": ["NSW"],
            "check_inputs": ["incar", "kpoints", "potcar"],
        },
        "phonon static 3/3": {
            "incar_settings": ["NSW"],
            "check_inputs": ["incar", "kpoints", "potcar"],
        },
    }

    # automatically use fake VASP and write POTCAR.spec during the test
    mock_vasp(ref_paths, fake_run_vasp_kwargs)

    # run the flow or job and ensure that it finished running successfully
    responses = run_locally(
        dft_phonon_workflow,
        create_folders=True,
        ensure_success=True,
        store=memory_jobstore,
    )

    # check for DFT phonon doc
    assert isinstance(
        dft_phonon_workflow.output.resolve(store=memory_jobstore)["data"]["001"],
        PhononBSDOSDoc,
    )