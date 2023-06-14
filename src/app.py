"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False


db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


MIGRATE = Migrate(app, db)

db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object


@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints


@app.route('/')
def sitemap():
    return generate_sitemap(app)


@app.route('/user/<user_id>', methods=['GET'])
def handle_hello(user_id=None):
    if request.method == "GET":
        print(type(user_id))
        if user_id is not None:
            user = User()
            user = user.query.get(user_id)

            if user is not None:
                return jsonify(user.serialize()), 200
            else:
                return jsonify({"message": "Not found"}), 404


@app.route('/user', methods=['GET'])
def all_users():
    if request.method == 'GET':
        users = User()
        users = users.query.all()
        users = list(map(lambda item: item.serialize(), users))
        return jsonify(users), 200


@app.route('/user', methods=['POST'])
def new_user():
    data = request.json
    if request.method == 'POST':
        if data.get("name") is None:
            return jsonify({"message": "wrong property"}), 400
        if data.get("lastname") is None:
            return jsonify({"message": "wrong property"}), 400
        if data.get("email") is None:
            return jsonify({"message": "wrong property"}), 400

        user = User()
        user_email = user.query.filter_by(email=data["email"]).first()

        if user_email is None:
            user = User(name=data["name"], lastname=data.get(
                "lastname"), email=data.get("email"))
            db.session.add(user)

            try:
                db.session.commit()
                return jsonify(data), 201
            except Exception as error:
                print(error)
                db.session.rollback()
                return jsonify({"message": f"error {error.args}"}), 500

        else:
            return jsonify({"message": "user exist"}), 400


@app.route('/user/<int:user_id>', methods=["PUT"])
def update_user(user_id=None):
    if request.method == "PUT":
        if user_id is None:
            return jsonify({"message": "wrong property"}), 400

        data = request.json
        if data.get("name") is None:
            return jsonify({"message": "wrong property"}), 400
        if data.get("lastname") is None:
            return jsonify({"message": "wrong property"}), 400

        data["name"] = data["name"].strip()

        if len(data["name"]) < 1:
            return jsonify({"message": "wrong property"}), 400
        if len(data["lastname"]) < 1:
            return jsonify({"message": "wrong property"}), 400

        user = User()
        update_user = user.query.get(user_id)

        if update_user is None:
            return jsonify({"message": "Not found"}), 404
        else:
            update_user.name = data["name"]
            update_user.lastname = data["lastname"]

            try:
                db.session.commit()
            except Exception as error:
                return jsonify({"message": f"error {error.args}"}), 500
        return jsonify(data), 201


@app.route("/user/<int:user_id>", methods=["DELETE"])
def delete_user(user_id=None):
    if request.method == "DELETE":
        if user_id is None:
            return jsonify({"message": "wrong property"}), 400

        user = User.query.get(user_id)
        if user is None:
            return jsonify({"message": "Not found"}), 404
        else:
            db.session.delete(user)

            try:
                db.session.commit()
                return jsonify([]), 204

            except Exception as error:
                return jsonify({"message": f"error {error.args}"}), 500


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
