'''
Created on Apr 11, 2012

@author: Geoffrey
'''
def ljust(value, size):
    return value.ljust(size).replace(' ', '&nbsp;')
   
def pronouns(sex):
    if not sex or sex == 'none':
        return 'it', 'it', 'its', 'itself'
    if sex == "male":
        return 'he', 'him', 'his', 'himself'
    if sex == "female":
        return 'she', 'her', 'hers', 'herself'
