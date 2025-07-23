from flask import Flask, render_template, request, redirect, url_for
import sqlite3, json, os

app = Flask(__name__)

DB_NAME = 'bus_ticket_system.db'

# Initialize database (reset routes so all 11 are always loaded)
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_name TEXT,
                departure_time TEXT,
                price REAL,
                available_seats INTEGER
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT,
                email TEXT,
                phone TEXT,
                route_id INTEGER,
                passengers TEXT,
                date TEXT,
                total_price REAL,
                FOREIGN KEY(route_id) REFERENCES routes(id)
                )''')

    # Clear old routes and load fresh data
    c.execute("DELETE FROM routes")
    sample_routes = [
        ("Anantapur → Kadiri", "10:00 AM", 200, 50),
        ("Jaipur → Delhi", "08:00 AM", 550, 40),
        ("Jodhpur → Udaipur", "02:30 PM", 350, 35),
        ("Anantapur → Tirupati", "05:00 PM", 300, 60),
        ("Hyderabad → Warangal", "09:00 AM", 250, 45),
        ("Chennai → Delhi", "06:45 PM", 400, 50),
        ("Delhi → Jammu", "09:15 AM", 600, 30),
        ("Kota → Jaipur", "07:00 PM", 380, 45),
        ("Udaipur → Mount Abu", "03:20 PM", 480, 40),
        ("East godavari → Kakinada", "01:10 PM", 350, 60),
        ("Sikar → Jhunjhunu", "04:40 PM", 300, 55)
    ]
    c.executemany("INSERT INTO routes (route_name, departure_time, price, available_seats) VALUES (?,?,?,?)", sample_routes)

    conn.commit()
    conn.close()

init_db()

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Display routes
@app.route('/routes')
def show_routes():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM routes")
    routes = c.fetchall()
    conn.close()
    return render_template('routes.html', routes=routes)

# Booking page
@app.route('/book/<int:route_id>', methods=['GET', 'POST'])
def book_ticket(route_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM routes WHERE id=?", (route_id,))
    route = c.fetchone()
    conn.close()

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        journey_date = request.form['date']
        num_passengers = int(request.form['num_passengers'])

        passengers = []
        for i in range(1, num_passengers + 1):
            pname = request.form.get(f'passenger_name_{i}')
            page = request.form.get(f'passenger_age_{i}')
            passengers.append({"name": pname, "age": page})

        passengers_json = json.dumps(passengers)
        total_price = route[3] * num_passengers

        # Save booking
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""INSERT INTO bookings 
                    (user_name, email, phone, route_id, passengers, date, total_price)
                    VALUES (?,?,?,?,?,?,?)""",
                  (name, email, phone, route_id, passengers_json, journey_date, total_price))
        conn.commit()
        booking_id = c.lastrowid
        conn.close()

        return redirect(url_for('success', booking_id=booking_id))

    return render_template('book.html', route=route)

# Booking confirmation
@app.route('/success/<int:booking_id>')
def success(booking_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""SELECT b.id, b.user_name, b.email, b.phone, b.passengers, b.date, b.total_price,
                 r.route_name, r.departure_time 
                 FROM bookings b 
                 JOIN routes r ON b.route_id = r.id WHERE b.id=?""", (booking_id,))
    booking = c.fetchone()
    conn.close()

    passengers = json.loads(booking[4])
    return render_template('success.html', booking=booking, passengers=passengers)

# View all bookings (history)
@app.route('/history')
def history():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""SELECT b.id, b.user_name, b.email, b.phone, b.passengers, b.date, b.total_price,
                 r.route_name, r.departure_time 
                 FROM bookings b 
                 JOIN routes r ON b.route_id = r.id ORDER BY b.id DESC""")
    bookings = c.fetchall()
    conn.close()

    for i, booking in enumerate(bookings):
        bookings[i] = list(booking)
        bookings[i][4] = json.loads(booking[4])  # passengers
    return render_template('history.html', bookings=bookings)

if __name__ == '__main__':
    app.run(debug=True)
