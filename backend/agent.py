"""
agent.py — CARA's reasoning core.

Implements an agent loop on top of Groq's native tool-calling (function calling)
API. The LLM decides, turn by turn, whether it needs to:
  - search the user's uploaded PDF documents (DocumentSearch)
  - search the live web (WebSearch)
  - run a calculation (Calculator)
  - or just answer directly from its own knowledge

No LangChain agent wrapper is used here — this is a plain tool-calling loop
against the Groq chat completions endpoint, which keeps the control flow
transparent and easy to debug.
"""

import ast
import json
import logging
import operator
import os

from groq import Groq
from tavily import TavilyClient

from rag_engine import search_documents

logger = logging.getLogger("cara.agent")

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
MAX_AGENT_STEPS = 6  # hard cap so a confused loop can't run forever

_groq_client: Groq | None = None
_tavily_client: TavilyClient | None = None


def get_groq_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to your .env file."
            )
        _groq_client = Groq(api_key=api_key)
    return _groq_client


def get_tavily_client() -> TavilyClient | None:
    global _tavily_client
    if _tavily_client is None:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return None
        _tavily_client = TavilyClient(api_key=api_key)
    return _tavily_client


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def tool_document_search(query: str) -> str:
    """Search the user's uploaded PDF documents for relevant passages."""
    try:
        results = search_documents(query, k=4)
    except Exception as exc:  # noqa: BLE001
        logger.exception("DocumentSearch failed")
        return f"DocumentSearch error: {exc}"

    if not results:
        return "No indexed documents found, or no relevant passages matched the query."

    formatted = []
    for i, doc in enumerate(results, start=1):
        formatted.append(f"[Passage {i}]\n{doc}")
    return "\n\n".join(formatted)


def tool_web_search(query: str) -> str:
    """Search the live web via Tavily."""
    client = get_tavily_client()
    if client is None:
        return "WebSearch is unavailable: TAVILY_API_KEY is not configured."

    try:
        response = client.search(query=query, max_results=5, search_depth="basic")
    except Exception as exc:  # noqa: BLE001
        logger.exception("WebSearch failed")
        return f"WebSearch error: {exc}"

    results = response.get("results", [])
    if not results:
        return "No web results found."

    formatted = []
    for r in results:
        title = r.get("title", "Untitled")
        url = r.get("url", "")
        content = r.get("content", "")
        formatted.append(f"{title} ({url})\n{content}")
    return "\n\n".join(formatted)


# Only a safe, restricted subset of operators — no eval() of arbitrary code.
_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numeric constants are allowed.")
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPERATORS:
            raise ValueError(f"Operator {op_type.__name__} is not allowed.")
        return _ALLOWED_OPERATORS[op_type](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPERATORS:
            raise ValueError(f"Operator {op_type.__name__} is not allowed.")
        return _ALLOWED_OPERATORS[op_type](_safe_eval(node.operand))
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")


def tool_calculator(expression: str) -> str:
    """Safely evaluate a numeric arithmetic expression (+, -, *, /, %, **)."""
    try:
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval(tree.body)
        return str(result)
    except Exception as exc:  # noqa: BLE001
        return f"Calculator error: could not evaluate '{expression}' ({exc})"


TOOL_IMPLEMENTATIONS = {
    "DocumentSearch": tool_document_search,
    "WebSearch": tool_web_search,
    "Calculator": tool_calculator,
}

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "DocumentSearch",
            "description": (
                "Search the user's uploaded PDF documents for passages relevant "
                "to the query. Use this when the user's question likely refers "
                "to content they uploaded (reports, papers, contracts, etc.)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to run against the indexed documents.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "WebSearch",
            "description": (
                "Search the live web for current information, news, facts about "
                "recent events, or anything not likely to be in the model's "
                "training data or the uploaded documents."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to run on the web.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "Calculator",
            "description": (
                "Evaluate a numeric arithmetic expression. Use this for any "
                "math computation instead of computing it mentally."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "A numeric expression, e.g. '(23 * 47) / 2'.",
                    }
                },
                "required": ["expression"],
            },
        },
    },
]

SYSTEM_PROMPT = (
    "You are CARA (Conversational AI Research Agent), a helpful assistant. "
    "You have three tools available: DocumentSearch (search the user's uploaded "
    "PDFs), WebSearch (search the live web), and Calculator (evaluate arithmetic). "
    "Decide autonomously, based on the question, whether you need a tool or can "
    "answer directly from your own knowledge. Use DocumentSearch when the question "
    "sounds like it references material the user uploaded. Use WebSearch for "
    "current events, recent facts, or anything time-sensitive. Use Calculator for "
    "any arithmetic rather than computing it yourself. If no tool is needed, "
    "answer directly. Always give a clear, concise, final natural-language answer.\n\n"
    "IMPORTANT — formatting: your answers are shown as plain text and are also "
    "sometimes read aloud by a text-to-speech engine. Never use Markdown tables, "
    "pipe characters, horizontal-rule dashes, headers (#), or bold/italic markup. "
    "Write in plain spoken-style prose and simple sentences. If you're listing "
    "multiple facts (e.g. a timeline of achievements), say them as a short series "
    "of plain sentences ('In 2016 she won silver at the Rio Olympics. In 2019 "
    "she won gold at...') rather than a table."
)


def run_agent(question: str) -> str:
    """Run the tool-calling agent loop and return a final natural-language answer."""
    client = get_groq_client()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    for step in range(MAX_AGENT_STEPS):
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            temperature=0.3,
        )
        choice = response.choices[0]
        msg = choice.message

        tool_calls = getattr(msg, "tool_calls", None)
        if not tool_calls:
            return msg.content or "I don't have an answer for that."

        # Append the assistant's tool-call turn, then each tool result.
        messages.append(
            {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in tool_calls
                ],
            }
        )

        for tc in tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}

            impl = TOOL_IMPLEMENTATIONS.get(name)
            if impl is None:
                result = f"Unknown tool: {name}"
            else:
                arg_value = next(iter(args.values()), "")
                result = impl(arg_value)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                }
            )

        logger.info("Agent step %d used tools: %s", step, [tc.function.name for tc in tool_calls])

    # Ran out of steps — ask once more for a final answer with no tools offered.
    final = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages + [
            {
                "role": "user",
                "content": "Please give your best final answer now, without using any more tools.",
            }
        ],
        temperature=0.3,
    )
    return final.choices[0].message.content or "I wasn't able to reach a final answer."
