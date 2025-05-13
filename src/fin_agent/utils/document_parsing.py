import base64
from io import BytesIO

import httpx
import PIL
import pymupdf
import tabula
from agno.media import Image

from pymupdf import Rect

from fin_agent.agents.document_parser.models import BoundingBox


def convert_relative_to_absolute_coordinates(
    bounding_box: BoundingBox | None, page_extents: Rect
) -> Rect:
    """
    Convert relative bounding box coordinates to absolute coordinates based on page dimensions.
    If bounding_box is None, the extents of the entire page are returned.

    Args:
        bounding_box (BoundingBox | None): The bounding box with relative coordinates (0-100 range)
        page_extents (Rect): A bounding box encompassing the entire page (xmin, ymin, xmax, ymax)

    Returns:
        Rect: A bounding box with absolute coordinates
    """
    if bounding_box is None:
        return page_extents

    page_width = page_extents[2] - page_extents[0]
    page_height = page_extents[3] - page_extents[1]

    x0 = page_extents[0] + bounding_box.x_min * page_width / 100
    y0 = page_extents[1] + bounding_box.y_min * page_height / 100
    x1 = page_extents[0] + bounding_box.x_max * page_width / 100
    y1 = page_extents[1] + bounding_box.y_max * page_height / 100

    return Rect(x0=x0, y0=y0, x1=x1, y1=y1)


def retrieve_pdf_page(pdf_url: str, page_number: int) -> pymupdf.Page:
    with httpx.Client() as client:
        response = client.get(pdf_url)
        response.raise_for_status()
        pdf_bytes = response.content
        pdf_document = pymupdf.open(stream=BytesIO(pdf_bytes), filetype="pdf")
        return pdf_document.load_page(page_number)


def crop_image(
    image: Image,
    image_width: float,
    image_height: float,
    bounding_box: BoundingBox | dict[str, float],
) -> Image:
    bounding_box = BoundingBox.model_validate(bounding_box)
    absolute_coordinates = dict(
        x_min=image_width / 100 * bounding_box.x_min,
        y_min=image_height / 100 * bounding_box.y_min,
        x_max=image_width / 100 * bounding_box.x_max,
        y_max=image_height / 100 * bounding_box.y_max,
    )
    if image.filepath:
        pil_image = PIL.Image.open(image.filepath)
    elif image.content:
        pil_image = PIL.Image.open(BytesIO(image.content))
    else:
        raise ValueError("Image must have a filepath or content")

    cropped_image = pil_image.crop(
        (
            absolute_coordinates["x_min"],
            absolute_coordinates["y_min"],
            absolute_coordinates["x_max"],
            absolute_coordinates["y_max"],
        )
    )
    buffer = BytesIO()
    cropped_image.save(buffer, format="PNG")
    return Image(content=buffer.getvalue())


def image_from_pdf_page(
    page: pymupdf.Page, bounding_box: BoundingBox | None = None
) -> bytes:
    extents = convert_relative_to_absolute_coordinates(bounding_box, page.rect)

    img = page.get_pixmap(clip=extents).pil_image()
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def b64_str_from_pdf_page(
    page: pymupdf.Page, bounding_box: BoundingBox | None = None
) -> str:
    """
    Convert a PDF page to a base64 encoded PNG image. The media prefix is omitted.

    Args:
        page (pymupdf.Page): The PDF page to convert
        bounding_box (BoundingBox | None, optional): Bounding box to clip the page.
            If None, the entire page is converted. Defaults to None.

    Returns:
        str: Base64 encoded PNG image
    """
    extents = convert_relative_to_absolute_coordinates(bounding_box, page.rect)

    img = page.get_pixmap(clip=extents).pil_image()
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_bytes = buffer.getvalue()
    return base64.b64encode(img_bytes).decode("utf-8")


def image_from_b64_str(b64_str: str) -> Image:
    image_content = base64.b64decode(b64_str.encode("utf-8"))
    return Image(content=image_content)


def b64_str_from_image(image: Image) -> str:
    return base64.b64encode(image.content).decode("utf-8")


def extract_text_from_pdf_page(
    page: pymupdf.Page, bounding_box: BoundingBox | None = None
) -> str:
    extents = convert_relative_to_absolute_coordinates(bounding_box, page.rect)
    return page.get_text(clip=extents)


def extract_tables_from_pdf(
    pdf_url: str,
    page_number: int,
    bounding_box: BoundingBox | None = None,
) -> list[str]:
    if bounding_box is None:
        area = [0, 0, 100, 100]
    else:
        area = [
            bounding_box.y_min,
            bounding_box.x_min,
            bounding_box.y_max,
            bounding_box.x_max,
        ]

    frames = tabula.read_pdf(
        pdf_url,
        pages=page_number,
        area=area,
        relative_area=True,
        pandas_options={"header": None},
    )
    return [f.to_markdown() for f in frames]
