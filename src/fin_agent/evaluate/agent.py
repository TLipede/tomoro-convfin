from typing import Annotated

from agno.agent import Agent
from agno.models.groq import Groq
from pydantic import BaseModel, Field

from fin_agent.settings import app_settings


class EvaluationResult(BaseModel):
    accuracy_score: Annotated[
        int,
        Field(
            ...,
            ge=0,
            le=1,
            description="Accuracy Score between 0 and 1 assigned to the Agent's answer.",
        ),
    ]
    accuracy_reason: Annotated[
        str,
        Field(
            ...,
            description="Detailed reasoning for the accuracy score.",
        ),
    ]


eval_agent = Agent(
    model=Groq(
        id="meta-llama/llama-4-maverick-17b-128e-instruct",
        api_key=app_settings.GROQ_API_KEY,
    ),
    name="Evaluation Agent",
    instructions=[
        "You are an expert evaluation agent, evaluating the accuracy of an AI Agent's answer compared to an expected answer for a given question.",
        "Your task is to provide a detailed analysis and assign a score on a scale of 0 to 1, where 1 indicates a perfect match to the expected answer.",
        "You will be provided with the agent's instructions, the expected answer, and the agent's response.",
        "The user will additionally inform you of the evaluation criteria.",
    ],
    # debug_mode=True,al
    response_model=EvaluationResult,
    structured_outputs=True,
    parse_response=True,
)
