-- migrations/001_initial.sql

CREATE EXTENSION IF NOT EXISTS vector;

-- Core nomenclature tree
CREATE TABLE taric_nodes (
    id              SERIAL PRIMARY KEY,
    code            TEXT NOT NULL UNIQUE,
    level           TEXT NOT NULL CHECK (level IN (
        'SECTION','CHAPTER','HEADING','SUBHEADING','CN8','TARIC10'
    )),
    description     TEXT NOT NULL,
    parent_code     TEXT,
    indent          INT DEFAULT 0,              -- dash level for GRI 6
    section_number  TEXT,                        -- e.g. 'XI' for textiles
    chapter_notes   TEXT,
    subheading_notes TEXT,
    valid_from      DATE DEFAULT '2026-01-01',
    valid_to        DATE,
    embedding       vector(1536)
);

CREATE INDEX idx_tn_code       ON taric_nodes(code);
CREATE INDEX idx_tn_level      ON taric_nodes(level);
CREATE INDEX idx_tn_parent     ON taric_nodes(parent_code);
CREATE INDEX idx_tn_valid      ON taric_nodes(valid_from, valid_to);
-- pgvector HNSW for fallback/durability (hot path uses TurboVec)
CREATE INDEX idx_tn_vec        ON taric_nodes USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- BTI rulings (gold-standard labeled examples)
CREATE TABLE bti_rulings (
    id              SERIAL PRIMARY KEY,
    bti_ref         TEXT UNIQUE NOT NULL,
    taric_code      TEXT NOT NULL,
    product_desc    TEXT NOT NULL,
    legal_basis     TEXT,                        -- GRI reference
    classification_rationale TEXT,
    issuing_country TEXT,                         -- 2-letter ISO
    start_date      DATE,
    end_date        DATE,
    keywords        TEXT[],
    embedding       vector(1536)
);

CREATE INDEX idx_bti_code      ON bti_rulings(taric_code);
CREATE INDEX idx_bti_vec       ON bti_rulings USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- TARIC measures (duty rates, quotas, prohibitions per code × origin)
CREATE TABLE taric_measures (
    id              SERIAL PRIMARY KEY,
    taric_code      TEXT NOT NULL,
    measure_type    TEXT NOT NULL,               -- 'third_country_duty','anti_dumping','quota','prohibition','license','preference'
    duty_expression TEXT,                         -- e.g. '12%', '0%', '€3 flat'
    geo_area_code   TEXT,                         -- ISO or TARIC geo group (e.g. '1011' = all third countries)
    geo_area_desc   TEXT,
    legal_base      TEXT,
    order_number    TEXT,                         -- for quotas
    condition_code  TEXT,
    valid_from      DATE,
    valid_to        DATE
);

CREATE INDEX idx_tm_code       ON taric_measures(taric_code);
CREATE INDEX idx_tm_geo        ON taric_measures(geo_area_code);
CREATE INDEX idx_tm_type       ON taric_measures(measure_type);

-- Classification sessions (tracks user flow + builds training data)
CREATE TABLE classifier_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at      TIMESTAMPTZ DEFAULT now(),
    origin_country  TEXT,
    dest_country    TEXT,
    incoterms       TEXT,
    product_desc    TEXT,
    -- HS6 stage
    candidate_hs6   JSONB,                       -- [{code, desc, score}]
    selected_hs6    TEXT,
    -- Narrowing stage
    narrowing_qs    JSONB,                        -- [{question, options, discriminator_key}]
    narrowing_ans   JSONB,                        -- {key: answer}
    -- Result stage
    suggested_hs10  JSONB,                        -- [{code, confidence, explanation}]
    final_hs10      TEXT,
    measures        JSONB,                        -- applicable duties/quotas
    -- Feedback
    user_feedback   TEXT CHECK (user_feedback IN ('correct','partial','wrong')),
    feedback_note   TEXT
);

CREATE INDEX idx_cs_feedback ON classifier_sessions(user_feedback)
    WHERE user_feedback IS NOT NULL;