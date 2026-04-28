import uuid, boto3, os
from flask import Flask, request, jsonify
from markupsafe import escape 

app = Flask(__name__)

# Initialize AWS DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')
table = dynamodb.Table('CommunityOrders')

@app.route('/order', methods=['POST'])
def place_order():
    data = request.json
    # OWASP V5: Input Validation
    if not data or 'item' not in data or 'qty' not in data:
        return jsonify({"error": "Bad Request: Missing item or qty"}), 400
    
    order_id = str(uuid.uuid4())
    table.put_item(Item={
        'order_id': order_id,
        'buyer': escape(data.get('buyer', 'Guest')), # Sanitize input
        'item': escape(data['item']),                # Sanitize input
        'qty': int(data['qty']),                     # Type-cast to prevent injection
        'status': 'PENDING'
    })
    return jsonify({"order_id": order_id, "status": "PENDING"}), 201

if __name__ == "__main__":
    # OWASP A05: Security Misconfiguration (Debug must be False)
    app.run(host='0.0.0.0', port=5000, debug=False)
