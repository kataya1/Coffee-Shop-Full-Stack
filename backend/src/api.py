import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks}\
         where drinks is the list of drinks]
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks')
def get_drinks():
    try:
        drinks = Drink.query.order_by(Drink.id).all()
        # checks if drinks is not None and make sure it returns an array
        drinks_array = [d.short() for d in drinks] if drinks else []
        return jsonify({
            "success": True,
            "drinks": drinks_array
        }), 200

    except Exception:
        abort(422)


'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks}\
         where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks-detail')
@requires_auth(permission='get:drinks-detail')
def get_detailed_drinks():
    try:
        drinks = Drink.query.order_by(Drink.id).all()
        return jsonify({
            "success": True,
            "drinks": [drink.long() for drink in drinks]
        }), 200
    except Exception as e:
        print(e)
        abort(422)


'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink}\
         where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks', methods=['POST'])
@requires_auth(permission='post:drinks')
def create_drink():
    body = request.get_json()
    if body is None or body == {}:
        abort(400)
    try:
        # some error in test where the test sends dict and not list
        #  (fixing it here just in case it sends dict for single ingrediend)
        recipe = body.get('recipe')
        if type(recipe) is not list:
            recipe = [recipe, ]
        recipe = json.dumps(recipe)
        new_drink = Drink(title=body.get('title'), recipe=recipe)
        new_drink.insert()
        return jsonify({
            "success": True,
            "drinks": [new_drink.long(), ]
        }), 200

    except Exception as e:
        print(f"error: {e}")
        abort(422)


'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where
    drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''

# i liked this allot, it's forign to me never seen it before so i copied it
# source: https://gist.github.com/mattupstate/d63caa0156b3d2bdfcdb
# requirements.txt was updated accordingly (import jsonpatch)
# nvm not working
""" def patch(instance, **kwargs):
    # Create the patch object
    patch = JsonPatch(request.get_json())
    # Get a dictionary instance of the model instance
    data = instance.asdict(exclude_pk=True, **kwargs)
    # Apply the patch to the  dictionary instance of the model
    data = patch.apply(data)
    # Apply the patched dictionary back to the model
    instance.fromdict(data) """


@app.route('/drinks/<id>', methods=['PATCH'])
@requires_auth(permission='patch:drinks')
def update_drinks(id):
    drink = Drink().query.get_or_404(id)
    try:
        body = request.get_json()
        print(body)
        # if it's body.get('attribute'') is none it defaults to the original
        #  value
        # but if it has attribute as a proberty of python or, it chooses the
        #  first one if both are true
        drink.title = body.get('title', None) or drink.title
        drink.recipe = body.get('recipe', None) or drink.recipe
        drink.update()
        return jsonify({
            "success": True,
            "drinks": [drink.long(), ]
        }), 200
    except Exception as e:
        print(e)
        abort(422)


'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id}
     where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<id>', methods=['DELETE'])
@requires_auth(permission='delete:drinks')
def delete_drink(id):
    drink = Drink().query.get_or_404(id)
    try:
        drink.delete()
        return jsonify({
            "success": True,
            "drinks": id
        }), 200
    except Exception as e:
        print(e)
        abort(422)


# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''
'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''


def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "not found"
    }), 404


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''

# source https://knowledge.udacity.com/questions/97965


@app.errorhandler(AuthError)
def autherror(error):
    error_details = error.error
    error_status_code = error.status_code
    return jsonify({
        'success': False,
        'error': error_status_code,
        'message': f"{error_details['code']}: {error_details['description']}"
    }), error_status_code
