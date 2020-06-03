#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  6 16:04:12 2019

@author: rikhoekstra
"""
from flask import jsonify
from models.name import Name, NaamError


class NameCollection(object):
    def __init__(self, resultlist, total=0, page_size=20): 
        self.container = []
        results = resultlist['hits']['hits']
        for result in results:
            self.container.append(Name(result))
        self.set_page_size(page_size)
            
    def view_page(self, page=0):
        if not isinstance(page, int) or page < 0:
            raise NaamError(message="Parameter page must be non-negative integer")
        return self.add_page_tems(page)

    def add_page_items(self, page_num):
        startIndex = self.page_size * page_num
        items = self.items[startIndex: startIndex + self.page_size]
        if self.iris:
            if isinstance(items[0], str):
                return items
            else:
                return [item["id"] for item in items]
        else:
            return [item for item in items]

    def listjson(self):
        """make json representation of items"""
        out = jsonify([n.base() for n in self.container]) 
        return out
    
    def set_page_size(self, page_size):
        if type(page_size) != int or page_size < 1:
            raise NaamError(message='page_size must be a positive integer value')
        self.page_size = page_size
    
    def __len__(self):
        return len(self.container)
    
    def __iter__(self):
        return(iter(self.container))
            