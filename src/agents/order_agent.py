from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from src.tools.order_tools import get_order_tracking


SYSTEM_PROMPT = """
You are the VoltNest Order Support Agent.

You help customers with order shipment and tracking questions.

Rules:
- Use the available tools when real order information is required.
- Never invent order status, tracking numbers, carriers, or delivery information.
- Only answer using information returned by the tools.
- If an order cannot be found, explain that clearly.
- Keep responses concise and helpful.
"""


llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
)


order_agent = create_react_agent(
    model=llm,
    tools=[get_order_tracking],
    prompt=SYSTEM_PROMPT,
)