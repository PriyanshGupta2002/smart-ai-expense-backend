import paddle
from paddleocr import PPStructureV3

from app.ai.receipt.state import ReceiptState

print("=" * 50)
print(f"Paddle Version: {paddle.__version__}")
print(f"CUDA Available: {paddle.is_compiled_with_cuda()}")
print(f"Device: {paddle.device.get_device()}")
print("=" * 50)

structure = PPStructureV3(
    lang="en",
)


def structure_node(state: ReceiptState):

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