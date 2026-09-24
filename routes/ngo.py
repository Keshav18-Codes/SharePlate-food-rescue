"""
routes/ngo.py
NGO (Receiver) module:
 - live discovery feed of nearby surplus food
 - veg/non-veg + quantity filters
 - one-click claim (reservation) system
 - pickup coordination: self-pickup vs request delivery
 - auto-generated receipt shown on the NGO's main page after claiming
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash

from db import query
from helpers import role_required, get_current_user

ngo_bp = Blueprint("ngo", __name__, url_prefix="/ngo")


@ngo_bp.route("/discover")
@role_required("ngo")
def discover():
    user = get_current_user()

    diet = request.args.get("diet", "")        # '', 'veg', 'non_veg'
    min_qty = request.args.get("min_qty", "")

    sql = """
        SELECT l.*, u.name AS provider_name, u.address AS provider_address,
               u.latitude AS provider_lat, u.longitude AS provider_lng
        FROM listings l
        JOIN users u ON u.id = l.provider_id
        WHERE l.status = 'active'
    """
    params = []

    if diet in ("veg", "non_veg"):
        sql += " AND l.diet_type = %s"
        params.append(diet)

    if min_qty:
        sql += " AND l.quantity >= %s"
        params.append(min_qty)

    sql += " ORDER BY l.created_at DESC"

    listings = query(sql, tuple(params), fetchall=True)

    return render_template(
        "ngo_discover.html",
        listings=listings,
        diet=diet,
        min_qty=min_qty,
        ngo_lat=user["latitude"],
        ngo_lng=user["longitude"],
    )


@ngo_bp.route("/claim/<int:listing_id>", methods=["POST"])
@role_required("ngo")
def claim(listing_id):
    user = get_current_user()
    pickup_type = request.form.get("pickup_type")  # 'self_pickup' or 'request_delivery'

    if pickup_type not in ("self_pickup", "request_delivery"):
        flash("Please choose a pickup option.", "error")
        return redirect(url_for("ngo.discover"))

    listing = query("SELECT * FROM listings WHERE id = %s", (listing_id,), fetchone=True)
    if not listing or listing["status"] != "active":
        flash("Sorry, that listing is no longer available.", "error")
        return redirect(url_for("ngo.discover"))

    # Lock the listing for this NGO
    updated = query(
        "UPDATE listings SET status = 'claimed' WHERE id = %s AND status = 'active' RETURNING id",
        (listing_id,),
        fetchone=True,
        commit=True,
    )
    if not updated:
        flash("Someone else just claimed this listing.", "error")
        return redirect(url_for("ngo.discover"))

    new_claim = query(
        """
        INSERT INTO claims (listing_id, ngo_id, pickup_type, status)
        VALUES (%s, %s, %s, 'claimed')
        RETURNING id
        """,
        (listing_id, user["id"], pickup_type),
        fetchone=True,
        commit=True,
    )
    claim_id = new_claim["id"]

    if pickup_type == "request_delivery":
        query(
            "INSERT INTO deliveries (claim_id, status) VALUES (%s, 'requested')",
            (claim_id,),
            commit=True,
        )

    # Auto-generate the receipt
    is_sale = listing["listing_type"] == "sale"
    amount = listing["sale_price"] if is_sale else 0
    new_receipt = query(
        """
        INSERT INTO receipts (listing_id, claim_id, provider_id, ngo_id, receipt_type, amount)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (listing_id, claim_id, listing["provider_id"], user["id"],
         "sale" if is_sale else "donation", amount),
        fetchone=True,
        commit=True,
    )

    flash("Claimed! Your receipt is ready.", "success")
    return redirect(url_for("ngo.receipt", receipt_id=new_receipt["id"]))


@ngo_bp.route("/dashboard")
@role_required("ngo")
def dashboard():
    """The NGO's main page: their claims + receipts."""
    user = get_current_user()

    receipts = query(
        """
        SELECT r.*, l.title AS listing_title, u.name AS provider_name
        FROM receipts r
        JOIN listings l ON l.id = r.listing_id
        JOIN users u ON u.id = r.provider_id
        WHERE r.ngo_id = %s
        ORDER BY r.created_at DESC
        """,
        (user["id"],),
        fetchall=True,
    )

    return render_template("ngo_dashboard.html", receipts=receipts)


@ngo_bp.route("/receipt/<int:receipt_id>")
@role_required("ngo")
def receipt(receipt_id):
    user = get_current_user()
    receipt_row = query(
        """
        SELECT r.*, l.title AS listing_title, l.quantity, l.unit,
               u.name AS provider_name, u.address AS provider_address
        FROM receipts r
        JOIN listings l ON l.id = r.listing_id
        JOIN users u ON u.id = r.provider_id
        WHERE r.id = %s AND r.ngo_id = %s
        """,
        (receipt_id, user["id"]),
        fetchone=True,
    )
    if not receipt_row:
        flash("Receipt not found.", "error")
        return redirect(url_for("ngo.dashboard"))

    return render_template("receipt.html", receipt=receipt_row)
