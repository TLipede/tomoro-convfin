from agno.playground import Playground, serve_playground_app

from fin_agent.settings import app_settings
from fin_agent.agents.action_generation.action_planner import action_planner
from fin_agent.agents.document_parser.bbox_generator import bbox_generator
from fin_agent.workflows.extract_document_context import PdfContextExtractionWorkflow

app = Playground(
    agents=[
        action_planner,
        bbox_generator,
    ],
    workflows=[
        PdfContextExtractionWorkflow(),
    ],
).get_app(use_async=True)


def run_playground():
    serve_playground_app("fin_agent.main:app", reload=app_settings.RELOAD_ENABLED)
