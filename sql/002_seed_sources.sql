INSERT INTO source_registry (name, type, base_url, cadence, enabled) VALUES
    ('contracts_finder', 'contract', 'https://www.contractsfinder.service.gov.uk/', 'daily', TRUE),
    ('ukri_gtr', 'grant', 'https://gtr.ukri.org/', 'daily', TRUE),
    ('ons', 'macro', 'https://api.ons.gov.uk/', 'weekly', TRUE)
ON CONFLICT (name) DO NOTHING;
