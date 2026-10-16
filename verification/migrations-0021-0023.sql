BEGIN;

-- Running upgrade 0021_avr_signed_ddc -> 0022_finance_hardening

CREATE UNIQUE INDEX uq_event_shares_event_user ON event_shares (event_id, user_id);

ALTER TABLE users ADD COLUMN token_version INTEGER DEFAULT '0' NOT NULL;

CREATE TABLE auth_attempts (
    key VARCHAR(64) NOT NULL, 
    attempts INTEGER NOT NULL, 
    window_started_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (key)
);

ALTER TABLE payment_requests ADD COLUMN operation_key VARCHAR(140);

ALTER TABLE payment_requests ADD COLUMN operation_hash VARCHAR(64);

CREATE UNIQUE INDEX uq_payment_operation_key ON payment_requests (operation_key);

UPDATE alembic_version SET version_num='0022_finance_hardening' WHERE alembic_version.version_num = '0021_avr_signed_ddc';

-- Running upgrade 0022_finance_hardening -> 0023_durable_signing

CREATE TABLE background_states (
    key VARCHAR(120) NOT NULL, 
    owner VARCHAR(64), 
    lease_until TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    watermark TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (key)
);

CREATE TABLE pending_act_signatures (
    id SERIAL NOT NULL, 
    accounting_id INTEGER NOT NULL, 
    document_sha256 VARCHAR(64), 
    signature_sha256 VARCHAR(64) NOT NULL, 
    signature_data BYTEA NOT NULL, 
    status VARCHAR(24) NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_pending_act_signature UNIQUE (accounting_id, signature_sha256), 
    FOREIGN KEY(accounting_id) REFERENCES self_employed_accounting (id) ON DELETE CASCADE
);

CREATE INDEX ix_pending_act_signatures_accounting_id ON pending_act_signatures (accounting_id);

CREATE INDEX ix_pending_act_signatures_status ON pending_act_signatures (status);

UPDATE alembic_version SET version_num='0023_durable_signing' WHERE alembic_version.version_num = '0022_finance_hardening';

COMMIT;

