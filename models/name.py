#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  6 11:30:01 2019

@author: rikhoekstra
"""
class Name(object):
    def __init__(self, esobject):
        """create name object from single elasticsearch result
        """
        self.id = esobject['_id']
        try: 
            self._score = esobject['_score']
        except KeyError:
            self._score = 0
        self._type = esobject['_type']
        self._index = esobject['_index'] 
        src = esobject['_source']
        for item in src.items():
            setattr(self, item[0], item[1])
    
            
    def base(self):
        """json representation"""
        jsob = {"id": self.id,
                "provenance": self.collection,
                "fullname": self.fullname,
                "prepositie": self.prepositie or '',
                "firstname": self.voornaam or '',
                "intrapositie": self.intrapositie or '',
                "geslachtsnaam": self.geslachtsnaam or '',
                "by": self.by,
                "dy": self.dy,
                "bio": self.biography,
                "birth": self.birth or 0,
                "death": self.death or 0,
                "reference":self.reference,
                }
        return jsob

class NaamError(Exception):
    status_code = 400

    def __init__(self, message, status_code=400, payload=None):
        Exception.__init__(self)
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status_code'] = self.status_code
        return rv