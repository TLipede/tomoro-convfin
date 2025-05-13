from typing import Annotated
from agno.agent import Agent
from agno.models.groq import Groq
from pydantic import BaseModel, Field

from fin_agent.settings import app_settings
from fin_agent.agents.document_parser.models import PageSection


class ContentSummarizerResponse(BaseModel):
    sections: Annotated[
        list[PageSection],
        Field(
            description="An ordered list of sections on the page, from top to bottom."
        ),
    ]


content_summarizer = Agent(
    model=Groq(
        id="meta-llama/llama-4-scout-17b-16e-instruct",
        api_key=app_settings.GROQ_API_KEY,
        temperature=0,
        top_p=1,
    ),
    name="Content Summarizer",
    instructions=[
        "You are an expert content summarizer, summarizing financial documents.",
        "You will be presented with a single page image from a company financial report.",
        "Your task is to scan the page from top to bottom and generate an ordered list of sections on the page.",
        "Look through the image very carefully and make sure you capture all the sections.",
        "The content type of each section should be one of: text, table, or graph.",
        "The overview of each section should be a short description of the content within the section.",
        "For text sections, try to separate by paragraph.",
        "Sections should be ordered from top to bottom and should not overlap.",
        "When suggesting y_min and y_max, choose bounds that are as large as possible.",
    ],
    # debug_mode=True,
    response_model=ContentSummarizerResponse,
    structured_outputs=True,
    parse_response=True,
)
