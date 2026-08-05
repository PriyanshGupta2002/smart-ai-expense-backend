# from paddleocr import PaddleOCR

# from app.ai.receipt.schemas import OCRBlock
# from app.ai.receipt.state import ReceiptState

# ocr = PaddleOCR(
#     use_doc_orientation_classify=True,
#     use_doc_unwarping=True,
#     use_textline_orientation=True,
#     lang="en",
# )


# def ocr_node(state: ReceiptState):

#     image_paths = state["image_paths"]

#     all_ocr_blocks: list[OCRBlock] = []
#     page_texts: list[str] = []

#     for page_number, image_path in enumerate(
#         image_paths,
#         start=1,
#     ):

#         results = ocr.predict(image_path)

#         page_blocks: list[OCRBlock] = []

#         for result in results:

#             data = result.json

#             # Depending on PaddleOCR version, json may wrap
#             # the actual result under "res".
#             if "res" in data:
#                 data = data["res"]

#             texts = data.get("rec_texts", [])
#             scores = data.get("rec_scores", [])
#             polys = data.get("rec_polys", [])

#             for text, score, polygon in zip(
#                 texts,
#                 scores,
#                 polys,
#             ):

#                 block = OCRBlock(
#                     text=text,
#                     confidence=float(score),
#                     bbox=[
#                         [
#                             float(point[0]),
#                             float(point[1]),
#                         ]
#                         for point in polygon
#                     ],
#                     page=page_number,
#                 )

#                 page_blocks.append(block)
#                 all_ocr_blocks.append(block)

#         page_text = "\n".join(block.text for block in page_blocks)

#         page_texts.append(f"--- PAGE {page_number} ---\n" f"{page_text}")

#     return {
#         "raw_ocr": all_ocr_blocks,
#         "ocr_text": "\n\n".join(page_texts),
#     }


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

    image_paths = state["image_paths"]

    all_blocks: list[OCRBlock] = []
    page_texts: list[str] = []

    for page_number, image_path in enumerate(
        image_paths,
        start=1,
    ):

        page_blocks: list[OCRBlock] = []

        results = ocr.predict(image_path)

        for result in results:

            data = result.json

            if "res" in data:
                data = data["res"]

            texts = data.get("rec_texts", [])
            scores = data.get("rec_scores", [])
            polys = data.get("rec_polys", [])

            for text, score, polygon in zip(
                texts,
                scores,
                polys,
            ):

                block = OCRBlock(
                    text=text,
                    confidence=float(score),
                    bbox=[
                        [
                            float(point[0]),
                            float(point[1]),
                        ]
                        for point in polygon
                    ],
                    page=page_number,
                )

                page_blocks.append(block)
                all_blocks.append(block)

        page_text = "\n".join(block.text for block in page_blocks)

        page_texts.append(f"--- PAGE {page_number} ---\n{page_text}")

    return {
        "raw_ocr": all_blocks,
        "ocr_text": "\n\n".join(page_texts),
    }
