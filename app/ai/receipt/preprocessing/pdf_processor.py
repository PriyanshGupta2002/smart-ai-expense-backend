import os
import tempfile

import fitz


def pdf_to_images(
    pdf_path: str,
) -> list[str]:

    document = fitz.open(pdf_path)

    image_paths: list[str] = []

    try:
        for page_number, page in enumerate(document):

            pixmap = page.get_pixmap(
                matrix=fitz.Matrix(2, 2),
                alpha=False,
            )

            fd, path = tempfile.mkstemp(suffix=f"_page_{page_number + 1}.png")

            os.close(fd)

            pixmap.save(path)

            image_paths.append(path)

    finally:
        document.close()

    return image_paths
