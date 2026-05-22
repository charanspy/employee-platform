from flask import Flask, jsonify
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

EMPLOYEES = [
    {"id": 1, "name": "Alice", "department": "HR"},
    {"id": 2, "name": "Bob", "department": "IT"},
]

@app.route("/")
def root():
    return jsonify({
        "app": "Employee API",
        "env": os.getenv("ENV", "dev")
    })

@app.route("/employees")
def employees():
    return jsonify(EMPLOYEES)

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

@app.route("/info")
def info():
    return jsonify({
        "environment": os.getenv("ENV", "dev"),
        "team": os.getenv("TEAM", "Platform Engineering"),
        "version": "1.0"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)