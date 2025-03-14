from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import threading

app = Flask(__name__)

DATABASE = 'tax_payments.db'

def get_conn():
    conn = getattr(threading.current_thread(), '_database', None)
    if conn is None:
        conn = threading.current_thread()._database = sqlite3.connect(DATABASE)
    return conn

@app.teardown_appcontext
def close_connection(exception):
    conn = getattr(threading.current_thread(), '_database', None)
    if conn is not None:
        conn.close()

def create_table():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tax_payments (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 company TEXT NOT NULL,
                 amount REAL NOT NULL,
                 payment_date TEXT,
                 status TEXT DEFAULT 'Unpaid',
                 due_date TEXT NOT NULL
             )''')
    conn.commit()

create_table()  # Call to create the table if it doesn't exist

@app.route('/')
def index():
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM tax_payments')
    data = c.fetchall()
    print(data)
    return render_template('index.html', payments=data)

@app.route('/create', methods=['POST'])
def create():
    company = request.form['company']
    amount = request.form['amount']
    due_date = request.form['due_date']
    conn = get_conn()
    c = conn.cursor()
    c.execute('INSERT INTO tax_payments (company, amount, due_date) VALUES (?, ?, ?)', (company, amount, due_date))
    conn.commit()
    return redirect(url_for('index'))

@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    conn = get_conn()
    c = conn.cursor()
    company = request.form.get('company')  # Get form data, return None if not present
    amount = request.form.get('amount')
    due_date = request.form.get('due_date')
    status = request.form.get('status')
    
    # Retrieving existing data
    c.execute('SELECT * FROM tax_payments WHERE id = ?', (id,))
    og_data = c.fetchone()
    og_data = {
        'id': og_data[0],
        'company': og_data[1],
        'amount': og_data[2],
        'payment_date': og_data[3],
        'status': og_data[4],
        'due_date': og_data[5]
    }
    
    # Updating only if form data is provided, otherwise, keeping original values
    if company is not None:
        og_data['company'] = company
    if amount is not None:
        og_data['amount'] = amount
    if due_date is not None:
        og_data['due_date'] = due_date
    if status is not None:
        og_data['status'] = status
    
    #updating
    c.execute('''UPDATE tax_payments SET company = ?, amount = ?, due_date = ?, status = ? WHERE id = ?''',
                  (og_data['company'], og_data['amount'], og_data['due_date'], og_data['status'], id))
    conn.commit()
    return redirect(url_for('index'))


@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    conn = get_conn()
    c = conn.cursor()
    c.execute('DELETE FROM tax_payments WHERE id = ?', (id,))
    conn.commit()
    return redirect(url_for('index'))

@app.route('/api/filter', methods=['GET'])
def filter_payments():
    if request.method == 'GET':
        due_date = request.args.get('due_date')
        tax_rate_input = request.args.get('tax_rate')  # Get tax_rate as a string

        # Validating input data
        if not due_date:
            return jsonify({'error': 'Missing due_date parameter'}), 400

        try:
            # Converting tax_rate from string to float and validating range
            tax_rate = float(tax_rate_input)
            if tax_rate < 0 or tax_rate > 1:
                return jsonify({'error': 'Invalid tax_rate (must be between 0 and 1)'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid tax_rate format'}), 400

        # Converting tax_rate to percentage string
        tax_rate_percent = f"{tax_rate * 100:.2f}%"

        conn = get_conn()
        c = conn.cursor()

        # Filtering by due_date
        c.execute('SELECT * FROM tax_payments WHERE due_date = ?', (due_date,))
        data = c.fetchall()

        if not data:
            return jsonify({'message': 'No records found for the specified due date.'})

        # Calculating total amount, tax amount, and formating as floats
        total_amount = sum(row[2] for row in data)
        tax_amount = total_amount * tax_rate

        response = {
            'due_date': due_date,
            'tax_rate': tax_rate_percent,
            'total_amount': f"{total_amount:.2f}", 
            'tax_amount': f"{tax_amount:.2f}",
            'payments': data
        }

        return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
