from app.ai.receipt.state import ReceiptState


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None

    return " ".join(value.split()).strip()


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

    return currencies.get(value.lower(), value.upper())


def normalize_gstin(value: str | None) -> str | None:
    if value is None:
        return None

    return value.replace(" ", "").upper()


def normalization_node(state: ReceiptState):
    receipt = state["extracted_receipt"]

    if receipt is None:
        raise ValueError("Extracted receipt is missing")

    normalized = receipt.model_copy(deep=True)

    # Merchant
    normalized.merchant.name = normalize_text(normalized.merchant.name)

    normalized.merchant.address = normalize_text(normalized.merchant.address)

    normalized.merchant.phone = normalize_text(normalized.merchant.phone)

    normalized.merchant.gst_number = normalize_gstin(normalized.merchant.gst_number)

    # Currency
    normalized.totals.currency = normalize_currency(normalized.totals.currency)

    # Items
    for item in normalized.items:
        item.name = normalize_text(item.name) or item.name

    return {"normalized_receipt": normalized}
