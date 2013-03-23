__author__ = 'Geoff'

master_attr = {'Brawn': {'con': 'Constitution', 'str': 'Strength', 'agi': 'Agility'},
               'Brain': {'int': 'Intelligence', 'wis': 'Wisdom', 'kno': 'Knowledge'},
               'Bravado': {'cha': 'Charm', 'bal': 'Balance', 'gui': 'Guile'}}

attr_dict = {}

[attr_dict.update(att_list) for att_list in master_attr.values()]

attr_list = tuple(attr_dict.keys())
