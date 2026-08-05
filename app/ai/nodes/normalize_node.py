from decimal import Decimal

from app.ai.receipt.state import ReceiptState


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None

    value = " ".join(value.split()).strip()

    return value or None


def normalize_currency(value: str | None) -> str | None:
    if value is None:
        return None

    currencies = {
        "$": "USD",
        "usd": "USD",
        "₹": "INR",
        "rs": "INR",
        "rs.": "INR",
        "inr": "INR",
        "€": "EUR",
        "eur": "EUR",
        "£": "GBP",
        "gbp": "GBP",
    }

    value = value.strip()

    return currencies.get(
        value.lower(),
        value.upper(),
    )


def normalize_gstin(value: str | None) -> str | None:
    if value is None:
        return None

    value = value.replace(
        " ",
        "",
    ).upper()

    return value or None


def normalize_payment_method(value: str | None) -> str | None:
    if value is None:
        return None

    value = value.strip().lower()

    mapping = {
        "upi": "UPI",
        "cash": "CASH",
        "credit card": "CARD",
        "debit card": "CARD",
        "card": "CARD",
        "visa": "CARD",
        "mastercard": "CARD",
        "master card": "CARD",
        "amex": "CARD",
        "american express": "CARD",
        "net banking": "NET_BANKING",
        "bank transfer": "BANK_TRANSFER",
    }

    return mapping.get(
        value,
        value.upper(),
    )


def normalize_decimal(value: Decimal | float | None):
    if value is None:
        return None

    return round(
        Decimal(value),
        2,
    )


def normalization_node(state: ReceiptState):

    receipt = state["extracted_receipt"]

    if receipt is None:
        raise ValueError("Extracted receipt is missing.")

    normalized = receipt.model_copy(
        deep=True,
    )

    # --------------------------------------------------
    # Merchant
    # --------------------------------------------------

    normalized.merchant.name = normalize_text(
        normalized.merchant.name,
    )

    normalized.merchant.address = normalize_text(
        normalized.merchant.address,
    )

    normalized.merchant.phone = normalize_text(
        normalized.merchant.phone,
    )

    normalized.merchant.gst_number = normalize_gstin(
        normalized.merchant.gst_number,
    )

    # --------------------------------------------------
    # Receipt / Invoice Metadata
    # --------------------------------------------------

    if hasattr(normalized, "invoice_number"):
        normalized.invoice_number = normalize_text(
            normalized.invoice_number,
        )

    if hasattr(normalized, "purchase_order"):
        normalized.purchase_order = normalize_text(
            normalized.purchase_order,
        )

    # --------------------------------------------------
    # Totals
    # --------------------------------------------------

    normalized.totals.currency = normalize_currency(
        normalized.totals.currency,
    )

    normalized.totals.subtotal = normalize_decimal(
        normalized.totals.subtotal,
    )

    normalized.totals.tax = normalize_decimal(
        normalized.totals.tax,
    )

    normalized.totals.discount = normalize_decimal(
        normalized.totals.discount,
    )

    normalized.totals.total = normalize_decimal(
        normalized.totals.total,
    )

    # --------------------------------------------------
    # Payment
    # --------------------------------------------------

    if hasattr(normalized, "payment_method"):
        normalized.payment_method = normalize_payment_method(
            normalized.payment_method,
        )

    # --------------------------------------------------
    # Line Items
    # --------------------------------------------------

    for item in normalized.items:

        item.name = (
            normalize_text(
                item.name,
            )
            or item.name
        )

        if hasattr(item, "category"):
            item.category = normalize_text(
                item.category,
            )

        item.quantity = normalize_decimal(
            item.quantity,
        )

        item.unit_price = normalize_decimal(
            item.unit_price,
        )

        item.total_price = normalize_decimal(
            item.total_price,
        )

    return {
        "normalized_receipt": normalized,
    }
