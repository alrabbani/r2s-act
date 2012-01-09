#!/usr/bin/env python 

######################################################################
#obj_phtn_src.py
######################################################################
# This python script defines an object that parses the photon source strength
#  output from ALARA.  
# The script supports command line calls, but is intended to be
#  used modularly by other scripts.
#
#
#
######################################################################

import textwrap as tw
import sys
from optparse import OptionParser

class PhtnSrcReader(object):
    """A new object of class PhtnSrcReader must be supplied the path of the file
     of interest.
    """
    
    def __init__(self, myInputFileName):
        """Init function for class PhtnSrcReader.
        """
        super(PhtnSrcReader, self).__init__()

        self.inputFileName = myInputFileName

        # stores a list of notes
        #self.notes = ['Notes for: ' + self.inputFileName]
        
    
    def read(self):
        """ Method opens and reads in lines and stores them in blocks on a 
        per-heading basis, e.g. headings are isotope identifiers or "TOTAL"
        """

        fr = open(self.inputFileName, 'r')
        
        self.headingList = list() # contains every line's list of isotope IDs
        self.coolingStepsList = list() # contains every line's list of cooling steps   
        self.probList = list() # contains every line's list of probabilities
        
        self.coolingSteps = list() # list of just the different cooling steps
        self.phtnList = list() # contains every line in string.split() form
        
        needCoolStepCnt = True

        # Read through the file...
        
        line = fr.readline()
        
        while(line != ''): # != EOF
            lineParts = line.split()
            
            self.phtnList.append(lineParts)
            
            # if list of the cooling steps in file is not complete yet...
            if needCoolStepCnt:
            # then we add next cooling step name
                # if we already started a list of cooling steps and shutdown
                if len(self.coolingSteps) and lineParts[1] == "shutdown": 
                        #alternately: == self.coolingSteps[0]:
                    needCoolStepCnt = False
                else:
                    if lineParts[1] != "shutdown":
                        # pull the next two pieces to make the cooling step identifier...
                        self.coolingSteps.append(lineParts[1:3])
                    else:
                        # pull the next piece which should be "shutdown"
                        self.coolingSteps.append(lineParts[1])
                
            self.headingList.append(lineParts[0])
            
            # handling the single string cooling step "shutdown"
            if lineParts[1] == "shutdown":
                self.coolingStepsList.append([lineParts[1]])
                self.probList.append(lineParts[2:])
            # or the two string cooling steps, e.g. "1 d"
            else:
                self.coolingStepsList.append(lineParts[1:3])
                self.probList.append(lineParts[3:])
                
            line = fr.readline() # read next line
        
        # return #what to return?
   

    def get_isotope(self, isotope="TOTAL"):
        """ACTION: Method searches headingList to find which entry in probList is
        the desired TOTAL, and returns the corresponding TOTAL block, which can 
        include multiple cooling steps.
        To get a specific cooling step's total, call isotope_source_strength
        REQUIRES: Method expects that read() has been successfully called.
        """
        
        meshcnt = -1

        # If the lists with headings and probabilities have contents...
        if len(self.headingList) and len(self.probList):
            self.totalHeadingList = list()
            self.totalProbList = list()
            self.totalCoolingStepsList = list()
            
            # Go through all entries in headingList
            for cnt, set in enumerate(self.headingList):
                
                # and save those that match the specified isotope.
                if set == isotope:
                   
                    # Look for entries with "shutdown" as cooling step. This
                    #  indicates the beginning of the entries for another mesh
                    #  cell.  When found, append empty list and increment
                    #  meshcnt.
                    if self.coolingStepsList[cnt] == ["shutdown"]:
                        self.totalHeadingList.append([])
                        self.totalProbList.append([])
                        self.totalCoolingStepsList.append([])
                        meshcnt += 1
                        
                    self.totalHeadingList[meshcnt].append(self.headingList[cnt])
                    self.totalProbList[meshcnt].append(self.probList[cnt])
                    self.totalCoolingStepsList[meshcnt].append(self.coolingStepsList[cnt])
                        
        else:
            print "totalsList or probList was empty. read() was probably not called"
        
        if len(self.totalHeadingList) == 0:
            print "{0} was not found in photon source." \
            "file.".format(isotope)
            
        else:
            return self.totalHeadingList
                
            
    def format_isotope_mcnp(self, coolingstep=0):
        """RETURNS: Method returns a formatted list of strings that is the block under
        heading TOTAL for some cooling step
        REQUIRES: Method expects that get_isotope() has been successfully called.
        If self.totalsList does not exist (e.g. get_total has not been called),
        the method quits.
        RECEIVES: If 'coolingstep' is specified, returns the block under TOTAL
        corresponding with the cooling step.
        """
        
        # if not len(self.totalsList):
            # print "object's variable 'totalsList' has not been set." \
            # " format_total_mcnp will now return ['0']"
            # return ['0']

        # try:
            # self.totalsList[coolingstep]
        # except:
            # print 'Cooling step', coolingstep, 'not found. Using last cooling step instead.'
            # coolingstep = len(self.totalsList) - 1

        grandTotal = [item for sublist in self.totalsList[coolingstep] for
                item in sublist]
        grandTotal = " ".join(grandTotal)

        # wrap is set up so that lines indent 5 spaces and wrap at 80 chars
        #  First line indents extra to make room for SI card.
        #  Resulting 'grandTotal' should copy/paste nicely into MCNP input deck.
        mcnpWrap = tw.TextWrapper()
        mcnpWrap.initial_indent = 7*' '
        mcnpWrap.subsequent_indent = 5*' '
        mcnpWrap.wdith = 80
        mcnpWrap.break_on_hyphens = False

        grandTotal = mcnpWrap.wrap(grandTotal)

        return grandTotal


    def isotope_source_strengths(self, coolingstep=0):
        """ACTION: Method parses all contents of self.totalProbList and creates a list of
        the sum of source strengths in each mesh cell, and a list of each mesh
        cell's list of source strengths at each energy.
        REQUIRES: Method expects that get_isotope() has been called already.
        NOTE that volume normalization of resulting list may
        be needed, depending on the mesh.
        RECEIVES: If 'coolingstep' is specified, returns the block under TOTAL
        corresponding with the cooling step.
        """
        
        # Not elegant... gen_sdef_probabilities needs to use the same coolingstep value.
        self.coolingstep = coolingstep
        
        self.meshprobs = list() # of lists of strings
        self.meshstrengths = list() # of floats

        # For each of these, sum the entries in the corresponding source
        # strengths block, and make a list of these sums (self.meshstrengths)
        if len(self.totalHeadingList) and len(self.totalProbList):

            for probset in self.totalProbList:
                #print set[coolingstep]
                #thistotal = [item for sublist in set[coolingstep] for item in sublist]
                
                self.meshprobs.append(probset[coolingstep])
                self.meshstrengths.append(sum([float(prob) for prob in probset[coolingstep]]))
                    
        else:
            print "headingList or probList was empty. read() was probably not called"

        return self.meshstrengths


    def gen_sdef_probabilities(self, meshform, outfile="phtn_sdef"):
        """REQUIRES: Method assumes that read() and isotope_source_strengths() have been
        called already.
        ACTION: Method creates a sequentially numbered listed of si and sp cards for
        MCNP input, using the energy structure specified (todo) and the photon
        source strength listed for each mesh cell.
        RECEIVES: Method receives a 3D list, meshform, of the form {{xmin,xmax,xintervals},{y...},{z...}}
        """

        try:
            nmesh = len(self.meshstrengths) + 1
        except:
            print "ERROR: total_source_strengths needs to be called before" \
                    "gen_sdef_probabilties"
            return [0]

        if nmesh > 994:
            print "ERROR: Too many mesh cells to create an SDEF card."
            return [0]
        
        # Shoddy placeholder for energy bins
        # Note that we replace the {0} with the .format method for each mesh cell.
        self.ergbins = "si{0} 0  1e-2  2e-2" \
          " 3e-2  4.5e-2  6e-2  7e-2  7.5e-2  1e-1  1.5e-1  2e-1  3e-1" \
          " 4e-1  4.5e-1  5.1e-1  5.12e-1  6e-1  7e-1  8e-1  1e0  1.33e0" \
          " 1.34e0  1.5e0  1.66e0  2e0  2.5e0  3e0  3.5e0" \
          " 4e0  4.5e0  5e0  5.5e0  6e0  6.5e0  7e0  7.5e0  8e0" \
          " 1e1  1.2e1  1.4e1  2e1  3e1  5e1"
        
        # calculate the mesh spacing in each direction
        xval = (meshform[0][1]-meshform[0][0])/float(meshform[0][2])/2
        yval = (meshform[1][1]-meshform[1][0])/float(meshform[1][2])/2
        zval = (meshform[2][1]-meshform[2][0])/float(meshform[2][2])/2
        
        cards=["sdef par=2 x=d996 y=d997 z=d998  erg ftr d999 tr=d995"]
        
        mcnpWrap = tw.TextWrapper()
        mcnpWrap.initial_indent = 0*' '
        mcnpWrap.subsequent_indent = 5*' '
        mcnpWrap.wdith = 80
        mcnpWrap.break_on_hyphens = False
        
        # create distribution for tr entries (point to transform cards)
        # SI card
        cards.extend(["c si995 - These are the mesh center coords"])
        card = ["si995 L"] # 
        card.extend([str(x) for x in range(1,nmesh)])
        card = " ".join(card)
        cards.extend(mcnpWrap.wrap(card))

        summeshstrengths = sum(self.meshstrengths)
        strnormmeshstrengths = \
                [str(x/summeshstrengths) for x in self.meshstrengths]
        
        # SP card
        card = ["sp995 D"] # D for discrete cummulative probabilities
        card.extend(strnormmeshstrengths)
        card = " ".join(card)
        cards.extend(mcnpWrap.wrap(card))
        
        # create distribution for X sampling
        # SI card
        cards.extend(["c si996 - x sampling"])
        card = ["si996 H"] # H for bin boundaries with continuous bin sampling.
        card.extend([str(-1*xval),str(xval)])
        card = " ".join(card)
        cards.extend(mcnpWrap.wrap(card))
        # SP card
        cards.append("sp996 D 0 1") # D for discrete cummulative probabilities
        
        # create distribution for Y sampling
        # SI card
        cards.extend(["c si997 - y sampling"])
        card = ["si997 H"] # H for bin boundaries.
        card.extend([str(-1*yval),str(yval)])
        card = " ".join(card)
        cards.extend(mcnpWrap.wrap(card))
        # SP card
        cards.append("sp997 D 0 1") # D for discrete cummulative probabilities
        
        # create distribution for Z sampling
        # SI card
        cards.extend(["c si998 - z sampling"])
        card = ["si998 H"] # H for bin boundaries.
        card.extend([str(-1*zval),str(zval)])
        card = " ".join(card)
        cards.extend(mcnpWrap.wrap(card))
        # SP card
        cards.append("sp998 D 0 1") # D for discrete cummulative probabilities

        # create dependent distribution for energy sampling
        cards.extend(["c ds999 - These are the sp/si numbers"])
        card = ["ds999 S"]
        card.extend([str(i) for i in range(1,nmesh)])
        card = " ".join(card)
        cards.extend(mcnpWrap.wrap(card))

        # iterate through each mesh cell, outputting the erg distributions
        for fakecnt, meshcells in enumerate(self.totalProbList):
            cnt = fakecnt + 1
            # sum up source strengths in mesh cell
            meshcell = (float(item) for item in meshcells[self.coolingstep])
            summeshstrengths = sum(meshcell)
           
            # We write fake probabilities if the mesh cell has no photon source
            #  strength.  This keeps MCNP from objecting.
            # Otherwiese we normalize and stringify the probability values.
            #~ Coding to exclude these cards would make this code more convoluted
            if summeshstrengths == 0:
                normmeshcell = [str(item + 1) for item in meshcell]
                cards.append("c  following distribution has zero photon source probability" \
                        + "\nc  however, non-zero bin probabilities keep MCNP happy.")
            else:
                # then normalize the source strengths in the mesh cell to total 1 (unnecessary...)
                normmeshcell = [str(x/summeshstrengths) for x in meshcell]
            
            # create the SI card
            card = self.ergbins.format(cnt)
            cards.extend(mcnpWrap.wrap(card))
            
            # create the SP card
            card = ["sp{0} 0".format(cnt)]
            card.extend(normmeshcell)
            card = " ".join(card)
            cards.extend(mcnpWrap.wrap(card))
            
        # create transform (TR) cards, 1 for each mesh cell.
        cnt = 0
        for x in range(meshform[0][2]):
            for y in range(meshform[1][2]):
                for z in range(meshform[2][2]):
                    cnt += 1
                    cards.append(" ".join( \
                            ["tr"+str(cnt), \
                            str(meshform[0][0]+xval+2*x*xval), \
                            str(meshform[1][0]+yval+2*y*yval), \
                            str(meshform[2][0]+zval+2*z*zval)]\
                            ))
        
        # write all cards to the outfile specified when function was called.
        fw = open(outfile, 'w')
        fw.writelines("\n".join(cards))
        fw.close()
        print "SDEF card has been generated in file '{0}'".format(outfile)
        print "Remember to update the imp:n to imp:p, as well as updating the \
                mode card."
        
        return


    def gen_gammas_file(self, meshform, outfile="gammas"):
        """ACTION: Method generates a file called 'gammas' to be used with a 
        modified version of MCNP5.
        REQUIRES: Method assumes that read() and isotope_source_strengths() 
        have been called already.
        RECEIVES:
        3D list, meshform, of the form {{xmin,xmax,xintervals},{y...},{z...}}
        """

        try:
            nmesh = len(self.meshstrengths) + 1
        except:
            print "ERROR: total_source_strengths needs to be called before" \
                    "gen_sdef_probabilties"
            return [0]

        # calculate the mesh spacing in each direction
        xval = (meshform[0][1]-meshform[0][0])/float(meshform[0][2])#/2
        yval = (meshform[1][1]-meshform[1][0])/float(meshform[1][2])#/2
        zval = (meshform[2][1]-meshform[2][0])/float(meshform[2][2])#/2

        fw = open(outfile, 'w')
        
        # write first line (intervals for x, y, z)
        fw.write(" ".join([str(x) for x in meshform]) + "\n")
        
        # create and write x coords line (2nd line)
        coords = [meshform[0][0]]
        for cnt in range(1, meshform[0][2]+1):
            coords.append(meshform[0][0]+cnt*xval)
        fw.write(" ".join([str(x) for x in coords]) + "\n")
        
        # create and write y coords line (3rd line)
        coords = [meshform[1][0]]
        for cnt in range(1, meshform[1][2]+1):
            coords.append(meshform[1][0]+cnt*yval)
        fw.write(" ".join([str(x) for x in coords]) + "\n")
        
        # create and write z coords line (4th line)
        coords = [meshform[2][0]]
        for cnt in range(1, meshform[2][2]+1):
            coords.append(meshform[2][0]+cnt*zval)
        fw.write(" ".join([str(x) for x in coords]) + "\n")

        # create and write 5th line (list of activated materials... ?????)
        fw.write(" ".join([str(x) for x in range(1,101)]) + "\n")

        # create and write lines for each mesh cell's gamma source strength
        # BUT first we must create a cummulative list of probabilities.
        for ergset in self.meshprobs:
            ergset_f = [float(erg) for erg in ergset]
            cummulative_ergset = list() # of strings
            preverg = 0.0
            for erg in ergset_f:
                ergsum = erg + preverg
                cummulative_ergset.append(ergsum)
                preverg = ergsum
            # The following list comprehension uses a format specifying output
            #  of 12 characters, with 5 values
            #  after the decimal point, using scientific notation.
            cummulative_ergset2 = ["{0:<12.5E}".format(x/cummulative_ergset[41]) \
                    for x in cummulative_ergset]
            fw.write("".join(cummulative_ergset2) + "\n") #~ trailing newline a problem?

        # all lines written, close file.
        fw.close()
        
        print "The file" + outfile + "was created successfully"

        return


    # DEPRECATED
    def read_pre_alara_2_9(self):
        """ DEPRECATED METHOD - Handles the earlier formatting of phtn_src file
        from ALARA.
        Method reads in lines and stores them in blocks on a per-heading basis
         e.g. headings are isotope identifiers or TOTAL
        This method handles the phtn_src format in ALARA prior to version 2.9
        """

        fr = open(self.inputFileName, 'r')

        line = fr.readline()
        
        hcnt = 0;
        pcnt = 1;
        
        self.headingList = []
        self.probList = []
        
        justReadAHeading = False
        wasBlank = False

        # Read through the file...
        # Events of interest:
        #  Blank lines signify either a new isotope, or a new set of probabilities
        #  Lines specifying isotopes are id'd by alphabetical characters
        #  Lines with photon source strengths are id'd by number
        
        while(line != ''): # != EOF
            lineParts = line.split()

            if len(lineParts) == 0:
                line = fr.readline()
                wasBlank = True
                continue
            
            if justReadAHeading:
                justReadAHeading = False
                
            if wasBlank and lineParts[0][0].isdigit():
                wasBlank = False
                self.probList[hcnt - 1].append([])
                pcnt += 1
                
            if lineParts[0][0].isalpha(): # check if first entry of line
                                            # starts with a letter
                justReadAHeading = True
                hcnt += 1
                pcnt = 1
                self.headingList.append(lineParts[0]) #~ storing a single string
                                                      #~ for consistency, use a list?
                self.probList.append([ [] ]) # empty list to hold lines.
                wasBlank = False
                
            else: # line is a list of numbers...
                
                self.probList[hcnt - 1][pcnt - 1].append(lineParts)
                
            line = fr.readline()
        
        # return #what to return?

    #END DEPRECATED
        

def main():
    """ACTION: Method defines an option parser and handles command-line
    usage of this module.
    REQUIRES: command line arguments to be passed - otherwise prints help
    information.
    RECEIVES: N/A
    """
    usage = "usage: %prog [options] arg"
    parser = OptionParser(usage)
    
    parser.add_option("-i","--input",action="store",dest="filename", \
            default="", help="photon source strengths are read from file")

    parser.add_option("-m","--mesh",action="store",dest="meshform", \
            default=(0,1,1,0,1,1,0,1,1),help="Needs a 9-valuelist, meshform, of the form " \
            "{xmin,xmax,xintervals,y...,z...} delimited by spaces.")
    parser.add_option("-s","--sdef",action="store_true",dest="sdef", \
            default=False, help="Will generate a file with the sdef" \
            "card and the si, sp, and tr cards for MCNP.  Needs mesh "\
            "info from -m.")
    parser.add_option("-g","--gammas",action="store_true",dest="gammas", \
            default=False,help="Will generate a 'gammas' file directly" \
            "from a phtn_src file for use by" \
            "modified versions of MCNP. Needs mesh info from -m.")
    parser.add_option("-H","--H5M",action="store_true",dest="h5m", \
            default=False,help="To be implemented...")

    (options, args) = parser.parse_args()

    # Print warning and then exit if no file was specified with -i/--input
    if options.filename == "":
        print "Methods in this module need a file name to begin. " \
                "Use the -i option."
        return

    exampleReader = PhtnSrcReader(options.filename)
    exampleReader.read()

    exampleReader.get_isotope()
    print "Cooling steps are:\n", exampleReader.coolingSteps, "\n"

    #Turn meshform list received into the 3D list used by other methods
    meshform3D = [ options.meshform[0::3], \
                options.meshform[3::6], \
                options.meshform[6::9] ]

    if options.sdef:
        print "sdef!"

    elif options.gammas:
        print "gammas!"
        exampleReader.gen_gammas(meshform3D)
    
    elif options.h5m:
        print ".h5m to 'gammas' file is not yet implemented."

if __name__=='__main__':
    main()
