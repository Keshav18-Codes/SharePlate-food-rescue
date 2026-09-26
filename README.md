<<<<<<< HEAD
# SharePlate

A food-rescue web app connecting **Food Providers** (shopkeepers with surplus
food), **NGOs** (who claim it), and **Volunteers** (who deliver it).

**Stack:** HTML, CSS, JavaScript (vanilla, no frameworks) + Python/Flask +
PostgreSQL (raw SQL via `psycopg2`, no ORM). Nothing else.

## 1. Prerequisites

- Python 3.9+
- PostgreSQL 13+ installed and running

## 2. Set up the database

```bash
# create the database
createdb shareplate

# load the schema
psql -U postgres -d shareplate -f schema.sql
```

## 3. Configure environment variables

Copy `.env.example` to `.env` and fill in your DB credentials, then export
them (or use a tool like `python-dotenv` / your shell's `source`):

```bash
cp .env.example .env
export $(cat .env | xargs)   # or set them manually
```

Required variables: `SECRET_KEY`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`,
`DB_PASSWORD`.

## 4. Install dependencies and run

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Visit **http://localhost:5000**

## 5. How to demo it

1. Register a **Provider** account (upload any PDF/image as the "FSSAI
   license" — verification is stored but not enforced for this demo).
2. Log in as the Provider, list a surplus food item (try one as a
   donation and one as a discounted sale).
3. Register/log in as an **NGO**, go to "Discover Food", filter by
   veg/non-veg, and claim an item — choose "Request Delivery" for at
   least one claim.
4. Check the NGO's "My Receipts" page — the receipt is auto-generated.
5. Register/log in as a **Volunteer**, go to "Delivery Requests", book
   the delivery you just created, then mark it delivered — you'll land
   on the delivery-done page.
6. Log back in as the Provider — the "Impact / Recent Receipts" table
   on the dashboard shows the completed claim.

## Project structure

```
shareplate_flask/
├── app.py                 # Flask entrypoint, blueprint registration
├── db.py                  # raw psycopg2 connection + query helper
├── helpers.py             # session auth decorators (login_required, role_required)
├── schema.sql             # PostgreSQL DDL — run this once
├── requirements.txt       # Flask + psycopg2-binary, nothing else
├── routes/
│   ├── auth.py             # registration (+doc upload), login, logout
│   ├── provider.py         # listings CRUD, inventory dashboard, receipts
│   ├── ngo.py               # discovery feed, filters, claim, receipts
│   └── volunteer.py         # delivery booking + delivery-done pages
├── templates/              # Jinja2 HTML templates
├── static/css/style.css    # vanilla CSS design system
├── static/js/              # vanilla JS: pricing toggle, geolocation, distance sort
└── uploads/
    ├── documents/           # verification docs (private, login-gated)
    └── food/                # food photos (public)
```

## Notes / things to extend for a stronger submission

- Verification documents are stored but not actually reviewed by an
  admin — add an admin approval flow (`is_verified` column already
  exists on `users`) if your rubric needs it.
- Distance in the NGO feed is calculated client-side (Haversine formula
  in `static/js/distance.js`) from browser geolocation — no map library
  is used, per the "no other tech" constraint.
- Expired listings aren't auto-expired by a background job; you could
  add a simple check comparing `expiry_at` to `NOW()` if you want that
  for the demo.
=======
# SharePlate-food-rescue
>>>>>>> 39403f3aaea090b1bffc9278608d1ca68bfb2b68
