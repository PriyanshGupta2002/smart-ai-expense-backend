from langgraph.graph import StateGraph, START, END
from app.ai.receipt.state import ReceiptState
from app.ai.nodes.ocr_node import ocr_node
from app.ai.nodes.layout_node import layout_node
from app.ai.nodes.classification_node import classification_node
from app.ai.nodes.extraction_node import extraction_node
from app.ai.nodes.normalize_node import normalization_node
from app.ai.nodes.validation_node import validation_node
from app.ai.nodes.retry_node import retry_extraction, retry_ocr
from app.ai.nodes.insert_to_db_node import insert_to_db_node
from app.ai.nodes.route_after_validation_node import route_after_validation

graph = StateGraph(ReceiptState)

graph.add_node("ocr_node", ocr_node)
graph.add_node(
    "layout",
    layout_node,
)
graph.add_node("extraction_node", extraction_node)
graph.add_node("classification_node", classification_node)
graph.add_node("validation_node", validation_node)
graph.add_node("normalization_node", normalization_node)
graph.add_node("retry_ocr", retry_ocr)
graph.add_node("retry_extraction", retry_extraction)
graph.add_node("insert_to_db_node", insert_to_db_node)


graph.add_edge(START, "ocr_node")
graph.add_edge("ocr_node", "layout")
graph.add_edge("layout", "extraction_node")
graph.add_edge("extraction_node", "classification_node")
graph.add_edge("classification_node", "validation_node")
graph.add_conditional_edges(
    "validation_node",
    route_after_validation,
    {
        "failed": END,
        "retry_ocr": "retry_ocr",
        "retry_extraction": "retry_extraction",
        "normalize": "normalization_node",
    },
)

graph.add_edge("retry_ocr", "ocr_node")
graph.add_edge("retry_extraction", "extraction_node")

graph.add_edge("normalization_node", "insert_to_db_node")
graph.add_edge("insert_to_db_node", END)


workflow = graph.compile()
