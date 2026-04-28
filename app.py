from flask import Flask, request, jsonify, render_template_string, redirect, url_for
import boto3, uuid
from markupsafe import escape
from boto3.dynamodb.conditions import Attr

app = Flask(__name__)
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('CommunityOrders')

# --- HTML TEMPLATES ---
BASE_STYLE = "<style>body{font-family:sans-serif; margin:40px;} table{width:100%; border-collapse:collapse;} th,td{padding:10px; border:1px solid #ddd; text-align:left;}</style>"

# 1. Customer Order Form
ORDER_PAGE = BASE_STYLE + """
    <h2>Place a New Order</h2>
    <form action="/order" method="post">
        Name: <input type="text" name="buyer" required><br><br>
        Item: <input type="text" name="item" required><br><br>
        Qty: <input type="number" name="qty" required><br><br>
        <button type="submit">Submit Order</button>
    </form>
    <br><a href="/status">Check My Order Status</a>
"""

# 2. Vendor Dashboard
DASHBOARD_PAGE = BASE_STYLE + """
    <h2>Vendor Dashboard - Pending Orders</h2>
    <table>
        <tr><th>ID</th><th>Buyer</th><th>Item</th><th>Qty</th><th>Action</th></tr>
        {% for order in orders %}
        <tr>
            <td>{{ order.order_id }}</td>
            <td>{{ order.buyer }}</td>
            <td>{{ order.item }}</td>
            <td>{{ order.qty }}</td>
            <td>
                <form action="/confirm" method="post">
                    <input type="hidden" name="order_id" value="{{ order.order_id }}">
                    Price: $<input type="number" step="0.01" name="price" required>
                    <button type="submit">Confirm & Set Price</button>
                </form>
            </td>
        </tr>
        {% endfor %}
    </table>
"""

# --- ROUTES ---

@app.route('/order', methods=['GET'])
def show_order_form():
    return render_template_string(ORDER_PAGE)

@app.route('/order', methods=['POST'])
def place_order():
    data = request.form
    order_id = str(uuid.uuid4())[:8] # Shorter ID for easy reading
    table.put_item(Item={
        'order_id': order_id,
        'buyer': escape(data.get('buyer')),
        'item': escape(data.get('item')),
        'qty': int(data.get('qty')),
        'price': 0,
        'status': 'PENDING'
    })
    return f"Order Submitted! Your ID is: <b>{order_id}</b>. <a href='/order'>Back</a>"

@app.route('/vendor')
def vendor_dashboard():
    # Only show PENDING orders
    response = table.scan(FilterExpression=Attr('status').eq('PENDING'))
    return render_template_string(DASHBOARD_PAGE, orders=response['Items'])

@app.route('/confirm', methods=['POST'])
def confirm_order():
    order_id = request.form.get('order_id')
    price = request.form.get('price')
    table.update_item(
        Key={'order_id': order_id},
        UpdateExpression="set #s=:s, price=:p",
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={':s': 'CONFIRMED', ':p': price}
    )
    return redirect(url_for('vendor_dashboard'))

@app.route('/status')
def check_status():
    response = table.scan() # In a real app, you'd filter by user
    orders = response['Items']
    output = BASE_STYLE + "<h2>Order Status</h2><table><tr><th>Item</th><th>Status</th><th>Price</th></tr>"
    for o in orders:
        price_display = f"${o['price']}" if o['status'] == 'CONFIRMED' else "TBD"
        output += f"<tr><td>{o['item']}</td><td>{o['status']}</td><td>{price_display}</td></tr>"
    return output + "</table><br><a href='/order'>New Order</a>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
