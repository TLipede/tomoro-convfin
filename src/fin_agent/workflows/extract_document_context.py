from textwrap import dedent
from typing import Any

import pymupdf
import ujson as json
from agno.agent import RunResponse
from agno.media import Image
from agno.utils.log import logger
from agno.workflow import Workflow
from pydantic import BaseModel, TypeAdapter, field_serializer, field_validator

from fin_agent.utils.document_parsing import (
    b64_str_from_image,
    b64_str_from_pdf_page,
    image_from_b64_str,
    retrieve_pdf_page,
)
from fin_agent.agents.document_parser.models import BoundingBox
from fin_agent.agents.document_parser.bbox_inspector import bbox_inspector
from fin_agent.agents.document_parser.content_summarizer import content_summarizer
from fin_agent.utils.document_parsing import crop_image


class ParsedPage(BaseModel):
    page_content: list[str | list[str]]
    page_images: list[Image | str]

    @field_validator("page_images", mode="before")
    @classmethod
    def validate_page_images(cls, v):
        images = []
        for image in v:
            if isinstance(image, str):
                images.append(image_from_b64_str(image))
            else:
                images.append(image)
        return images

    @field_serializer("page_images", return_type=list[str])
    @classmethod
    def serialize_page_images(cls, page_images: list[Image]):
        images = [b64_str_from_image(image) for image in page_images]
        return images


def construct_inspector_message(
    section: dict,
    full_page_image: Image,
    page: pymupdf.Page,
    suggested_bbox: BoundingBox | None = None,
    previous_choices: list[BoundingBox] | None = None,
) -> dict[str, Any]:
    message = {
        "intended_data": {
            "content_type": section["content_type"],
            "overview": section["overview"],
        },
    }
    if suggested_bbox:
        message["cropped_bounding_box"] = suggested_bbox.model_dump()
    else:
        message["cropped_bounding_box"] = {
            "x_min": 0,
            "x_max": 100,
            "y_min": 0,
            "y_max": 100,
        }

    if not previous_choices:
        previous_choices = []

    message["previous_choices"] = previous_choices
    image_width, image_height = page.rect[2], page.rect[3]
    cropped_image = crop_image(
        image=full_page_image,
        image_width=image_width,
        image_height=image_height,
        bounding_box=message["cropped_bounding_box"],
    )
    images = [cropped_image]

    return {"message": json.dumps(message), "images": images}


class PdfContextExtractionWorkflow(Workflow):
    description = dedent(
        """A workflow which extracts context in and easy to digest format from a 
        page of a PDF annual financial report."""
    )

    content_summarizer = content_summarizer
    bbox_inspector = bbox_inspector

    def run(
        self,
        message: str,
        overwrite_cache: bool = False,
        n_max_bbox_iterations: int = 3,
    ):
        message_dict = json.loads(message)

        page_number = message_dict["page_number"]
        pdf_url = message_dict["pdf_url"]

        cache_key = f"{pdf_url}_{page_number}"
        run_cache = self.session_state.get(cache_key, {})

        if run_cache and run_cache.get("output") and not overwrite_cache:
            logger.info(
                f"Using cached result for page {page_number} from PDF {pdf_url}"
            )
            parsed_page = TypeAdapter(ParsedPage).validate_python(run_cache["output"])
            return RunResponse(run_id=self.run_id, content=parsed_page)

        logger.info(f"Retrieving page {page_number} from PDF {pdf_url}")
        page = retrieve_pdf_page(pdf_url, page_number)
        logger.info(f"Retrieved page {page_number} from PDF {pdf_url}")

        image_str = b64_str_from_pdf_page(page)
        full_page_image = image_from_b64_str(image_str)
        run_cache["full_page_image"] = image_str

        content_summarizer_response = self.content_summarizer.run(
            message="Summarize the content of this page.",
            images=[full_page_image],
        )

        run_cache["content_summarizer_response"] = content_summarizer_response.content
        section_bounds = []
        for section in content_summarizer_response.content.sections:
            message = construct_inspector_message(
                section=section.model_dump(),
                full_page_image=full_page_image,
                page=page,
            )
            previous_choices = []
            for iteration in range(n_max_bbox_iterations):
                inspector_response = self.bbox_inspector.run(
                    message=message["message"],
                    images=message["images"],
                ).content
                if (
                    inspector_response.is_accurate
                    or iteration == n_max_bbox_iterations - 1
                ):
                    section_bounds.append(
                        {
                            "bounding_box": inspector_response.suggested_bounding_box,
                            "content_type": section.content_type,
                            "overview": section.overview,
                        }
                    )
                    break
                else:
                    previous_choices.append(
                        inspector_response.suggested_bounding_box.model_dump()
                    )
                    message = construct_inspector_message(
                        section=section.model_dump(),
                        full_page_image=full_page_image,
                        page=page,
                        suggested_bbox=inspector_response.suggested_bounding_box,
                        previous_choices=previous_choices,
                    )

        return RunResponse(run_id=self.run_id, content=run_cache["output"])
