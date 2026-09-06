-- Adds fields required for customer authentication in public API.
ALTER TABLE "Customer"
ADD COLUMN IF NOT EXISTS password VARCHAR(128),
ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT now();
