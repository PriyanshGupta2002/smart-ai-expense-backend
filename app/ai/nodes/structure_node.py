from paddleocr import PPStructureV3

from app.ai.receipt.state import ReceiptState

structure = PPStructureV3(
    lang="en",
)


def structure_node(
    state: ReceiptState,
):

    markdown_pages: list[str] = []
    document_json: list[dict] = []

    for image_path in state["image_paths"]:

        result = structure.predict(image_path)[0]

        markdown_pages.append(result.markdown["markdown_texts"])

        document_json.append(result.json)

    return {
        "markdown_text": "\n\n".join(markdown_pages),
        "document_json": document_json,
    }
