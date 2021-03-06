from flask import Flask, jsonify, request, make_response
import json
import redis
import functools

app = Flask(__name__)
g_dbc = None


# get database connection
def getDBC():
    global g_dbc
    if g_dbc == None:
        g_dbc = redis.StrictRedis(host='db', port=6379, db=0)
    return g_dbc


# check header content-type
def content_type(content_type):
    def _content_type(function):
        @functools.wraps(function)
        def wrapper(*argv, **keywords):
            if request.headers.get("Content-Type") != content_type:
                error_message = {
                    "Error": "Invalid Content-Type."
                }
                return make_response(jsonify(error_message), 400)
            return function(*argv, **keywords)
        return wrapper
    return _content_type


# check header x-api-key
def require_apikey():
    def _require_apikey(function):
        @functools.wraps(function)
        def wrapper(*argv, **keywords):
            dbc = getDBC()
            # fetch apikey list
            apikeys = dbc.lrange("apikeys", 0, -1)
            # check api key.
            requestApikey = request.headers.get("x-api-key")
            if bytes(requestApikey.encode('utf-8')) not in apikeys:
                error_message = {
                    "Error": "Invalid api key."
                }
                return make_response(jsonify(error_message), 401)
            # add count
            keyCount = "count-" + requestApikey
            count = dbc.get(keyCount)
            if count == None:
                count = "0"
            count = int(count) + 1
            dbc.set(keyCount, str(count))
            return function(*argv, **keywords)
        return wrapper
    return _require_apikey


@app.route("/api/state", methods=['GET'])
@content_type('application/json')
@require_apikey()
def getState():
    # get state
    keyState = "state"
    dbc = getDBC()
    state = dbc.get(keyState)
    result = {
        "state": state.decode('utf-8')
    }
    return make_response(jsonify(result))


@app.route("/api/state", methods=['PUT'])
@content_type('application/json')
@require_apikey()
def putState():
    # set state
    requestData = json.loads(request.data)
    if "value" not in requestData:
        error = {
            "Error": "Invalid request parameters."
        }
        return make_response(jsonify(error), 400)
    keyState = "state"
    dbc = getDBC()
    dbc.set(keyState, requestData["value"])
    result = {
        "result": "OK"
    }
    return make_response(jsonify(result))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)


