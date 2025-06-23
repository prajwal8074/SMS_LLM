-- Create the listings table if it doesn't exist
CREATE TABLE IF NOT EXISTS listings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- Unique ID for the listing
    item_name VARCHAR(255) NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    description TEXT DEFAULT 'No description',
    seller_name TEXT DEFAULT 'Unknown',
    seller_contact NUMERIC(10) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active', -- 'active', 'sold'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);