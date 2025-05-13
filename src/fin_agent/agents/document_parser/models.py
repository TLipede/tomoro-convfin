from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator


### Content Summarizer ###
class TextSectionOverview(BaseModel):
    """To be used when content_type is general text data."""

    text_subtype: Annotated[
        str,
        Field(
            description="The type of text content in the block, e.g. header/footer/body_text/alt_text/title"
        ),
    ]
    first_three_words: str
    last_three_words: str


class TableSectionOverview(BaseModel):
    column_headers: list[str] | None = None
    row_headers: list[str] | None = None
    table_description: str | None = None


class GraphSectionOverview(BaseModel):
    graph_description: str | None = None
    axis_labels: list[str]


class PageSection(BaseModel):
    """A section of content on a page."""

    content_type: Annotated[
        Literal["table", "graph"] | str,
        Field(
            description="""
            The type of content in the block. This can be one of:
            - table: a table
            - graph: a graph
            - other: any other type of (text) content
            """
        ),
    ]
    overview: Annotated[
        TextSectionOverview | TableSectionOverview | GraphSectionOverview,
        Field(
            description="An overview of the content within the section.",
        ),
    ]

    # Included to encourage the agent to provide non-overlapping sections
    # Not used downstream
    y_min: Annotated[
        float,
        Field(
            description="The y position of the top of the section as a percentage of the page height",
            ge=0,
            le=100,
        ),
    ]
    y_max: Annotated[
        float,
        Field(
            description="The y position of the bottom of the section as a percentage of the page height",
            ge=0,
            le=100,
        ),
    ]


class ContentSummary(BaseModel):
    """An ordered summary of the types of content on a page."""

    sections: Annotated[
        list[PageSection],
        Field(
            description="An ordered list of sections on the page from top to bottom."
        ),
    ]


### Bounding Box Inspector ###
class BoundingBox(BaseModel):
    x_min: Annotated[
        float,
        Field(
            description="The x position of the top left corner of the bounding box as a percentage of the page width",
            ge=0,
            le=100,
        ),
    ]
    y_min: Annotated[
        float,
        Field(
            description="The y position of the top left corner of the bounding box as a percentage of the page height",
            ge=0,
            le=100,
        ),
    ]
    x_max: Annotated[
        float,
        Field(
            description="The x position of the bottom right corner of the bounding box as a percentage of the page width",
            ge=0,
            le=100,
        ),
    ]
    y_max: Annotated[
        float,
        Field(
            description="The y position of the bottom right corner of the bounding box as a percentage of the page height",
            ge=0,
            le=100,
        ),
    ]

    @model_validator(mode="after")
    def check_coordinates(self):
        if self.x_min <= 1 and self.x_max <= 1 and self.y_min <= 1 and self.y_max <= 1:
            self.x_min *= 100
            self.x_max *= 100
            self.y_min *= 100
            self.y_max *= 100
        return self
