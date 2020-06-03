import copy
import json
from models.name import Name, NaamError
from models.name_collection import NameCollection
from models.error import *
import models.queries as query_helper
import models.permissions as permissions
from elasticsearch import Elasticsearch
#from elasticsearch.exceptions import NotFoundError

"""This is an overhaul from Marijn's AnnotationStore, as it doesn't 
need much of its functionality, including the authentication part, as
the name index is meant to be consulted only

I also edited out the collections, though it might be useful to introduce
some sort of other collection at a later stage
"""

class NameStore(object):

    def __init__(self):
        """what should this do as we will only populate from es?"""
        pass

    def configure_index(self, configuration):
        self.es_config = configuration
        self.es_index = configuration['_index']
        self.es = Elasticsearch([{"host": self.es_config['host'], "port": self.es_config['port']}])
        if not self.es.indices.exists(index=self.es_index):
            self.es.indices.create(index=self.es_index)
        self.needs_refresh = False

    def index_needs_refresh(self):
        return self.needs_refresh

    def index_refresh(self):
        self.es.indices.refresh(index=self.es_index)
        self.needs_refresh = False

    def set_index_needs_refresh(self):
        self.needs_refresh = True

    def check_index_is_fresh(self):
        # check index is up to date, refresh if needed
        if self.index_needs_refresh():
            self.index_refresh()

    def get_name_es(self, name_id, params):
        if "action" not in params:
            params["action"] = "see"
        if "username" not in params:
            params["username"] = None
        # get Name from index
        Name = self.get_from_index(name_id,
                                   action=params["action"],
                                   name_type="naam")
        return Name.to_clean_json(params)

    def get_names_es(self, params):
        # check index is up to date, refresh if needed
        self.check_index_is_fresh()
        response = self.get_from_index_by_filters(params, name_type="naam")
        Names = [Name(hit) for hit in response["hits"]["hits"]]
        return {
            "total": response["hits"]["total"],
            "names": [Name.base() for Name in Names]
        }

    def get_names_by_id_es(self, name_ids, params):
        # check index is up to date, refresh if needed
        self.check_index_is_fresh()
        response = self.es.mget(index=self.es_index, doc_type="Name", body={"ids": name_ids})
        return [hit["_source"] for hit in response["hits"]["hits"]]

#    def get_collection_es(self, collection_id, params):
#        if "action" not in params:
#            params["action"] = "see"
#        if "username" not in params:
#            params["username"] = None
#        return collection.to_clean_json(params)

#    def get_collections_es(self, params):
#        # check index is up to date, refresh if needed
#        self.check_index_is_fresh()
#        response = self.get_from_index_by_filters(params, name_type="NameCollection")
#        collections = NameCollection(response["hits"]["hits"])
#        return {
#            "total": response["hits"]["total"],
#            "collections": collection.to_clean_json(params)
#        }



    ####################
    # Helper functions #
    ####################
    """old helpers were superfluous, but we may add some similarity stuff here later """


    ###################
    # ES interactions #
    ###################

    """all adding stuff is delegated to helpers as we do not foresee writing interactions
    with the index as yet. Keep as placeholders though"""
    
    #    def add_to_index(self, Name, name_type):
    #        self.should_have_target_list(Name)
    #        self.should_have_permissions(Name)
    #        self.should_not_exist(Name['id'], name_type)
    #        return self.es.index(index=self.es_index, doc_type=name_type, id=Name['id'], body=Name)
    #
    #    def add_bulk_to_index(self, Names, name_type):
    #        raise ValueError("Function not yet implemented")
    
    #    def get_from_index(self, id, action, name_type="naam"):
    #        """for now we only have naam, but probably extend with institution
    #        and geonames later
    #        """
    #        # check index is up to date, refresh if needed
    #        self.check_index_is_fresh()
    #        # check that Name exists (and is not deleted)
    #        self.should_exist(id, name_type)
    #        return Name

    def get_from_index_by_id(self, name_id, name_type="naam"):
        self.should_exist(name_id, name_type)
        return self.es.get(index=self.es_index, doc_type=name_type, id=name_id)['_source']

    def get_from_index_by_filters(self, params, name_type="naam"):
        filter_queries = query_helper.make_param_filter_queries(params)
#        filter_queries += [query_helper.make_permission_see_query(params)]
        query = {
            "from": params["page"] * self.es_config["page_size"],
            "size": self.es_config["page_size"],
            "query": query_helper.bool_must(filter_queries)
        }
        return self.es.search(index=self.es_index, doc_type=name_type, body=query)



#    def remove_from_index(self, name_id, name_type):
#        self.should_exist(name_id, name_type)
#        return self.es.delete(index=self.es_index, doc_type=name_type, id=name_id)

#    def remove_from_index_if_allowed(self, name_id, params, name_type="_all"):
#        if "username" not in params:
#            params["username"] = None
#        # check index is up to date, refresh if needed
#        self.check_index_is_fresh()
#        # check that Name exists (and is not deleted)
#        self.should_exist(name_id, name_type)
#        # get original Name json
#        name_json = self.get_from_index_by_id(name_id, name_type)
#        # check if user has appropriate permissions
#        if not permissions.is_allowed_action(params["username"], "edit", Name(name_json)):
#            raise PermissionError(message="Unauthorized access - no permission to {a} Name".format(a=params["action"]))
#        return self.remove_from_index(name_id, "Name")
#
#    def is_deleted(self, name_id, name_type="_all"):
#        if self.es.exists(index=self.es_index, doc_type=name_type, id=name_id):
#            res = self.es.get(index=self.es_index, doc_type=name_type, id=name_id)
#            if "status" in res["_source"] and res["_source"]["status"] == "deleted":
#                return True
#        return False

    def should_exist(self, name_id, name_type="_all"):
        if self.es.exists(index=self.es_index, doc_type=name_type, id=name_id):
            if not self.is_deleted(name_id, name_type):
                return True
        raise NaamError(message="Name with id %s does not exist" % (name_id), status_code=404)

    def should_not_exist(self, name_id, name_type="_all"):
        if self.es.exists(index=self.es_index, doc_type=name_type, id=name_id):
            raise NaamError(message="Name with id %s already exists" % (name_id))
        else:
            return True

    def get_objects_from_hits(self, hits, doc_type="naam"):
        objects = []
        for hit in hits:
            if hit["_source"]["type"] == doc_type:
                objects += [Name(hit)]
#            elif hit["_source"]["type"] == "NameCollection":
#                objects += [NameCollection(hit["_source"])]



    def list_name_ids(self):
        return list(self.name_index.keys())

    def list_Names(self, ids=None):
        if not ids:
            ids = self.list_name_ids()
        return [Name for id, Name in self.name_index.items() if id in ids]

    def list_Names_as_json(self, ids=None):
        if not ids:
            ids = self.list_name_ids()
        return [Name.to_json() for id, Name in self.name_index.items() if id in ids]

#    def load_Names_es(self, Names_file):
#        with open(Names_file, 'r') as fh:
#            data = json.loads(fh.read())
#        for Name in data['Names']:
#            try:
#                self.add_name_es(Name)
#            except NaamError:
#                pass
#        for collection in data['collections']:
#            try:
#                self.create_collection_es(collection)
#            except NaamError:
#                pass




