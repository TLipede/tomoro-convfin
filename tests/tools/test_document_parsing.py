from pymupdf import Rect

from fin_agent.teams.document_parser import BoundingBox
from fin_agent.utils.document_parsing import convert_relative_to_absolute_coordinates


def test_convert_relative_to_absolute_coordinates():
    bounding_box = BoundingBox(x_min=0, y1=0, x2=100, y2=100, content_type="text")
    page_extents = Rect(0, 0, 100, 100)
    assert convert_relative_to_absolute_coordinates(bounding_box, page_extents) == Rect(
        0, 0, 100, 100
    )
