from flask import Flask, jsonify, request
import mysql.connector
import datetime
from config import DB_CONFIG

app = Flask(__name__)

# Database connection setup
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# Error handling
def handle_db_error(e):
    app.logger.error(f"Database error: {e}")
    return jsonify({"error": "An error occurred while processing your request."}), 500

# Database operations
def get_trails_by_location(location):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        query = "SELECT trail_id, name, difficulty, location, distance_km FROM trails WHERE location = %s"
        cursor.execute(query, (location,))
        trails = cursor.fetchall()
        db.close()
        return trails
    except mysql.connector.Error as e:
        return handle_db_error(e)

def save_favorite_trail(trail_id, rating, user_id):
    if rating < 1 or rating > 10:
        return jsonify({"error": "Rating must be between 1 and 10"}), 400
    try:
        db = get_db_connection()
        cursor = db.cursor()
        date_saved = datetime.datetime.now()
        query = "INSERT INTO favourite (user_id, trail_id, date_saved, rating) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (user_id, trail_id, date_saved, rating))
        db.commit()
        db.close()
    except mysql.connector.Error as e:
        return handle_db_error(e)

def get_trails_by_difficulty(difficulty):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        query = "SELECT trail_id, name, difficulty, location, distance_km FROM trails WHERE difficulty = %s"
        cursor.execute(query, (difficulty,))
        trails = cursor.fetchall()
        db.close()
        return trails
    except mysql.connector.Error as e:
        return handle_db_error(e)

def get_trails_by_amenities(amenities):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        query = """
            SELECT t.trail_id, t.name, t.difficulty, t.location, t.distance_km
            FROM trails t
            JOIN amenities a ON t.trail_id = a.trail_id
            WHERE a.name IN %s
            GROUP BY t.trail_id
            HAVING COUNT(DISTINCT a.name) >= 1
        """
        cursor.execute(query, (tuple(amenities),))
        trails = cursor.fetchall()
        db.close()
        return trails
    except mysql.connector.Error as e:
        return handle_db_error(e)

# API Endpoint 1: Requesting hiking recommendations based on location
@app.route('/trails/location', methods=['GET'])
def get_trails_by_location_endpoint():
    location = request.args.get('location')
    if not location:
        return jsonify({"error": "Location is required"}), 400
    trails = get_trails_by_location(location)
    return jsonify([{"trail_id": trail[0], "name": trail[1], "difficulty": trail[2], "location": trail[3], "distance_km": trail[4]} for trail in trails])

# API Endpoint 2: Saving favorite trails/rating trails
@app.route('/favorites', methods=['POST'])
def save_favorite_trail_endpoint():
    data = request.get_json()
    if not all(key in data for key in ('user_id', 'trail_id', 'rating')):
        return jsonify({"error": "Missing required fields"}), 400
    return save_favorite_trail(data['trail_id'], data['rating'], data['user_id'])

# API Endpoint 3: Retrieving trails based on difficulty of walk
@app.route('/trails/difficulty', methods=['GET'])
def get_trails_by_difficulty_endpoint():
    difficulty = request.args.get('difficulty')
    if not difficulty:
        return jsonify({"error": "Difficulty is required"}), 400
    trails = get_trails_by_difficulty(difficulty)
    return jsonify([{"trail_id": trail[0], "name": trail[1], "difficulty": trail[2], "location": trail[3], "distance_km": trail[4]} for trail in trails])

# API Endpoint 4: Retrieving trails based on required amenities
@app.route('/trails/amenities', methods=['GET'])
def get_trails_by_amenities_endpoint():
    amenities = request.args.getlist('amenities')
    if not amenities:
        return jsonify({"error": "Amenities are required"}), 400
    trails = get_trails_by_amenities(amenities)
    return jsonify([{"trail_id": trail[0], "name": trail[1], "difficulty": trail[2], "location": trail[3], "distance_km": trail[4]} for trail in trails])

if __name__ == '__main__':
    app.run(debug=True)