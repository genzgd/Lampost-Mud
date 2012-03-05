'''
Created on Feb 15, 2012

@author: Geoff
'''
import sys

from lampost.mud import MudNature
from lampost.context import Context


if __name__ == "__main__":  
    port = 2500 if len(sys.argv) < 2 else int(sys.argv[1])
    db_num = 0 if len(sys.argv) < 3 else int(sys.argv[2])
    Context(MudNature(), port, db_num).start()