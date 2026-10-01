from src.graph.checkpointer import checkpointer


if __name__ == "__main__":
    checkpointer.setup()

    print(
        "LangGraph PostgreSQL checkpoint tables are ready."
    )