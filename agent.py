# agent.py — direct Groq API approach, no LangChain agent wrapper
import os
import json
from groq import Groq
from dotenv import load_dotenv
from tavily import TavilyClient
from rag_engine import load_vector_store, search_documents

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
vector_store = load_vector_store()

# ── Tool functions ──
def rag_search(query: str) -> str:
    context = search_documents(query, vector_store)
    return context if context else "No relevant info found in documents."

def web_search(query: str) -> str:
    results = tavily.search(query=query, max_results=3)
    output = ""
    for r in results["results"]:
        output += f"Source: {r['url']}\n{r['content']}\n\n"
    return output

def calculator(expression: str) -> str:
    try:
        return f"Result: {eval(expression)}"
    except:
        return "Invalid expression."

# ── Tool definitions sent to Groq ──
tools = [
    {
        "type": "function",
        "function": {
            "name": "DocumentSearch",
            "description": "Search uploaded PDF documents and notes. Use for questions about uploaded study material.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "WebSearch",
            "description": "Search the internet for current news, real-time data, recent events.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "Calculator",
            "description": "Evaluate math expressions like 85000 * 0.15",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Math expression to evaluate"}
                },
                "required": ["expression"]
            }
        }
    }
]

# ── Tool executor ──
def execute_tool(tool_name: str, tool_args: dict) -> str:
    if tool_name == "DocumentSearch":
        return rag_search(tool_args["query"])
    elif tool_name == "WebSearch":
        return web_search(tool_args["query"])
    elif tool_name == "Calculator":
        return calculator(tool_args["expression"])
    return "Unknown tool."

# ── Main agent function ──
def run_agent(question: str) -> str:
    messages = [
        {
            "role": "system",
            "content": "You are CARA, a helpful AI research agent. Use tools when needed. After getting tool results, give a clear final answer."
        },
        {
            "role": "user",
            "content": question
        }
    ]

    print(f"\nThought: Processing question — '{question}'")

    # Agentic loop — keep going until model gives final answer
    for i in range(5):
        response = groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=1024
        )

        message = response.choices[0].message

        # If no tool call — we have the final answer
        if not message.tool_calls:
            print(f"Final Answer ready after {i+1} step(s)")
            return message.content

        # Process each tool call
        messages.append({
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in message.tool_calls
            ]
        })

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            print(f"Action: {tool_name}({tool_args})")
            result = execute_tool(tool_name, tool_args)
            print(f"Observation: {result[:150]}...")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })

    return "Could not complete the task within step limit."