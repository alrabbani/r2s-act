#!/usr/bin/env python
# This script reads an MCNP input file and prints out an ALARA material
# defintion for each material (with densities from cell cards).
#
# input: MCNP input file, optional output file name
# output: ALARA material definations, without density specificed.
#
# python imports
import sys
import os
from optparse import OptionParser

# pyne imports
from pyne.material import Material
from pyne.material import MultiMaterial
from pyne.mcnp import read_mcnp_inp

def mats_to_alara(input, output):
    """This function reads in MCNP inp file and prints out an ALARA matlib"""

    mats = read_mcnp_inp(input)
    mat_count = 0  # number material objects
    multi_count = 0 # number of mulimaterial objects
    for mat in mats :
        if isinstance(mat, Material):
            mat.write_alara(output)
            mat_count += 1
        elif isinstance(mat, MultiMaterial):
            for submat in mat._mats:
                submat.write_alara(output)
                multi_count += 1

    print '{0} single density mats and {1} multi-density mats printed'\
        .format(mat_count, multi_count)
    

def main(arguments=None):
    parser = OptionParser(usage='%prog <mcnp_inp_file> [options]')
    parser.add_option('-o', dest='output', default='matlib.out',\
        help='Name of materials output file, default=%default')
    (opts, args) = parser.parse_args(arguments)

    if opts.output in os.listdir('.'):
        os.remove(opts.output)

    mats_to_alara(args[0], opts.output)

if __name__ == '__main__':
    # No arguments case -> print help output
    if len(sys.argv) == 1:
        sys.arv.append('-h')

    main()
