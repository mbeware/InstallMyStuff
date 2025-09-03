#!/usr/bin/python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass
import sys
import os
import re
import pprint
import json


class ListOfBlocks:
    Blocks = []

    def __init__( self):
        self.Blocks.append({})


    def add( self, block ):
        if block.Index in self.Blocks[0]:
            #remove block from ListOfBlocks
            del self.Blocks[0][block.Index]
        self.Blocks[0][block.Index] = block.Params 

    def dump( self ):
        return json.dumps( self.Blocks[0], indent=2 )
    

#----------------------------------------------------------------
class LogBlock:
    def __init__( self, ndx ):
        self.Index  = ndx
        self.Params = {}

    def add( self, infoType, key, val, trim=True ):
        if self.Params.get( infoType ) is None:
            self.Params[ infoType ] = {}
        if trim:
            val = val.strip(" ")
        self.Params[ infoType ][ key ] = val

    def addAll( self, infoType, keyVals ):
        for k,v in keyVals:
            self.add( infoType, k, v )

    def show( self ):
        pprint.pp( { 'Block[{}]'.format(self.Index): self.Params } )

    

#-------------------------------------------------------
def matchAnyPattern( patterns, line ):
    for Pat in patterns:
        Match = patterns[Pat].search( line )
        if Match:
            KeyVals = Match.groupdict() #.items()
            return Pat, KeyVals
    return None, None

#-------------------------------------------------------
# "python3-blinker:amd64 (1.4+dfsg1-0.4, automatic), libpolkit-agent-1-0:amd64 (0.105-33, automatic), ..."
#   NAME     = "python3-blinker"
#   ARCH     = "amd64"
#   VERSIONS = ["1.4+dfsg1-0.4", "automatic"]
#   ...
def extractListOfSofts( s, sep=',', trim=True ):
    Pat    = re.compile( r"(?P<NAME>[^:]*):(?P<ARCH>[^ ]*) \((?P<VERSIONS>[^\)]*)\)," )
    Pos    = 0
    Softs  = []

    # makes sure s ends with a comma ( , )
    s += ','

    while Pos < len(s):
        Match = Pat.match( s, Pos )
        if Match:
            GroupKV = Match.groupdict()
            KeyVals = {}

            # fixes VERSIONS value by splitting and cleaning-up the CSV
            for k,v in GroupKV.items():
                if k == 'VERSIONS':
                    Values = [s.strip() for s in v.split(',')]
                    KeyVals['VERSIONS'] = Values
                    if "automatic" in Values: 
                        KeyVals['AUTOMATIC'] = True
                    else:  
                        KeyVals['AUTOMATIC'] = False
                else:
                    KeyVals[k] = v

            Softs.append( KeyVals )
            Pos = Match.end(0)
        else:
            break
    return Softs

#----------------------------------------------------------------
# parses given log file
#----------------------------------------------------------------
def parseLogFile( filename ):
    errors   = []
    AllInstall = ListOfBlocks()

    _STATES  = [ 'NONE', 'IN_BLOCK', 'OUT_BLOCK' ]
    CurState = "NONE"
    Patterns = {}

    Patterns['START']   = re.compile( r"(?P<TAG>^Start-Date): (?P<DATE>.*) (?P<TIME>.*)" )
    Patterns['END']     = re.compile( r"(?P<TAG>^End-Date): (?P<DATE>.*) (?P<TIME>.*)" )
    Patterns['CMDLINE'] = re.compile( r"(?P<TAG>^Commandline): (?P<RAW>.*)" )
    Patterns['INSTALL'] = re.compile( r"(?P<TAG>^Install): (?P<RAW>.*)" )
    Patterns['REINSTALL'] = re.compile( r"(?P<TAG>^Reinstall): (?P<RAW>.*)" )
    Patterns['UPGRADE'] = re.compile( r"(?P<TAG>^Upgrade): (?P<RAW>.*)" )
    Patterns['PURGE']   = re.compile( r"(?P<TAG>^Purge): (?P<RAW>.*)" )
    Patterns['REQBY']   = re.compile( r"(?P<TAG>^Requested-By): (?P<USER>.*) \((?P<UID>.*)\)" )
    Patterns['REMOVE']  = re.compile( r"(?P<TAG>^Remove): (?P<RAW>.*)" )

    # Open the log file
    CurBlock = None
    BlockNdx = 0
    with open( filename, 'r' ) as file:
        for linenumber,line in (enumerate(file,1)):  #Start at line 1, because humans start counting at 1...
            line = line.strip( "\r\n\t " )
            if len(line) > 0:
                #print( "<<", CurState, ">>" )
                PatId, PatGroups = matchAnyPattern( Patterns, line )

                if CurState in ['NONE', 'OUT_BLOCK', 'ERROR']:
                    if PatId  == "START":
                        BlockNdx += 1
                        CurBlock = LogBlock( BlockNdx )
                        CurBlock.add('METADATA', 'LINENUMBER', str(linenumber))
                        CurBlock.add('METADATA', 'FILENAME', filename)
                        CurBlock.addAll( PatId, PatGroups.items() )
                        CurState = "IN_BLOCK"
                    elif CurState != 'ERROR':
                        errors.append(f"bad log entry at line {linenumber} of '{filename}'. Was expecting 'Start-Date:' but got '{line[12:]}'")
                        CurState = 'ERROR'

                elif CurState == 'IN_BLOCK':
                    if PatId == "END":
                        CurBlock.addAll( PatId, PatGroups.items() )
                        # CurBlock.show()
                        AllInstall.add( CurBlock )                        
                        CurState = "OUT_BLOCK"

                    elif PatId in ['INSTALL', 'UPGRADE', 'PURGE', 'REMOVE','REINSTALL']: 
                        Raw = PatGroups.get( 'RAW', [] )
                        Softs = extractListOfSofts( Raw )
                        CurBlock.add( PatId, 'SOFTWARES', Softs, trim=False )
                        
                    elif PatId in ["CMDLINE", "REQBY"]:
                        CurBlock.addAll( PatId, PatGroups.items() )
                    else:
                        errors.append(f"bad log entry at line {linenumber} of '{filename}'. '{line}'")
                        CurState = 'ERROR'
                        

    AllInstall.dump()

    if errors:
        for error in errors:
            print( error )


#----------------------------------------------------------------
# executes unit tests for this module
#----------------------------------------------------------------
def doUnitTests():
    Line = "python3-blinker:amd64 (1.4+dfsg1-0.4, automatic), libpolkit-agent-1-0:amd64 (0.105-33, automatic)"
    Pat    = re.compile( r"(?P<NAME>[^:]*):(?P<ARCH>[^ ]*) \((?P<VERSIONS>[^\)]*)\)," )
    Pos    = 0

    Line += ","

    while Pos < len(Line):
        Match = Pat.match( Line, Pos )
        if Match:
            GroupKV = Match.groupdict()
            for k,v in GroupKV.items():
                if k == 'VERSIONS':
                    Values = [s.strip() for s in v.split(',')]
                    pprint.pp( {k:Values} )
                else:
                    pprint.pp( {k:v} )
            Pos = Match.end(0)
        else:
            break


#----------------------------------------------------------------
# if module is called directly (not imported), it executes unit tests
#----------------------------------------------------------------
if __name__ == "__main__":
    # doUnitTests()
    parseLogFile('/home/mbeware/Documents/dev/InstallMyStuff/TestLogs/apt/history.merged.log')

 




# poloonsky
# I used the history.log.2 from your project and it parses it with nenni a hiccup !
# To test it out, replace the doUnitTests() at the bottom to call parseLogFile() with the file name directly (I use a main.py that uses the command line args) (edited)
# From this module, we can begin to put together a list of apps/libraries that are needed.
#   1) look for blocks containing an INSTALL item
#   2) out of this, you get the list of files ("SOFTWARES") that were install
#   3) look for blocks with a PURGE item and remove the indicated file from the list
#   4) if you find the same file in another block .... you must only keep the latest
#       ...or something like that
# Anyway, my goal was to thoroughly parse EVERY block to extract as much useful data as possible (ex: separate DATE & TIME, split the list of versions of a file, ...) 



