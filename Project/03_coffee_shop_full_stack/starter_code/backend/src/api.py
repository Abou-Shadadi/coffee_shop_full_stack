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
!! Running this funciton will add one
'''
# db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['GET'])
def get_drinks(): 
    try: 
        result={
        'success': True,
        'drinks': [drinks.short() for drinks in Drink.query.all()]
        }

        return jsonify(result, 200)
    except:
        abort(500, error_message='Error occured while getting drink details, Please try again later!') # Internal server error    

'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
 
@app.route("/drinks-detail")
@requires_auth("get:drinks-detail")
def get_drink_details_long(jwt):
    try:
        drinks = [drink_detail.long() for drink_detail in Drink.query.all()]
    except AuthError as e:
        abort(e)
    except:
         abort(500, error_message='Error occured while getting drink details, Please try again later!') # Internal server error    
    return jsonify(success=True, drinks=drinks)

'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drinks(payload):
# validations for input fields  
    if not 'title' in request.get_json(): # validate if the title field is empty
        abort(400, error_message='title field is required')

    if not 'recipe' in request.get_json():  # validate if the recipe field is empty
        abort(400, error_message='recipe field is required')

    try:
        drink_data = Drink(
        title=request.get_json().get('title'),
        recipe=json.dumps([request.get_json().get('recipe')])) # serialize formatted string
        return jsonify({'success': True, 'drinks': [drink_data.long()]}), 200
    except:
        abort(400, error_message='title must be unique')
  

'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drinks(id):
    drink_row = Drink.query.get(id)
    if not drink_row:
        abort(404, error_message='Drink was not found, Please try again later!')

    if 'title' in request.get_json():  # update only if the title field is not empty
        drink_row.title = request.get_json().get('title')
    else:
        abort(400, error_message='title is required')
    if 'recipe' in request.get_json(): # update only if the recip field is not empty
        drink_row.recipe = [json.dumps(request.get_json().get('recipe'))]
    try:
        drink_row.update()
    except:
        abort(400, error_message='title must be unique')

    return jsonify({'success': True, 'drinks': [drink_row.long()]}), 200

'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(id):
    # #? i added a return statement to "delete method" in models.py
    # #? to make sure the right resource is deleted :)
    try:
        drink_row = Drink.query.get(id)
        if drink_row:
            delete_query=drink_row.delete()
            return jsonify({
            'success': True,
            'delete': id
            }), 200
        abort(404, error_message='Drink not found, Please tr again later!') # not found     
    except:
            abort(500, error_message='Error occured while getting drink details, Please try again later!') # internal server error  

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
@app.errorhandler(400)
def unprocessable(error_detail):
    return jsonify({
        "success": False,
        "error": 400,
        "message": error_detail.error_message
    }), 400
'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''
@app.errorhandler(404)
def unprocessable(error_detail):
    return jsonify({
        "success": False,
        "error": 404,
        "message": error_detail.error_message
    }), 404


@app.errorhandler(500)
def unprocessable(error_detail):
    return jsonify({
        "success": False,
        "error": 500,
        "message": error_detail.error_message
    }), 500    


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''

@app.errorhandler(AuthError)
def unprocessable(error_detail):
    return jsonify({
        "success": False,
        "error": error_detail.status_code,
        "message": error_detail.error.get('error_message'),
    }), error_detail.status_code