from __future__ import annotations

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)

from src.core.context import (
    emit_token,
    get_token_sink,
)
from src.core.llm import create_chat_groq
from src.knowledge.schema import KnowledgeEvidence
from src.tools.knowledge_tools import retrieve_knowledge


CONTEXTUALIZATION_PROMPT = """
You rewrite follow-up customer questions into standalone search queries
for VoltNest's static company knowledge base.

Use the conversation only to resolve references in the latest customer
question.

Rules:

- Preserve the customer's exact intent.
- Add only context clearly established by the conversation.
- Do not answer the question.
- Do not invent facts.
- Do not add customer-specific live state.
- Return only the standalone search query.
- Keep it concise.

Example:

Previous customer question:
Does the VoltNest warranty cover accidental damage?

Latest customer question:
What kinds of issues are covered then?

Standalone query:
What kinds of issues are covered by the VoltNest limited warranty?
"""


ANSWER_PROMPT = """
You are the VoltNest Knowledge Support Agent.

Your responsibility is to answer questions about VoltNest's static,
authoritative company information.

You will receive authoritative evidence retrieved from VoltNest's
knowledge base.

GROUNDING RULES

1. Treat the supplied evidence as the only authoritative source for
   VoltNest policy and company-information facts.

2. Answer only with facts supported by the supplied evidence.

3. Never invent or infer missing VoltNest:
   - policies
   - eligibility decisions
   - timelines
   - procedures
   - guarantees
   - exceptions
   - company actions

4. Say that information could not be found only when:
   - no evidence was supplied, or
   - the supplied evidence genuinely does not address the question.

5. Distinguish explicit negative evidence from missing evidence.

   If the evidence explicitly states that something is not covered,
   not allowed, not eligible, excluded, unavailable, or prohibited,
   answer that directly.

LIVE DATA BOUNDARY

The supplied knowledge evidence contains general company information.
It does not establish the current state of a specific customer's:

- order
- shipment
- payment
- refund
- return
- cancellation
- account
- support ticket

Do not claim that a specific order, payment, shipment, refund, return,
or account has a particular status from policy evidence.

RESPONSE STYLE

- Give the answer directly.
- Keep the response concise and customer-friendly.
- Do not mention embeddings, FAISS, pgvector, vector search, chunks,
  retrieval scores, internal agents, or internal architecture.
"""


FOLLOW_UP_MARKERS = (
    " then",
    "that",
    "those",
    "these",
    " it ",
    " they ",
    " them ",
    "what about",
    "how about",
    "and what",
    "and how",
)


llm = create_chat_groq()


def _latest_user_message(
    messages: list[BaseMessage],
) -> str:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            content = str(
                message.content
            ).strip()

            if content:
                return content

    raise ValueError(
        "Knowledge agent requires a user message."
    )


def _needs_contextualization(
    query: str,
) -> bool:
    normalized = (
        f" {query.lower().strip()} "
    )

    return any(
        marker in normalized
        for marker in FOLLOW_UP_MARKERS
    )


def _recent_conversation(
    messages: list[BaseMessage],
    *,
    max_messages: int = 4,
) -> str:
    relevant = messages[:-1][
        -max_messages:
    ]

    lines: list[str] = []

    for message in relevant:
        content = str(
            message.content
        ).strip()

        if not content:
            continue

        if isinstance(
            message,
            HumanMessage,
        ):
            role = "Customer"
        elif isinstance(
            message,
            AIMessage,
        ):
            role = "Support"
        else:
            continue

        lines.append(
            f"{role}: {content}"
        )

    return "\n".join(lines)


def _standalone_query(
    messages: list[BaseMessage],
) -> str:
    """
    Produce a retrieval query.

    This is internal model work and must never be
    exposed through the customer token stream.
    """

    current_query = (
        _latest_user_message(
            messages
        )
    )

    if not _needs_contextualization(
        current_query
    ):
        return current_query

    context = _recent_conversation(
        messages
    )

    if not context:
        return current_query

    response = llm.invoke(
        [
            SystemMessage(
                content=(
                    CONTEXTUALIZATION_PROMPT
                )
            ),
            HumanMessage(
                content=(
                    "Conversation:\n"
                    f"{context}\n\n"
                    "Latest customer question:\n"
                    f"{current_query}"
                )
            ),
        ]
    )

    rewritten = str(
        response.content
    ).strip()

    return (
        rewritten
        or current_query
    )


def _format_evidence(
    evidence: list[
        KnowledgeEvidence
    ],
) -> str:
    if not evidence:
        return (
            "No relevant authoritative "
            "knowledge evidence was found."
        )

    sections: list[str] = []

    for position, item in enumerate(
        evidence,
        start=1,
    ):
        sections.append(
            "\n".join(
                [
                    f"Evidence {position}",
                    (
                        f"Title: "
                        f"{item.title}"
                    ),
                    (
                        f"Section: "
                        f"{item.heading}"
                    ),
                    (
                        "Content:\n"
                        f"{item.content}"
                    ),
                ]
            )
        )

    return "\n\n".join(
        sections
    )


def _generate_answer(
    *,
    current_question: str,
    evidence_text: str,
) -> str:
    """
    Generate the customer-facing grounded answer.

    When no request-scoped token sink exists, preserve
    the normal synchronous invoke() behavior.

    When a token sink exists, stream only this final
    customer-facing generation and reconstruct the exact
    authoritative answer from those same chunks.
    """

    answer_messages = [
        SystemMessage(
            content=ANSWER_PROMPT
        ),
        HumanMessage(
            content=(
                "Customer question:\n"
                f"{current_question}\n\n"
                "Authoritative VoltNest evidence:\n"
                f"{evidence_text}"
            )
        ),
    ]

    if get_token_sink() is None:
        response = llm.invoke(
            answer_messages
        )

        return str(
            response.content
        ).strip()

    chunks: list[str] = []

    for chunk in llm.stream(
        answer_messages
    ):
        content_piece = (
            chunk.content
        )

        if not isinstance(
            content_piece,
            str,
        ):
            continue

        if not content_piece:
            continue

        chunks.append(
            content_piece
        )

        emit_token(
            content_piece
        )

    return "".join(
        chunks
    ).strip()


def run_knowledge_agent(
    messages: list[BaseMessage],
) -> AIMessage:
    """
    Deterministic retrieve-then-generate knowledge
    pipeline.

    Retrieval always happens before answer generation.
    Follow-up questions are contextualized only when
    needed.

    Only the final customer-facing answer generation
    participates in HTTP token streaming.
    """

    current_question = (
        _latest_user_message(
            messages
        )
    )

    retrieval_query = (
        _standalone_query(
            messages
        )
    )

    evidence = retrieve_knowledge(
        retrieval_query
    )

    evidence_text = (
        _format_evidence(
            evidence
        )
    )

    answer = _generate_answer(
        current_question=(
            current_question
        ),
        evidence_text=(
            evidence_text
        ),
    )

    return AIMessage(
        content=answer
    )