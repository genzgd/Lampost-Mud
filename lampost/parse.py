'''
Created on Mar 18, 2012

@author: Geoff
'''
class KeyData():
    def __init__(self, value=None):
        self.count = 1
        self.values = []
        if value:
            self.values.append(value)