"""
routes/provider.py
Food Provider (shopkeeper) module:
 - list surplus food (category, quantity, expiry)
 - free donation vs discounted sale pricing
 - active inventory dashboard (edit / pull down spoiled items)
 - receipts feed (impact) after an NGO claims/buys
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash

from db import query
from helpers import role_required, get_current_user

provider_bp = Blueprint("provider", __name__, url_prefix="/provider")


@provider_bp.route("/dashboard")
@role_required("provider")
def dashboard():
    user = get_current_user()

    listings = query(
        """
        SELECT * FROM listings
        WHERE provider_id = %s
        ORDER BY
            CASE status WHEN 'active' THEN 0 ELSE 1 END,
            created_at DESC
        """,
        (user["id"],),
        fetchall=True,
    )

    receipts = query(
        """
        SELECT r.*, l.title AS listing_title, u.name AS ngo_name
        FROM receipts r
        JOIN listings l ON l.id = r.listing_id
        JOIN users u ON u.id = r.ngo_id
        WHERE r.provider_id = %s
        ORDER BY r.created_at DESC
        LIMIT 20
        """,
        (user["id"],),
        fetchall=True,
    )

    return render_template("provider_dashboard.html", listings=listings, receipts=receipts)


@provider_bp.route("/listings/new", methods=["GET", "POST"])
@role_required("provider")
def new_listing():
    if request.method == "GET":
        return render_template("provider_new_listing.html")

    user = get_current_user()
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "").strip()
    diet_type = request.form.get("diet_type", "veg")
    quantity = request.form.get("quantity")
    unit = request.form.get("unit", "kg")
    listing_type = request.form.get("listing_type")  # 'donation' or 'sale'
    original_price = request.form.get("original_price") or None
    sale_price = request.form.get("sale_price") or None
    expiry_at = request.form.get("expiry_at")  # datetime-local input

    if not title or not category or not quantity or not listing_type or not expiry_at:
        flash("Please fill in all required fields.", "error")
        return render_template("provider_new_listing.html", form=request.form)

    if listing_type not in ("donation", "sale"):
        flash("Invalid listing type.", "error")
        return render_template("provider_new_listing.html", form=request.form)

    if listing_type == "sale" and not sale_price:
        flash("Please enter a discounted sale price.", "error")
        return render_template("provider_new_listing.html", form=request.form)

    query(
        """
        INSERT INTO listings
            (provider_id, title, category, diet_type, quantity, unit, photo_path,
             listing_type, original_price, sale_price, expiry_at, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')
        """,
        (user["id"], title, category, diet_type, quantity, unit, None,
         listing_type, original_price, sale_price, expiry_at),
        commit=True,
    )

    flash("Listing posted!", "success")
    return redirect(url_for("provider.dashboard"))


@provider_bp.route("/listings/<int:listing_id>/edit", methods=["GET", "POST"])
@role_required("provider")
def edit_listing(listing_id):
    user = get_current_user()
    listing = query(
        "SELECT * FROM listings WHERE id = %s AND provider_id = %s",
        (listing_id, user["id"]),
        fetchone=True,
    )
    if not listing:
        flash("Listing not found.", "error")
        return redirect(url_for("provider.dashboard"))

    if request.method == "GET":
        return render_template("provider_edit_listing.html", listing=listing)

    title = request.form.get("title", "").strip()
    category = request.form.get("category", "").strip()
    diet_type = request.form.get("diet_type", "veg")
    quantity = request.form.get("quantity")
    unit = request.form.get("unit", "kg")
    listing_type = request.form.get("listing_type")  # 'donation' or 'sale'
    original_price = request.form.get("original_price") or None
    sale_price = request.form.get("sale_price") or None
    expiry_at = request.form.get("expiry_at")

    if not title or not category or not quantity or not listing_type or not expiry_at:
        flash("Please fill in all required fields.", "error")
        return render_template("provider_edit_listing.html", listing=listing, form=request.form)

    if listing_type not in ("donation", "sale"):
        flash("Invalid listing type.", "error")
        return render_template("provider_edit_listing.html", listing=listing, form=request.form)

    if listing_type == "sale" and not sale_price:
        flash("Please enter a discounted sale price.", "error")
        return render_template("provider_edit_listing.html", listing=listing, form=request.form)

    query(
        """
        UPDATE listings
        SET title = %s, category = %s, diet_type = %s, quantity = %s, unit = %s,
            listing_type = %s, original_price = %s, sale_price = %s,
            expiry_at = %s
        WHERE id = %s
        """,
        (title, category, diet_type, quantity, unit,
         listing_type, original_price, sale_price, expiry_at, listing_id),
        commit=True,
    )

    flash("Listing updated.", "success")
    return redirect(url_for("provider.dashboard"))


@provider_bp.route("/listings/<int:listing_id>/update", methods=["POST"])
@role_required("provider")
def update_listing(listing_id):
    user = get_current_user()
    listing = query(
        "SELECT * FROM listings WHERE id = %s AND provider_id = %s",
        (listing_id, user["id"]),
        fetchone=True,
    )
    if not listing:
        flash("Listing not found.", "error")
        return redirect(url_for("provider.dashboard"))

    new_quantity = request.form.get("quantity")
    if new_quantity:
        query(
            "UPDATE listings SET quantity = %s WHERE id = %s",
            (new_quantity, listing_id),
            commit=True,
        )
        flash("Quantity updated.", "success")

    return redirect(url_for("provider.dashboard"))


@provider_bp.route("/listings/<int:listing_id>/pull-down", methods=["POST"])
@role_required("provider")
def pull_down(listing_id):
    """Mark a listing as spoiled/withdrawn -- removes it from the live feed."""
    user = get_current_user()
    listing = query(
        "SELECT * FROM listings WHERE id = %s AND provider_id = %s",
        (listing_id, user["id"]),
        fetchone=True,
    )
    if not listing:
        flash("Listing not found.", "error")
        return redirect(url_for("provider.dashboard"))

    query(
        "UPDATE listings SET status = 'spoiled' WHERE id = %s",
        (listing_id,),
        commit=True,
    )
    flash("Listing pulled down.", "success")
    return redirect(url_for("provider.dashboard"))