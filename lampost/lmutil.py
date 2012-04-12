'''
Created on Apr 11, 2012

@author: Geoffrey
'''
def ljust(value, size):
    return value + (size - len(value)) * "&nbsp"