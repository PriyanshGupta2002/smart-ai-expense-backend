from app.ai.receipt.schemas import OCRBlock, LayoutBlock, OCRRow
from app.ai.receipt.state import ReceiptState


def geometry(block: OCRBlock):

    xs = [point[0] for point in block.bbox]
    ys = [point[1] for point in block.bbox]

    return LayoutBlock(
        text=block.text,
        confidence=block.confidence,
        x=min(xs),
        y=min(ys),
        width=max(xs) - min(xs),
        height=max(ys) - min(ys),
    )


def layout_node(state: ReceiptState):

    blocks = [geometry(block) for block in state["raw_ocr"]]

    blocks.sort(key=lambda b: b.y + b.height / 2)

    rows: list[list[LayoutBlock]] = []

    for block in blocks:

        center_y = block.y + block.height / 2

        matched = False

        for row in rows:

            avg_y = sum(b.y + b.height / 2 for b in row) / len(row)

            avg_height = sum(b.height for b in row) / len(row)

            tolerance = avg_height * 0.6

            if abs(center_y - avg_y) <= tolerance:
                row.append(block)
                matched = True
                break

        if not matched:
            rows.append([block])

    result = []

    for row in rows:

        row.sort(key=lambda b: b.x)

        result.append(OCRRow(blocks=row))

    layout_text = "\n".join(
        " | ".join(block.text for block in row.blocks) for row in result
    )

    return {
        "layout": result,
        "layout_text": layout_text,
    }
