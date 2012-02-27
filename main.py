'''
Created on Feb 15, 2012

@author: Geoff
'''
import sys

from lampost.mud import MudNature
from lampost.context import Context


if __name__ == "__main__":  
    port = 2500 if len(sys.argv) < 2 else int(sys.argv[1])
    Context(MudNature(), port).start()