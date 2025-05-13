from agno.agent import Agent
from agno.models.groq import Groq
from agno.storage.sqlite import SqliteStorage
from agno.tools.calculator import CalculatorTools
from agno.tools.reasoning import ReasoningTools
from pydantic import BaseModel

from fin_agent.settings import app_settings


class ActionPlan(BaseModel):
    reasoning: str
    tool_calls: list[dict[str, str]]


action_planner = Agent(
    model=Groq(
        id="meta-llama/llama-4-scout-17b-16e-instruct",
        api_key=app_settings.GROQ_API_KEY,
        temperature=0,
    ),
    role="Action Planner",
    tools=[
        CalculatorTools(
            include_tools=[
                "add",
                "subtract",
                "multiply",
                "divide",
            ]
        ),
        ReasoningTools(),
    ],
    instructions=[
        "You are a part of a team of expert financial analysts.",
        "You are an action planner.",
        "You will be presented with a page from a financial report.",
        "The page will include a table of data and the text before and after the table.",
        "You will be asked questions about the data presented with the document.",
        "Your task is to generate the series of tool calls needed for an agent to perform the calculation.",
        "Use the reasoning tools to break down the problem and outline your thought process.",
        "Do not actually run any calculations.",
        "Provide your answer as a JSON object with the following keys:",
        "- reasoning: A summary of your reasoning process.",
        "- tool_calls: An ordered list of tool call references (in order of execution) to perform the calculation. Do not include reasoning tools. Each tool call reference should have the following keys:",
        "    - tool: The name of the tool to use.",
        "    - args: The arguments to pass to the tool.",
        "",
        "Refer to the result of previous tool calls in the args of subsequent tool calls using the template variable {{result_<idx>}} where <idx> is the index of the tool call.",
        "Make sure all tool calls are ordered and that the arguments of each tool call are numeric.",
        "Only return the JSON object, do not include any additional text.",
        "Example response:",
        """\n{"reasoning": ..., "tool_calls":  [{"tool": "add", "args": {"a": 1, "b": 2}}, {"tool": "subtract", "args": {"a": {{result_0}}, "b": 2}}]}""",
        "If you have insufficient information to perform the calculation, return an empty list for tool_calls and explain that you require more information in your reasoning.",
    ],
    show_tool_calls=True,
    debug_mode=True,
    add_history_to_messages=True,
    read_chat_history=True,
    storage=SqliteStorage(table_name="analyst", db_file="/tmp/fin_agent.db"),
)

action_planner_advanced = Agent(
    model=Groq(
        id="meta-llama/llama-4-scout-17b-16e-instruct",
        api_key=app_settings.GROQ_API_KEY,
        temperature=0,
    ),
    role="Action Planner",
    tools=[
        CalculatorTools(
            include_tools=[
                "add",
                "subtract",
                "multiply",
                "divide",
            ]
        ),
        # ReasoningTools(),
    ],
    instructions=[
        "You are a part of a team of expert financial analysts.",
        "You are an action planner.",
        "You will be presented with a page from a financial report, along with a question to answer.",
        "The page will include some article text.",
        "The page may also include some tables of data.",
        "Some charts or graphs may also be provided as images.",
        "Your task is to generate the series of tool calls needed for an agent to perform the calculation.",
        "Use the reasoning tools to break down the problem and outline your thought process.",
        "Do not actually run any calculations.",
        "Provide your answer as a JSON object with the following keys:",
        "- reasoning: A summary of your reasoning process.",
        "- tool_calls: An ordered list of tool call references (in order of execution) to perform the calculation. Do not include reasoning tools. Each tool call reference should have the following keys:",
        "    - tool: The name of the tool to use.",
        "    - args: The arguments to pass to the tool.",
        "",
        "Do not include any reasoning tools in the tool_calls.",
        "Refer to the result of previous tool calls in the args of subsequent tool calls using the template variable {{result_<idx>}} where <idx> is the index of the tool call.",
        "Make sure all tool calls are ordered and that the arguments of each tool call are numeric.",
        "Only return the JSON object, do not include any additional text.",
        "Example response:",
        """\n{"reasoning": ..., "tool_calls":  [{"tool": "add", "args": {"a": 1, "b": 2}}, {"tool": "subtract", "args": {"a": {{result_0}}, "b": 2}}]}""",
        "If you have insufficient information to perform the calculation, return an empty list for tool_calls and explain that you require more information in your reasoning.",
    ],
    show_tool_calls=True,
    debug_mode=True,
    add_history_to_messages=True,
    read_chat_history=True,
    storage=SqliteStorage(table_name="analyst", db_file="/tmp/fin_agent.db"),
)
