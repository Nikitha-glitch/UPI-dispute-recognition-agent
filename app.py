from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import os
from models import db, User, Transaction, Dispute
from agent import UPIDisputeAgent

app = Flask(__name__)

# Config
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret-key-12345' # Default for demo purposes
app.config['SECRET_KEY'] = 'flask-session-secret-key'

db.init_app(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# --- WEB ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# --- API ROUTES ---

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    phone = str(data.get('phone', '')).strip()
    mpin = str(data.get('mpin', '')).strip()

    if not all([name, email, phone, mpin]):
        return jsonify({"msg": "Missing required fields"}), 400

    if User.query.filter_by(phone=phone).first() or User.query.filter_by(email=email).first():
        return jsonify({"msg": "User with this phone or email already exists"}), 400

    hashed_mpin = bcrypt.generate_password_hash(mpin).decode('utf-8')
    new_user = User(name=name, email=email, phone=phone, mpin_hash=hashed_mpin)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"msg": "Registration successful"}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    phone = str(data.get('phone', '')).strip()
    mpin = str(data.get('mpin', '')).strip()

    user = User.query.filter_by(phone=phone).first()
    if user and bcrypt.check_password_hash(user.mpin_hash, mpin):
        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            "msg": "Login successful", 
            "access_token": access_token,
            "user": {"name": user.name, "phone": user.phone, "balance": user.balance}
        }), 200
    
    return jsonify({"msg": "Invalid phone number or MPIN"}), 401

@app.route('/api/user/balance', methods=['GET'])
@jwt_required()
def get_balance():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    return jsonify({"balance": user.balance}), 200

@app.route('/api/transaction/send', methods=['POST'])
@jwt_required()
def send_money():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    data = request.json
    amount = float(data.get('amount', 0))
    receiver_upi = data.get('receiver_upi')
    merchant_id = data.get('merchant_id', None)

    if amount <= 0 or not receiver_upi:
        return jsonify({"msg": "Invalid transaction details"}), 400

    if user.balance < amount:
        return jsonify({"msg": "Insufficient balance"}), 400

    # Simulate debiting the user
    user.balance -= amount

    # Create Transaction Record
    new_txn = Transaction(
        user_id=user.id,
        amount=amount,
        receiver_upi=receiver_upi,
        merchant_id=merchant_id,
        status='PENDING' # Will be resolved or set to SUCCESS normally
    )
    
    # Let's mock the initial status based on the exact amount rules
    if (amount % 5 == 0 or amount % 2 == 0) and amount != 0:
        new_txn.status = 'PENDING'
    else:
        new_txn.status = 'SUCCESS'
        
    # If success, don't revert. If failed or pending, we might need agent to resolve.
    db.session.add(new_txn)
    db.session.commit()

    return jsonify({
        "msg": "Transaction processed",
        "transaction_id": new_txn.id,
        "status": new_txn.status,
        "new_balance": user.balance
    }), 201

@app.route('/api/transaction/history', methods=['GET'])
@jwt_required()
def transaction_history():
    user_id = get_jwt_identity()
    transactions = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.timestamp.desc()).all()
    
    result = []
    for t in transactions:
        result.append({
            "id": t.id,
            "amount": t.amount,
            "receiver_upi": t.receiver_upi,
            "status": t.status,
            "timestamp": t.timestamp.isoformat()
        })
    return jsonify(result), 200

@app.route('/api/dispute/resolve', methods=['POST'])
@jwt_required()
def resolve_dispute():
    # User might not even be needed here if txn validation is strong, but good for security
    user_id = get_jwt_identity()
    data = request.json
    txn_id = data.get('transaction_id')
    txn_id = str(txn_id).strip() if txn_id else None

    if not txn_id:
        return jsonify({"msg": "Transaction ID is required"}), 400

    txn = Transaction.query.get(txn_id)
    if not txn:
        return jsonify({"msg": "Transaction not found"}), 404
        
    if str(txn.user_id) != str(user_id):
        return jsonify({"msg": "Unauthorized to access this transaction"}), 403

    # Instantiate the Agent mapping the transaction
    agent = UPIDisputeAgent(txn_id)
    result = agent.verify_and_resolve()

    return jsonify(result), 200

@app.route('/api/dispute/history', methods=['GET'])
@jwt_required()
def dispute_history():
    user_id = get_jwt_identity()
    
    # Get all disputes for transactions belonging to the user
    disputes = db.session.query(Dispute, Transaction).join(Transaction).filter(Transaction.user_id == user_id).order_by(Dispute.resolved_at.desc()).all()
    
    result = []
    for d, t in disputes:
        result.append({
            "transaction_id": d.transaction_id,
            "merchant_txn_id": d.merchant_txn_id,
            "receiver_txn_id": d.receiver_txn_id,
            "dispute_status": d.dispute_status,
            "original_amount": t.amount,
            "resolved_at": d.resolved_at.isoformat()
        })
        
    return jsonify(result), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
