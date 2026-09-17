"""
Vercel Serverless Function & Flask API Entrypoint for AirResolve.
Exposes endpoints for customer data, flight retrieval, and deterministic policy resolution.
"""

import os
import sys

# Ensure root directory is on Python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from flask import Flask, jsonify, request, send_from_directory
from agent.orchestrator import ResolutionAgent
from policy.policy_engine import PolicyEngine

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, "public"))
agent = ResolutionAgent(data_dir=os.path.join(BASE_DIR, "data"))
policy_engine = agent.policy_engine


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "AirResolve Policy Engine",
        "system_date": "2026-09-23",
        "version": "1.0.0"
    })


@app.route("/api/customers", methods=["GET"])
def get_customers():
    """Returns list of all customers and their primary flight disruption data."""
    customers_dict = policy_engine.customers_data.get("customers", {})
    bookings_dict = policy_engine.bookings_data.get("bookings", {})

    result = []
    for pnr, cust in customers_dict.items():
        booking = bookings_dict.get(pnr, {})
        segment = policy_engine.get_primary_segment(booking)
        result.append({
            "pnr": pnr,
            "name": cust.get("name"),
            "loyalty_tier": cust.get("loyalty_tier"),
            "contact": cust.get("contact"),
            "travel_history": cust.get("travel_history_last_12m"),
            "flight": segment,
        })
    return jsonify({"customers": result})


@app.route("/api/booking/<pnr>", methods=["GET"])
def get_booking(pnr):
    """Retrieve verified booking and customer profile for a specific PNR."""
    customer = policy_engine.get_customer(pnr)
    if not customer:
        return jsonify({"error": "Customer not found", "pnr": pnr}), 404

    booking = policy_engine.get_booking(customer.get("booking_reference"))
    segment = policy_engine.get_primary_segment(booking)

    return jsonify({
        "customer": customer,
        "booking": booking,
        "primary_segment": segment
    })


@app.route("/api/chat", methods=["POST"])
def chat():
    """Process a message through the deterministic resolution orchestrator."""
    data = request.get_json(force=True, silent=True) or {}
    message = data.get("message", "").strip()
    pnr = data.get("pnr", "SK4821X").strip()

    if not message:
        return jsonify({"error": "Message parameter is required"}), 400

    response = agent.process_message(
        message=message,
        active_customer_id_or_pnr=pnr,
    )

    return jsonify(response.to_dict())


# Serve static web frontend when deployed or run locally
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    public_dir = os.path.join(BASE_DIR, "public")
    if path != "" and os.path.exists(os.path.join(public_dir, path)):
        return send_from_directory(public_dir, path)
    return send_from_directory(public_dir, "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting AirResolve API server on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
