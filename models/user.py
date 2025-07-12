from flask import Blueprint, request, jsonify
from models.user import User, db  # ✅ src. hata diya

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@user_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')

    if not username or not email:
        return jsonify({'error': 'Missing username or email'}), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({'error': 'User already exists'}), 409

    new_user = User(username=username, email=email)
    db.session.add(new_user)
    db.session.commit()

    return jsonify(new_user.to_dict()), 201
