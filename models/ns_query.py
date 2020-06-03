#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  6 11:29:09 2019

@author: rikhoekstra
"""
from elasticsearch import Elasticsearch
from queries import bool_should, bool_must 
es = Elasticsearch(timeout=30, max_retries=10, retry_on_timeout=True) 
index = "namenindex"
doc_type= "naam"

def get(index, doc_type, id):
    result = es.get(index=index, 
                    doc_type=doc_type,
                    id=id)
    return result

def simple(field, condition):
    body =  {"query": {"match": {field: condition}}}
    return body

def fuzzy(field, condition, fuzziness=2):
    """ from es docs:
    {
    "query": {
        "fuzzy" : {
            "user" : {
                "value": "ki",
                "boost": 1.0,
                "fuzziness": 2,
                "prefix_length": 0,
                "max_expansions": 100
                }
            }
        }
    }
            should we implement this???
    """
    {"query":
        {"fuzzy": {field:condition}}}
        
    

def qrange(field, condition):
    body = {"query":{}}
    return body
    
def query(index=index, 
          doc_type=doc_type, 
          body={}):
    query = {}
    query['index'] = index
    query['doc_type'] = doc_type
    results = es.search(index=index,
                        doc_type=doc_type,
                        body=body)
    return results