from pathlib import Path
from textwrap import dedent

import ujson as json
from agno.media import Image

from fin_agent.evaluate.agent import eval_agent
from fin_agent.agents.document_parser.content_summarizer import content_summarizer


EXAMPLES_DIR = (Path(__file__).parent.parent.parent.parent / "examples").resolve()
EXAMPLE_IMAGES = sorted(list(EXAMPLES_DIR.glob("*.png")))
assert EXAMPLES_DIR.exists(), "Examples directory does not exist"


def evaluate_content_summarizer():
    agent_instructions = content_summarizer.instructions
    expected_answers = [
        {
            "sections": [
                {
                    "content_type": "text",
                    "overview": {
                        "text_subtype": "body_text",
                        "first_three_words": "Company's new portable",
                        "last_three_words": "and Financial Condition",
                    },
                },
                {
                    "content_type": "text",
                    "overview": {
                        "text_subtype": "body_text",
                        "first_three_words": "Backlog",
                        "last_three_words": "gross margin percentages",
                    },
                },
                {
                    "content_type": "table",
                    "overview": {
                        "row_headers": [
                            "Net sales",
                            "Cost of sales",
                            "Gross margin",
                            "Gross margin percentage",
                        ]
                    },
                },
            ]
        },
    ]
    examples = [
        {
            "message": {
                "message": "",
                "instructions": agent_instructions,
                "expected_answer": answer,
            },
            "images": [Image(filepath=filepath)],
        }
        for answer, filepath in zip(expected_answers, EXAMPLE_IMAGES[:2])
    ]
    evaluation_criteria = dedent("""The content summarizer should generate an ordered list of sections on the page, from top to bottom.
    The content type of each section should be one of: text, table, or graph.
    The expected answer is a list of sections with the content type and overview.
    The agent should generate an answer which matches all the sections mentioned in the expected answer.
    Score as follows:
    - 0 if the agent does not generate an answer which matches all the sections mentioned in the expected answer
    - 1 if the agent generates an answer which matches all the sections mentioned in the expected answer

    If the agent has captured all the sections, but has marked split or joined some of the sections in the expected answwer 
    (for example, splitting or merging paragraphs), the answer should be treated as correct and scored as 1.
    """)
    evaluations = []
    for example in examples:
        message = example["message"]
        images = example["images"]
        response = content_summarizer.run(message="", images=images)
        message["agent_response"] = response.content.model_dump()
        message["evaluation_criteria"] = evaluation_criteria
        evaluation = eval_agent.run(
            message=json.dumps(message),
            images=images,
        )
        evaluations.append(evaluation)
    return evaluations
