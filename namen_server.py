from flask import Flask, Blueprint, request, abort, make_response, jsonify, g
from flask_restplus import Api, Resource
from flask_httpauth import HTTPBasicAuth
from flask.ext.cors import CORS

from models.response_models import *
from models.error import InvalidUsage
from parse.headers_params import *
from models.name_store import NameStore
from models.user_store import UserStore
from models.name import NaamError
from models.name_collection import NameCollection

from settings import server_config

app = Flask(__name__, static_url_path='', static_folder='public')
app.config['SECRET_KEY'] = "some combination of key words"
cors = CORS(app)
#api = Api(app)
blueprint = Blueprint('api', __name__)
api = Api(blueprint)

#auth = HTTPBasicAuth()

name_store = NameStore()
user_store = UserStore()

#@api.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    return error.to_dict(), error.status_code

@api.errorhandler(NameError)
def handle_Name_error(error):
    return error.to_dict(), error.status_code

#@auth.verify_password
#def verify_password(token_or_username, password):
#    # anonymous access is allowed, set user to None
#    if not token_or_username and not password:
#        g.user = None # anonymous user
#        return True
#    # Non-anonymous access requires authentication
#    # First try to authenticate by token
#    g.user = user_store.verify_auth_token(token_or_username)
#    if g.user:
#        return True
#    if user_store.verify_user(token_or_username, password):
#        g.user = user_store.get_user(token_or_username)
#        return True
#    # non-anoymous user not verified -> return error 403
#    return False

#@auth.error_handler # handled by HTTPBasicAuth
#def unauthorized():
#    # return 403 instead of 401 to prevent browsers from displaying the default auth dialog
#    return make_response(jsonify({'message': 'Unauthorized access'}), 403)
#
#@api.errorhandler # handled by Flask restplus api
#def handle_unauthorized_api(error):
#    # return 403 instead of 401 to prevent browsers from displaying the default auth dialog
#    return {'message': 'Unauthorized access'}, 403


"""--------------- Name endpoints ------------------"""


@api.route("/api", endpoint='api_base')
class BasicAPI(Resource):

    @api.response(200, 'Success', name_collection_response)
    @api.response(404, 'Nameindex Error')
    def get(self):
        return {"message": "Nameindex server online"}

"""--------------- Name endpoints ------------------"""


@api.route("/api/names", endpoint='name_list')
class NamesAPI(Resource):

    # @auth.login_required # do we need to login??
    @api.response(200, 'Success', name_collection_response)
    @api.response(404, 'Name Error')
    def get(self):
        params = get_params(request)
        data = name_store.get_names_es(params)
        container = NameCollection(request.url, data["names"], total=data["total"])
        return container.view()

#    #@auth.login_required
#    @api.response(201, 'Success')
#    @api.response(404, 'Invalid Name Error')
#    @api.expect(name_model)
#    def post(self):
#        params = get_params(request, anon_allowed=False)
#        new_Name = request.get_json()
#        response = name_store.add_Name_es(new_Name, params=params)
#        return response, 201

@api.doc(params={'name_id': 'The Name ID'}, required=False)
@api.route('/api/names/<name_id>', endpoint='name')
class NameAPI(Resource):

    #@auth.login_required
    @api.response(200, 'Success', name_response)
    @api.response(404, 'Name does not exist')
    def get(self, name_id):
        params = get_params(request)
        try:
            Name = name_store.get_from_index_by_id(name_id, params)
        except PermissionError:
            abort(403)
        response_data = Name
        return response_data

    #@auth.login_required
    def put(self, name_id):
        params = get_params(request, anon_allowed=False)
        Name = request.get_json()
        response_data = name_store.update_Name_es(Name, params=params)
        return response_data

    #@auth.login_required
    def delete(self, Name_id):
        params = get_params(request, anon_allowed=False)
        response_data = name_store.remove_Name_es(Name_id, params)
        return response_data


"""--------------- Collection endpoints ------------------"""


@api.route("/api/collections")
class CollectionsAPI(Resource):

    #@auth.login_required
    def post(self):
        #prefer = interpret_header(request.headers)
        params = get_params(request, anon_allowed=False)
        collection_data = request.get_json()
        collection = name_store.create_collection_es(collection_data, params)
        container = NameContainer(request.url, collection, view=params["view"])
        return container.view(), 201

    #@auth.login_required
    def get(self):
        params = get_params(request)
        response_data = []
        collection_data = name_store.get_collections_es(params)
        for collection in collection_data["collections"]:
            container = NameContainer(request.url, collection, view=params["view"])
            response_data.append(container.view())
        return response_data

@api.route("/api/collections/<collection_id>")
class CollectionAPI(Resource):

    #@auth.login_required
    def get(self, collection_id):
        params = get_params(request)
        collection = name_store.get_collection_es(collection_id, params)
        if params["view"] == "PreferContainedDescriptions":
            collection["items"] = name_store.get_Names_by_id_es(collection["items"])
        container = NameContainer(request.url, collection, view=params["view"])
        return container.view()

    #@auth.login_required
    def put(self, collection_id):
        params = get_params(request, anon_allowed=False)
        collection_data = request.get_json()
        collection = name_store.update_collection_es(collection_data)
        container = NameContainer(request.url, collection, view=params["view"])
        return container.view()

    #@auth.login_required
    def delete(self, collection_id):
        params = get_params(request, anon_allowed=False)
        collection = name_store.remove_collection_es(collection_id, params)
        return collection

@api.route("/api/collections/<collection_id>/Names/")
class CollectionNamesAPI(Resource):

    #@auth.login_required
    @api.response(200, 'Success')
    @api.response(404, 'Invalid Name Error')
    @api.expect(name_model)
    def post(self, collection_id):
        params = get_params(request, anon_allowed=False)
        Name_data = request.get_json()
        if 'id' not in Name_data.keys():
            Name_data = name_store.add_Name_es(Name_data, params)
        collection = name_store.add_Name_to_collection_es(Name_data['id'], collection_id, params)
        container = NameContainer(request.url, collection, view=params["view"])
        return container.view()

    #@auth.login_required
    def get(self, collection_id):
        params = get_params(request)
        collection = name_store.get_collection_es(collection_id, params)
        container = NameContainer(request.url, collection.items, view=params["view"])
        return container.view()

@api.route("/api/collections/<collection_id>/Names/<Name_id>")
class CollectionNameAPI(Resource):

    #@auth.login_required
    def delete(self, collection_id, Name_id):
        params = get_params(request, anon_allowed=False)
        return name_store.remove_Name_from_collection_es(Name_id, collection_id, params)

@api.route("/api/users")
class UsersApi(Resource):

    @api.response(201, 'Success', user_response)
    @api.response(400, 'Invalid user data')
    def post(self):
        user_details = request.get_json()
        #if "username" not in user_details or "password" not in user_details:
        #    return {"message": "user data requires 'username' and 'password'"}, 400
        user = user_store.register_user(user_details["username"], user_details["password"])
        token = user_store.generate_auth_token(user.user_id, expiration=600)
        return {"action": "created",  "user": {"username": user.username, "token": token.decode('ascii')}}, 201

    #@auth.login_required
    @api.response(200, 'Success', user_response)
    @api.response(404, 'User does not exist')
    def put(self):
        user_details = request.get_json()
        if "new_password" not in user_details or "password" not in user_details:
            return {"message": "password update requires 'password' and 'new_password'"}, 400
        user = user_store.update_password(g.user.username, user_details["password"], user_details["new_password"])
        response = {"action": "updated", "user": user.json()}
        del response["user"]["password_hash"]
        return response, 200

    #@auth.login_required
    def delete(self):
        user_store.delete_user(g.user)
        return {}, 204

#@api.route("/api/login")
#class LoginApi(Resource):
#
#    #@auth.login_required
#    @api.response(200, 'Success', user_response)
#    @api.response(404, 'User does not exist')
#    def post(self):
#        if not g.user:
#            abort(403)
#        token = user_store.generate_auth_token(g.user.user_id, expiration=600)
#        return {"action": "verified", "user": {"username": g.user.username, "token": token.decode('ascii')}}, 200
#
#@api.route("/api/logout")
#class LogoutApi(Resource):
#
#    @auth.login_required
#    @api.response(200, 'Success', user_response)
#    @api.response(404, 'User does not exist')
#    def get(self):
#        # once token-based auth is implemented, remove token upon logout
#        return {"action": "logged out"}, 200

app.register_blueprint(blueprint)

if __name__ == "__main__":
    import os
    name_store.configure_index(server_config["Elasticsearch"])
    user_store.configure_index(server_config["Elasticsearch"])
    app.run(port=int(os.environ.get("PORT", 3000)), debug=True, threaded=True)

