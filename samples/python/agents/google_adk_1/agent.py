import json
import random
import httpx
from typing import Any, AsyncIterable, Dict, Optional
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.tool_context import ToolContext
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.models.lite_llm import LiteLlm
from google.genai import types

# Local cache of created request_ids for demo purposes.
request_ids = set()


def approval_leave(
        leave_date: str = "04/12/2024",
):
    """Use this to approval leave.

    Args:
        leave_date: The leave date of employee  (e.g., "04/12/2024").

    Returns:
        A dictionary containing the approval result.
    """
    return {"approval_result":"Approved"}


class LeaveApprovalAgent:
    """An agent that handles reimbursement requests."""

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self._agent = self._build_agent()
        self._user_id = "remote_agent"
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    def invoke(self, query, session_id) -> str:
        session = self._runner.session_service.get_session(
            app_name=self._agent.name, user_id=self._user_id, session_id=session_id
        )
        content = types.Content(
            role="user", parts=[types.Part.from_text(text=query)]
        )
        if session is None:
            session = self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )
        events = self._runner.run(
            user_id=self._user_id, session_id=session.id, new_message=content
        )
        if not events or not events[-1].content or not events[-1].content.parts:
            return ""
        return "\n".join([p.text for p in events[-1].content.parts if p.text])

    async def stream(self, query, session_id) -> AsyncIterable[Dict[str, Any]]:
        session = self._runner.session_service.get_session(
            app_name=self._agent.name, user_id=self._user_id, session_id=session_id
        )
        content = types.Content(
            role="user", parts=[types.Part.from_text(text=query)]
        )
        if session is None:
            session = self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )
        async for event in self._runner.run_async(
                user_id=self._user_id, session_id=session.id, new_message=content
        ):
            if event.is_final_response():
                response = ""
                if (
                        event.content
                        and event.content.parts
                        and event.content.parts[0].text
                ):
                    response = "\n".join([p.text for p in event.content.parts if p.text])
                elif (
                        event.content
                        and event.content.parts
                        and any([True for p in event.content.parts if p.function_response])):
                    response = next((p.function_response.model_dump() for p in event.content.parts))
                yield {
                    "is_task_complete": True,
                    "content": response,
                }
            else:
                yield {
                    "is_task_complete": False,
                    "updates": "Processing the leave approval request...",
                }

    def _build_agent(self) -> LlmAgent:
        """Builds the LLM agent for the reimbursement agent."""
        return LlmAgent(
            model="gemini-2.0-flash-001",
            # model=LiteLlm("openai/meta-llama/Llama-3.1-8B-Instruct"),
            name="leave_approval_agent",
            description=(
                "This agent handles the leave approval for the employees"
                " given the date of the leave."
            ),
            instruction="""
    You are an agent who handle the leave approval process for employees.

    When you receive an leave approval request, you should ask for the date.

    If you have all of the information, you can then use approval_leave() to approval for the employee.
    """,
            tools=[
                approval_leave,
            ],
        )
