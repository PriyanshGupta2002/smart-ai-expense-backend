from paddleocr import PaddleOCR

from app.ai.receipt.schemas import OCRBlock
from app.ai.receipt.state import ReceiptState

ocr = PaddleOCR(
    use_doc_orientation_classify=True,
    use_doc_unwarping=True,
    use_textline_orientation=True,
    lang="en",
)


def ocr_node(state: ReceiptState):
    image_path = state["image_path"]

    result = ocr.predict(image_path)

    ocr_blocks: list[OCRBlock] = []

    for page in result:

        texts = page["rec_texts"]
        scores = page["rec_scores"]
        polygons = page["rec_polys"]

        for text, score, polygon in zip(
            texts,
            scores,
            polygons,
        ):
            ocr_blocks.append(
                OCRBlock(
                    text=text,
                    confidence=float(score),
                    bbox=polygon.tolist(),
                )
            )

    ocr_text = "\n".join(block.text for block in ocr_blocks)

    return {
        "raw_ocr": ocr_blocks,
        "ocr_text": ocr_text,
    }
