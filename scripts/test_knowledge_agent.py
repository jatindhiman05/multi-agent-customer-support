from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()
from src.agents.knowledge_agent import knowledge_agent


questions = [
    "How long do I have to return a product?",
    "Does my warranty cover accidental damage?",
    "My package says delivered but I cannot find it. What should I do?",
]


for question in questions:

    print("\n" + "=" * 70)
    print(f"USER: {question}")
    print("=" * 70)

    response = knowledge_agent.invoke(
        {
            "messages": [
                HumanMessage(content=question)
            ]
        }
    )

    print("\nAGENT:")
    print(response["messages"][-1].content)