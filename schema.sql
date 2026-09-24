-- SharePlate database schema (PostgreSQL)
-- Run this once against your database:
--   psql -U youruser -d shareplate -f schema.sql

DROP TABLE IF EXISTS receipts CASCADE;
DROP TABLE IF EXISTS deliveries CASCADE;
DROP TABLE IF EXISTS claims CASCADE;
DROP TABLE IF EXISTS listings CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ============================================================
-- USERS  (Food Provider / NGO / Volunteer share one table,
-- distinguished by role)
-- ============================================================
CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    role            VARCHAR(20) NOT NULL CHECK (role IN ('provider', 'ngo', 'volunteer')),
    name            VARCHAR(150) NOT NULL,
    email           VARCHAR(150) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    phone           VARCHAR(20),
    address         VARCHAR(255),
    latitude        DOUBLE PRECISION,
    longitude       DOUBLE PRECISION,
    is_verified     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ============================================================
-- DOCUMENTS  (FSSAI / health license for providers,
-- registration certificate for NGOs)
-- ============================================================
CREATE TABLE documents (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    doc_type        VARCHAR(100) NOT NULL,
    file_path       VARCHAR(255) NOT NULL,
    uploaded_at     TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ============================================================
-- LISTINGS  (surplus food posted by providers)
-- ============================================================
CREATE TABLE listings (
    id              SERIAL PRIMARY KEY,
    provider_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title           VARCHAR(150) NOT NULL,
    category        VARCHAR(50) NOT NULL,           -- e.g. Bakery, Produce, Cooked Meals
    diet_type       VARCHAR(20) NOT NULL DEFAULT 'veg' CHECK (diet_type IN ('veg', 'non_veg')),
    quantity        NUMERIC(10,2) NOT NULL,
    unit            VARCHAR(20) NOT NULL DEFAULT 'kg',
    photo_path      VARCHAR(255),
    listing_type    VARCHAR(20) NOT NULL CHECK (listing_type IN ('donation', 'sale')),
    original_price  NUMERIC(10,2),
    sale_price      NUMERIC(10,2),
    expiry_at       TIMESTAMP NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'claimed', 'completed', 'spoiled', 'expired')),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ============================================================
-- CLAIMS  (an NGO reserving a listing)
-- ============================================================
CREATE TABLE claims (
    id              SERIAL PRIMARY KEY,
    listing_id      INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    ngo_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    pickup_type     VARCHAR(20) NOT NULL CHECK (pickup_type IN ('self_pickup', 'request_delivery')),
    status          VARCHAR(20) NOT NULL DEFAULT 'claimed'
                        CHECK (status IN ('claimed', 'completed', 'cancelled')),
    claimed_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMP
);

-- ============================================================
-- DELIVERIES  (volunteer fulfilling a "request_delivery" claim)
-- ============================================================
CREATE TABLE deliveries (
    id              SERIAL PRIMARY KEY,
    claim_id        INTEGER NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    volunteer_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'requested'
                        CHECK (status IN ('requested', 'booked', 'delivered')),
    booked_at       TIMESTAMP,
    delivered_at    TIMESTAMP
);

-- ============================================================
-- RECEIPTS  (auto-generated when a claim is made, shown on the
-- provider's and NGO's main page)
-- ============================================================
CREATE TABLE receipts (
    id              SERIAL PRIMARY KEY,
    listing_id      INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    claim_id        INTEGER NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    provider_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ngo_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    receipt_type    VARCHAR(20) NOT NULL CHECK (receipt_type IN ('donation', 'sale')),
    amount          NUMERIC(10,2) NOT NULL DEFAULT 0,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_listings_status ON listings(status);
CREATE INDEX idx_listings_provider ON listings(provider_id);
CREATE INDEX idx_claims_ngo ON claims(ngo_id);
CREATE INDEX idx_documents_user ON documents(user_id);
