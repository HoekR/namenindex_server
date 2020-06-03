#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 15 09:35:17 2019

@author: rikhoekstra
"""

from flask import Flask, Blueprint, request, abort, make_response, jsonify, g
from flask_restplus import Api, Resource
from flask_cors import CORS

from models.response_models import *
from models.error import InvalidUsage
from parse.headers_params import *
from models.name_store import NameStore
#from models.user_store import UserStore
from models.name import NaamError
from models.name_collection import NameCollection

from settings import server_config

app = Flask(__name__, static_url_path='', static_folder='public')
app.config['SECRET_KEY'] = "some combination of key words"
cors = CORS(app)
blueprint = Blueprint('api', __name__, url_prefix='/api')
api = Api(blueprint, doc="/docs")


#
name_store = NameStore()
#only public apis so no user management required!
#user_store = UserStore() 

def register_server():
    """moved this from main function as this seems to be skipped now"""
    name_store.configure_index(server_config["Elasticsearch"])
    



"""--------------- Error handling -----------------------"""
@api.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    return error.to_dict(), error.status_code

@api.errorhandler(NaamError)
def handle_Name_error(error):
    return error.to_dict(), error.status_code


"""--------------- endpoints ------------------"""


#api endpoint
@api.route("/", endpoint='api_base')
class BasicAPI(Resource):
    @api.doc('basic api access point for namenindex')
    @api.response(200, 'Success', name_response)
    @api.response(404, 'Nameindex Error')
    def get(self):
        """This is the namenindex server for searching names"""
        return {"message": "Nameindex server v0.1 online"}

  
#get name by id
@api.doc(params={'name_id': 'A Name ID'}, required=False)
@api.route("/names/<string:name_id>", endpoint='name_base')
class PersonNameAPI(Resource):

    @api.response(200, 'Success', name_response)
    @api.response(404, 'Name does not exist')
    def get(self, name_id):
#        params = get_params(request)
#        try:
        name = name_store.get_name_es(name_id)
        response_data = name
        return jsonify(response_data)

    def put(self):
        """not implemented"""
        pass

#@api.route("/collections", endpoint='collections')
# first prepare elasticsearch with a double index
#class CollectionAPI(Resource):
#
#    @api.response(200, 'Success', name_response)
#    @api.response(404, 'Collection does not exist')
#    def get(self, collection):
#        params={}
##        params['fieldname'] = 'collection'
#        params['searchterm'] = collection
##        try:
#        collection = name_store.get_collection_es(params)
#        response_data = collection
#        return jsonify(response_data)


#collection    
@api.doc(params={'collection': 'A Collection Name'}, required=False)
@api.route("/collections/<string:collection>", endpoint='collection')
class CollectionAPI(Resource):

    @api.response(200, 'Success', name_response)
    @api.response(404, 'Collection does not exist')
    def get(self, collection):
        params={}
#        params['fieldname'] = 'collection'
        params['searchterm'] = collection
#        try:
        collection = name_store.get_collection_es(params)
        response_data = collection
        return jsonify(response_data)



#search all
@api.doc(params={'search_term': 'search string in alle fields'}, required=False)
@api.route("/search/all/<string:search_term>", endpoint='search_all')
class AllSimpleSearchAPI(Resource):

    @api.response(200, 'Success', name_response)
    @api.response(404, 'No input?')
    def get(self, search_term=''):
        searchterm = search_term
        fieldname = '_all'
        body = name_store.simple(field=fieldname, condition=searchterm)
        name = name_store.query(index='namenindex',
                                doc_type='naam', 
                                body=body
                )
        response_data = name
        return jsonify(response_data)

#search all
@api.doc(params={'search_term': 'search string in alle fields'}, required=False)
@api.route("/search/all/source/<string:search_term>", endpoint='search_source_all')
class AllSimpleSearchAPI(Resource):

    @api.response(200, 'Success', name_response)
    @api.response(404, 'No input?')
    def get(self, search_term=''):
        searchterm = search_term
        fieldname = '_all'
        body = name_store.simple(field=fieldname, condition=searchterm)
        name = name_store.query(index='namenindex',
                                doc_type='naam', 
                                body=body,
                                sourcify=True
                )
        response_data = name
        return jsonify(response_data)


#search simple field
@api.doc(params={'search_field': 'field name',
                 'search_term': 'search string'}, required=False)
@api.route("/search/simple", endpoint='simple_search')
class PersonNameSimpleSearchAPI(Resource):

    @api.response(200, 'Success', name_response)
    @api.response(404, 'No input?')
    def get(self):
        params = get_params(request)
        
#        try:
        fieldname = params['filter']['field_name']
        searchterm = params['filter']['search_term']
        body = name_store.simple(field=fieldname, condition=searchterm)
        names = name_store.query(index='namenindex',
                                doc_type='naam', 
                                body=body
                )
        response_data = names #['hits']['hits']
        return jsonify(response_data)

#search simple field
@api.doc(params={'search_field': 'field name',
                 'search_term': 'search string'}, required=False)
@api.route("/search/source/simple", endpoint='simple_search_source')
class PersonNameSimpleSearchAPI(Resource):

    @api.response(200, 'Success', name_response)
    @api.response(404, 'No input?')
    def get(self):
        params = get_params(request)
        
#        try:
        fieldname = params['filter']['field_name']
        searchterm = params['filter']['search_term']
        body = name_store.simple(field=fieldname, condition=searchterm)
        names = name_store.query(index='namenindex',
                                doc_type='naam', 
                                body=body,
                                sourcify=True
                )
        response_data = names
        return jsonify(response_data)

app.register_blueprint(blueprint)
app.before_first_request(register_server)

if __name__ == "__main__":
    import os
    name_store.configure_index(server_config["Elasticsearch"])
#    user_store.configure_index(server_config["Elasticsearch"])
    app.run(port=int(os.environ.get("PORT", 3000)), debug=True, threaded=True)

