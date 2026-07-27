"""repair invoice tax context and snapshots

Revision ID: 0012_invoice_tax_repair
Revises: 0011_coord_singleton
Create Date: 2026-07-27
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0012_invoice_tax_repair"
down_revision: Union[str, None] = "0011_coord_singleton"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Keep the repair deterministic while the app starts. The statements below
    # only fill missing/zero tax data; existing non-zero manual values survive.
    op.execute("LOCK TABLE event_items, payment_requests IN SHARE ROW EXCLUSIVE MODE")

    # Some old requests still have contractor_id even when their copied BIN/status
    # fields were empty. Restore the identity first without touching tax amounts.
    op.execute(
        """
        UPDATE payment_requests AS payment
        SET iin_bin_snapshot = COALESCE(
                NULLIF(payment.iin_bin_snapshot, ''),
                contractor.iin_bin
            ),
            tax_status_snapshot = CASE
                WHEN payment.tax_status_snapshot IS NULL
                  OR payment.tax_status_snapshot IN ('', 'not_found', 'error', 'legacy_checked')
                THEN contractor.tax_status
                ELSE payment.tax_status_snapshot
            END,
            contractor_name_snapshot = COALESCE(
                NULLIF(payment.contractor_name_snapshot, ''),
                contractor.name
            ),
            tax_source_snapshot = COALESCE(
                NULLIF(payment.tax_source_snapshot, ''),
                contractor.source,
                'recovered_v0012'
            ),
            updated_at = CURRENT_TIMESTAMP
        FROM contractors AS contractor
        WHERE payment.contractor_id = contractor.id
          AND payment.payment_method = 'invoice'
          AND payment.status NOT IN ('cancelled', 'rejected')
          AND (
              NULLIF(payment.iin_bin_snapshot, '') IS NULL
              OR payment.tax_status_snapshot IS NULL
              OR payment.tax_status_snapshot IN ('', 'not_found', 'error', 'legacy_checked')
              OR NULLIF(payment.contractor_name_snapshot, '') IS NULL
          )
        """
    )

    # KGD checks already wrote an exact before/after audit entry. Use the newest
    # successful one for an invoice item whose live tax context was later erased.
    op.execute(
        """
        WITH latest_audit AS (
            SELECT DISTINCT ON (audit.entity_id)
                audit.entity_id AS item_id,
                regexp_replace(audit.after_json ->> 'iin_bin', '[^0-9]', '', 'g') AS iin_bin,
                audit.after_json ->> 'tax_check_status' AS tax_status,
                COALESCE(NULLIF(audit.after_json ->> 'vat_amount', '')::numeric, 0) AS vat_amount,
                COALESCE(NULLIF(audit.after_json ->> 'deduction_amount', '')::numeric, 0) AS deduction_amount
            FROM audit_log AS audit
            WHERE audit.entity_type = 'event_item'
              AND (
                  audit.action LIKE 'tax_checked_%'
                  OR audit.action = 'tax_set_manual'
              )
              AND audit.after_json IS NOT NULL
              AND lower(COALESCE(audit.after_json ->> 'iin_bin_locked', 'false')) = 'true'
              AND audit.after_json ->> 'tax_check_status' NOT IN ('', 'not_found', 'error')
              AND length(regexp_replace(audit.after_json ->> 'iin_bin', '[^0-9]', '', 'g')) = 12
            ORDER BY audit.entity_id, audit.created_at DESC NULLS LAST, audit.id DESC
        )
        UPDATE event_items AS item
        SET payment_method = 'invoice',
            iin_bin = CASE
                WHEN length(regexp_replace(COALESCE(item.iin_bin, ''), '[^0-9]', '', 'g')) = 12
                THEN item.iin_bin
                ELSE audit.iin_bin
            END,
            iin_bin_locked = TRUE,
            tax_check_status = CASE
                WHEN item.tax_check_status IS NULL
                  OR item.tax_check_status IN ('', 'not_found', 'error', 'legacy_checked')
                THEN audit.tax_status
                ELSE item.tax_check_status
            END,
            vat_amount = CASE
                WHEN COALESCE(item.vat_amount, 0) = 0 AND audit.vat_amount <> 0
                THEN audit.vat_amount
                ELSE item.vat_amount
            END,
            deduction_amount = CASE
                WHEN COALESCE(item.deduction_amount, 0) = 0 AND audit.deduction_amount <> 0
                THEN audit.deduction_amount
                ELSE item.deduction_amount
            END,
            updated_at = CURRENT_TIMESTAMP
        FROM latest_audit AS audit
        WHERE item.id = audit.item_id
          AND EXISTS (
              SELECT 1
              FROM payment_requests AS payment
              WHERE payment.event_item_id = item.id
                AND payment.payment_method = 'invoice'
                AND payment.status NOT IN ('cancelled', 'rejected')
          )
          AND (
              item.payment_method IS DISTINCT FROM 'invoice'
              OR length(regexp_replace(COALESCE(item.iin_bin, ''), '[^0-9]', '', 'g')) <> 12
              OR item.iin_bin_locked IS DISTINCT FROM TRUE
              OR item.tax_check_status IS NULL
              OR item.tax_check_status IN ('', 'not_found', 'error', 'legacy_checked')
              OR (COALESCE(item.vat_amount, 0) = 0 AND audit.vat_amount <> 0)
              OR (COALESCE(item.deduction_amount, 0) = 0 AND audit.deduction_amount <> 0)
          )
        """
    )

    # Copy the recovered live context into incomplete active request snapshots.
    # These are the immutable request/card fields and are also a future fallback.
    op.execute(
        """
        UPDATE payment_requests AS payment
        SET iin_bin_snapshot = CASE
                WHEN length(regexp_replace(COALESCE(payment.iin_bin_snapshot, ''), '[^0-9]', '', 'g')) = 12
                THEN payment.iin_bin_snapshot
                ELSE item.iin_bin
            END,
            tax_status_snapshot = CASE
                WHEN payment.tax_status_snapshot IS NULL
                  OR payment.tax_status_snapshot IN ('', 'not_found', 'error', 'legacy_checked')
                THEN item.tax_check_status
                ELSE payment.tax_status_snapshot
            END,
            vat_status_snapshot = CASE
                WHEN COALESCE(NULLIF(payment.vat_status_snapshot, ''), '') <> ''
                THEN payment.vat_status_snapshot
                WHEN item.tax_check_status = 'our_vat' OR COALESCE(item.vat_amount, 0) > 0
                THEN 'vat'
                ELSE 'no_vat'
            END,
            vat_amount_snapshot = CASE
                WHEN COALESCE(payment.vat_amount_snapshot, 0) = 0 AND COALESCE(item.vat_amount, 0) <> 0
                THEN item.vat_amount
                ELSE payment.vat_amount_snapshot
            END,
            deduction_amount_snapshot = CASE
                WHEN COALESCE(payment.deduction_amount_snapshot, 0) = 0
                  AND COALESCE(item.deduction_amount, 0) <> 0
                THEN item.deduction_amount
                ELSE payment.deduction_amount_snapshot
            END,
            tax_source_snapshot = COALESCE(
                NULLIF(payment.tax_source_snapshot, ''),
                'recovered_v0012'
            ),
            updated_at = CURRENT_TIMESTAMP
        FROM event_items AS item
        WHERE payment.event_item_id = item.id
          AND payment.payment_method = 'invoice'
          AND payment.status NOT IN ('cancelled', 'rejected')
          AND length(regexp_replace(COALESCE(item.iin_bin, ''), '[^0-9]', '', 'g')) = 12
          AND item.iin_bin_locked = TRUE
          AND item.tax_check_status IS NOT NULL
          AND item.tax_check_status NOT IN ('', 'not_found', 'error', 'legacy_checked')
          AND (
              length(regexp_replace(COALESCE(payment.iin_bin_snapshot, ''), '[^0-9]', '', 'g')) <> 12
              OR payment.tax_status_snapshot IS NULL
              OR payment.tax_status_snapshot IN ('', 'not_found', 'error', 'legacy_checked')
              OR NULLIF(payment.vat_status_snapshot, '') IS NULL
              OR (COALESCE(payment.vat_amount_snapshot, 0) = 0 AND COALESCE(item.vat_amount, 0) <> 0)
              OR (
                  COALESCE(payment.deduction_amount_snapshot, 0) = 0
                  AND COALESCE(item.deduction_amount, 0) <> 0
              )
          )
        """
    )

    # If the status/base snapshots survived but the calculated amounts did not,
    # rebuild only the missing zero values with the same 16% VAT / 10% deduction
    # formula used by the application. Never replace an existing non-zero value.
    op.execute(
        """
        UPDATE payment_requests AS payment
        SET vat_status_snapshot = CASE
                WHEN payment.tax_status_snapshot = 'our_vat' THEN 'vat'
                ELSE 'no_vat'
            END,
            vat_amount_snapshot = CASE
                WHEN payment.tax_status_snapshot = 'our_vat'
                  AND COALESCE(payment.vat_amount_snapshot, 0) = 0
                THEN round(
                    COALESCE(payment.item_amount_fact_snapshot, payment.item_amount_plan_snapshot, 0)
                    - COALESCE(payment.item_amount_fact_snapshot, payment.item_amount_plan_snapshot, 0) / 1.16,
                    2
                )
                ELSE payment.vat_amount_snapshot
            END,
            deduction_amount_snapshot = CASE
                WHEN payment.tax_status_snapshot = 'our_vat'
                  AND COALESCE(payment.deduction_amount_snapshot, 0) = 0
                THEN round(
                    COALESCE(payment.item_amount_fact_snapshot, payment.item_amount_plan_snapshot, 0) / 1.16 * 0.10,
                    2
                )
                WHEN payment.tax_status_snapshot = 'our_no_vat'
                  AND COALESCE(payment.deduction_amount_snapshot, 0) = 0
                THEN round(
                    COALESCE(payment.item_amount_fact_snapshot, payment.item_amount_plan_snapshot, 0) * 0.10,
                    2
                )
                ELSE payment.deduction_amount_snapshot
            END,
            tax_source_snapshot = COALESCE(
                NULLIF(payment.tax_source_snapshot, ''),
                'recovered_v0012'
            ),
            updated_at = CURRENT_TIMESTAMP
        WHERE payment.payment_method = 'invoice'
          AND payment.status NOT IN ('cancelled', 'rejected')
          AND length(regexp_replace(COALESCE(payment.iin_bin_snapshot, ''), '[^0-9]', '', 'g')) = 12
          AND payment.tax_status_snapshot IN ('our_vat', 'our_no_vat')
          AND (
              NULLIF(payment.vat_status_snapshot, '') IS NULL
              OR (
                  payment.tax_status_snapshot = 'our_vat'
                  AND COALESCE(payment.vat_amount_snapshot, 0) = 0
                  AND COALESCE(payment.item_amount_fact_snapshot, payment.item_amount_plan_snapshot, 0) <> 0
              )
              OR (
                  COALESCE(payment.deduction_amount_snapshot, 0) = 0
                  AND COALESCE(payment.item_amount_fact_snapshot, payment.item_amount_plan_snapshot, 0) <> 0
              )
          )
        """
    )

    # Finally, make each live item agree with its newest complete active invoice
    # request. This repairs the exact stale-autosave damage seen in production.
    op.execute(
        """
        WITH latest_request AS (
            SELECT DISTINCT ON (payment.event_item_id)
                payment.event_item_id AS item_id,
                payment.iin_bin_snapshot AS iin_bin,
                payment.tax_status_snapshot AS tax_status,
                payment.vat_amount_snapshot AS vat_amount,
                payment.deduction_amount_snapshot AS deduction_amount
            FROM payment_requests AS payment
            WHERE payment.payment_method = 'invoice'
              AND payment.status NOT IN ('cancelled', 'rejected')
              AND length(regexp_replace(COALESCE(payment.iin_bin_snapshot, ''), '[^0-9]', '', 'g')) = 12
              AND payment.tax_status_snapshot IS NOT NULL
              AND payment.tax_status_snapshot NOT IN ('', 'not_found', 'error', 'legacy_checked')
            ORDER BY
                payment.event_item_id,
                payment.created_at DESC NULLS LAST,
                payment.id DESC
        ),
        changed AS (
            UPDATE event_items AS item
            SET payment_method = 'invoice',
                iin_bin = CASE
                    WHEN length(regexp_replace(COALESCE(item.iin_bin, ''), '[^0-9]', '', 'g')) = 12
                    THEN item.iin_bin
                    ELSE request.iin_bin
                END,
                iin_bin_locked = TRUE,
                tax_check_status = CASE
                    WHEN item.tax_check_status IS NULL
                      OR item.tax_check_status IN ('', 'not_found', 'error', 'legacy_checked')
                    THEN request.tax_status
                    ELSE item.tax_check_status
                END,
                vat_amount = CASE
                    WHEN COALESCE(item.vat_amount, 0) = 0 AND COALESCE(request.vat_amount, 0) <> 0
                    THEN request.vat_amount
                    ELSE item.vat_amount
                END,
                deduction_amount = CASE
                    WHEN COALESCE(item.deduction_amount, 0) = 0
                      AND COALESCE(request.deduction_amount, 0) <> 0
                    THEN request.deduction_amount
                    ELSE item.deduction_amount
                END,
                updated_at = CURRENT_TIMESTAMP
            FROM latest_request AS request
            WHERE item.id = request.item_id
              AND (
                  item.payment_method IS DISTINCT FROM 'invoice'
                  OR length(regexp_replace(COALESCE(item.iin_bin, ''), '[^0-9]', '', 'g')) <> 12
                  OR item.iin_bin_locked IS DISTINCT FROM TRUE
                  OR item.tax_check_status IS NULL
                  OR item.tax_check_status IN ('', 'not_found', 'error', 'legacy_checked')
                  OR (COALESCE(item.vat_amount, 0) = 0 AND COALESCE(request.vat_amount, 0) <> 0)
                  OR (
                      COALESCE(item.deduction_amount, 0) = 0
                      AND COALESCE(request.deduction_amount, 0) <> 0
                  )
              )
            RETURNING
                item.id,
                item.iin_bin,
                item.tax_check_status,
                item.vat_amount,
                item.deduction_amount
        )
        INSERT INTO audit_log (
            user_id,
            entity_type,
            entity_id,
            action,
            before_json,
            after_json,
            created_at
        )
        SELECT
            NULL,
            'event_item',
            changed.id,
            'invoice_tax_context_recovered_v0012',
            NULL,
            json_build_object(
                'iin_bin', changed.iin_bin,
                'iin_bin_locked', TRUE,
                'tax_check_status', changed.tax_check_status,
                'vat_amount', changed.vat_amount,
                'deduction_amount', changed.deduction_amount
            ),
            CURRENT_TIMESTAMP
        FROM changed
        """
    )


def downgrade() -> None:
    # The migration only restores data that was already present in KGD audit
    # entries, contractor records, request snapshots or their saved amount base.
    # Re-erasing recovered accounting data on downgrade would be destructive.
    pass
