======================================
Custom MCNP source routine information
======================================
The R2S-ACT workflow uses a custom photon sampling source routine in MCNP in order to sample particles on the mesh.

This folder contains a modified version(s) of the ``source.F90`` file, and a link to the custom-compiled DAG-MCNP executable that uses this custom ``source.F90`` file (link is only applicable for user in *cnergg* group on Wisconsin's CAE; see section *CNERG custom executables*).

As of Nov. 27, 2012, the most up to date/capable ``source.F90`` replacement is ``source_gamma.F90``.

source.F90 files
----------------
The different ``source.F90`` versions...

Wisconsin R2S-ACT:

:``source_gamma.F90``: Derived from ``vendor/source_gamma_meshtal2.F90``; Implements alias table sampling of voxels, as well as alias table sampling of photon energies. Also implements biasing. Uses ``gammas`` file that can include bias values and custom energy bins.  The original code was modified from 24 energy groups to 42 groups (or custom), and dynamic array allocation was added.

:``source_moab.F90``: Derived from ``source_gamma.F90``; Uses the iTaps Fortran API to read a MOAB mesh directly.  The ``gammas`` file is *not* used.

From KIT (Germany); Details specified in ``vendor/Leichtle_R2Smesh_Source_20111006.pdf``:

:``vendor/source_gamma_meshtal1.F90``: uses RDUM and IDUM cards in MCNP
:``vendor/source_gamma_meshtal2.F90``: reads in data from file ``gammas`` 

From CCFE (UK):

:``vendor/mcr2s_source.F90``: ...

Compiling
----------
In general, the user must copy or link the custom ``source.F90`` within the ``src`` directory for MCNP, and then build MCNP as usual.

General compiling tips
=======================
Todo

Compiling for CNERG users
==========================
On a CAE system, one should be able to use the mcnp5p links for running problems.

Alternately, to use one of these in a custom compile of MCNP/DAG-MCNP, one can check out the DAG-MCNP source, and then link the files in the repository to the ``DAG-MCNP/5.1.51/trunk/Source/src`` folder like this:

        ln -s *path to mcnp_source folder*/source_gamma.F90 source.F90

(or you could copy the file to that folder, but it won't get updated when changes happen in the repository)

To *compile* DAG-MCNP:

We call the build scripts from within the /5.1.51/trunk/Source folder.
Since we are using some custom code, the .o files are in the way... use 'clean' (But this also gives an error so we build twice...); do the following two commands:

1:
    �� ../scripts/build_dagmc clean

    �� error messages

2:
    �� ../scripts/build_dagmc

    �� Success!

You can now call the ``mcnp5`` executable that was created in ``Source/src``.

If you make further modifications to the same ``source.F90``, you can usually recompile directly with the second command above (clean is not needed).

You can make it easy to call my using an ``alias`` command in your ``.bashrc file``, e.g., for CNERG users:

        alias mcnp5p='$HOME/DAG-MCNP/5.1.51/trunk/Source/src/mcnp5'

CNERG custom executables
---------------------------
For those in CNERG, DAG-MCNP/MCNP5 executables compiled with the custom source routines are maintained.  You must be in the svn-dagmc group to access the modified executable. 
The executables are linked to as ``mcnp5p`` and ``mcnp5p_moab`` in ``r2s-act/mcnp_source``. 
The actual executables are managed/updated by Eric Relson (as of 3-13-2013).

Custom-compiled DAG-MCNP/MCNP5 executable links:

:``mcnp5p``: compiled with ``source_gamma.F90``; For use with workflow storing photon source info in the ``gammas`` file. (Structured mesh only)
:``mcnp5p_moab``: compiled with ``source_moab.F90``; For use with the workflow reading photon source info directly from a MOAB mesh.

testing/
---------
An ad-hoc testing framework using Python and bash scripting is located in the ``testing_gammas/`` and ``testing_moab/`` directories.  
This framework runs unit tests written in Fortran.  

A Python script extracts the necessary code from the custom ``source.F90``.
The bash script then combines this code with some external parts of the MCNP code-base needed for testing (Specifically MCNP's random number generator, which is not export controlled; it is reproduced in ``mcnp_placeholder.F90``), and compiles and runs the Fortran tests.

Information on running the tests is given in ``testing_gammas/README.rst`` and ``testing_moab/README.rst``.
