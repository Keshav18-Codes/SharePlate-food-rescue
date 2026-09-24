"""
routes/volunteer.py
Volunteer (Delivery) module -- only relevant when an NGO chose
"Request Delivery" instead of self-pickup. Simple 2D pages:
a booking page and a delivery-done page.
"""
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash

from db import query
from helpers import role_required, get_current_user

volunteer_bp = Blueprint("volunteer", __name__, url_prefix="/volunteer")


@volunteer_bp.route("/dashboard")
@role_required("volunteer")
def dashboard():
    user = get_current_user()

    open_requests = query(
        """
        SELECT d.id AS delivery_id, d.status, l.title, l.quantity, l.unit,
               up.name AS provider_name, up.address AS provider_address,
               un.name AS ngo_name, un.address AS ngo_address
        FROM deliveries d
        JOIN claims c ON c.id = d.claim_id
        JOIN listings l ON l.id = c.listing_id
        JOIN users up ON up.id = l.provider_id
        JOIN users un ON un.id = c.ngo_id
        WHERE d.status = 'requested'
        ORDER BY d.id DESC
        """,
        fetchall=True,
    )

    my_deliveries = query(
        """
        SELECT d.id AS delivery_id, d.status, l.title, l.quantity, l.unit,
               up.name AS provider_name, up.address AS provider_address,
               un.name AS ngo_name, un.address AS ngo_address
        FROM deliveries d
        JOIN claims c ON c.id = d.claim_id
        JOIN listings l ON l.id = c.listing_id
        JOIN users up ON up.id = l.provider_id
        JOIN users un ON un.id = c.ngo_id
        WHERE d.volunteer_id = %s
        ORDER BY d.id DESC
        """,
        (user["id"],),
        fetchall=True,
    )

    return render_template("volunteer_dashboard.html", open_requests=open_requests, my_deliveries=my_deliveries)


@volunteer_bp.route("/book/<int:delivery_id>", methods=["POST"])
@role_required("volunteer")
def book(delivery_id):
    user = get_current_user()

    updated = query(
        """
        UPDATE deliveries
        SET volunteer_id = %s, status = 'booked', booked_at = %s
        WHERE id = %s AND status = 'requested'
        RETURNING id
        """,
        (user["id"], datetime.utcnow(), delivery_id),
        fetchone=True,
        commit=True,
    )

    if not updated:
        flash("That delivery was already booked by someone else.", "error")
        return redirect(url_for("volunteer.dashboard"))

    return redirect(url_for("volunteer.booking", delivery_id=delivery_id))


@volunteer_bp.route("/booking/<int:delivery_id>")
@role_required("volunteer")
def booking(delivery_id):
    """Fixed demo booking confirmation page."""
    user = get_current_user()
    delivery_row = query(
        """
        SELECT d.id AS delivery_id, d.status, l.title, l.quantity, l.unit,
               up.name AS provider_name, up.address AS provider_address, up.phone AS provider_phone,
               un.name AS ngo_name, un.address AS ngo_address, un.phone AS ngo_phone
        FROM deliveries d
        JOIN claims c ON c.id = d.claim_id
        JOIN listings l ON l.id = c.listing_id
        JOIN users up ON up.id = l.provider_id
        JOIN users un ON un.id = c.ngo_id
        WHERE d.id = %s AND d.volunteer_id = %s
        """,
        (delivery_id, user["id"]),
        fetchone=True,
    )
    if not delivery_row:
        flash("Booking not found.", "error")
        return redirect(url_for("volunteer.dashboard"))

    return render_template("volunteer_booking.html", delivery=delivery_row)


@volunteer_bp.route("/deliver/<int:delivery_id>", methods=["POST"])
@role_required("volunteer")
def mark_delivered(delivery_id):
    user = get_current_user()

    updated = query(
        """
        UPDATE deliveries
        SET status = 'delivered', delivered_at = %s
        WHERE id = %s AND volunteer_id = %s
        RETURNING claim_id
        """,
        (datetime.utcnow(), delivery_id, user["id"]),
        fetchone=True,
        commit=True,
    )
    if not updated:
        flash("Delivery not found.", "error")
        return redirect(url_for("volunteer.dashboard"))

    claim_id = updated["claim_id"]
    claim_row = query(
        "UPDATE claims SET status = 'completed', completed_at = %s WHERE id = %s RETURNING listing_id",
        (datetime.utcnow(), claim_id),
        fetchone=True,
        commit=True,
    )
    if claim_row:
        query(
            "UPDATE listings SET status = 'completed' WHERE id = %s",
            (claim_row["listing_id"],),
            commit=True,
        )

    return redirect(url_for("volunteer.done", delivery_id=delivery_id))


@volunteer_bp.route("/done/<int:delivery_id>")
@role_required("volunteer")
def done(delivery_id):
    """Delivery-done confirmation page."""
    user = get_current_user()
    delivery_row = query(
        """
        SELECT d.id AS delivery_id, d.status, d.delivered_at, l.title,
               un.name AS ngo_name
        FROM deliveries d
        JOIN claims c ON c.id = d.claim_id
        JOIN listings l ON l.id = c.listing_id
        JOIN users un ON un.id = c.ngo_id
        WHERE d.id = %s AND d.volunteer_id = %s
        """,
        (delivery_id, user["id"]),
        fetchone=True,
    )
    if not delivery_row:
        flash("Delivery not found.", "error")
        return redirect(url_for("volunteer.dashboard"))

    return render_template("volunteer_done.html", delivery=delivery_row)
