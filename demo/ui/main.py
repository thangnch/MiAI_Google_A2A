
"""A UI solution and host service to interact with the agent framework.
run:
  uv main.py
"""
import asyncio
import os
import threading

import mesop as me

from state.state import AppState
from components.page_scaffold import page_scaffold
from pages.home import home_page_content
from pages.agent_list import agent_list_page
from pages.conversation import conversation_page
from pages.event_list import event_list_page
from pages.settings import settings_page_content
from pages.task_list import task_list_page
from state import host_agent_service
from service.server.server import ConversationServer

from fastapi import FastAPI, APIRouter
from fastapi.middleware.wsgi import WSGIMiddleware
from dotenv import load_dotenv

load_dotenv()

def on_load(e: me.LoadEvent):  # pylint: disable=unused-argument
    """On load event"""
    state = me.state(AppState)
    me.set_theme_mode(state.theme_mode)
    if "conversation_id" in me.query_params:
      state.current_conversation_id = me.query_params["conversation_id"]
    else:
      state.current_conversation_id = ""

# Policy to allow the lit custom element to load
security_policy=me.SecurityPolicy(
    allowed_script_srcs=[
      'https://cdn.jsdelivr.net',
    ]
  )


@me.page(
    path="/",
    title="Chat",
    on_load=on_load,
    security_policy=security_policy,
)
def home_page():
    """Main Page"""
    state = me.state(AppState)
    with page_scaffold():  # pylint: disable=not-context-manager
        home_page_content(state)


@me.page(
    path="/agents",
    title="Agents",
    on_load=on_load,
    security_policy=security_policy,
)
def another_page():
    """Another Page"""
    agent_list_page(me.state(AppState))


@me.page(
    path="/conversation",
    title="Conversation",
    on_load=on_load,
    security_policy=security_policy,
)
def chat_page():
    """Conversation Page."""
    conversation_page(me.state(AppState))

@me.page(
    path="/event_list",
    title="Event List",
    on_load=on_load,
    security_policy=security_policy,
)
def event_page():
    """Event List Page."""
    event_list_page(me.state(AppState))


@me.page(
    path="/settings",
    title="Settings",
    on_load=on_load,
    security_policy=security_policy,
)
def settings_page():
    """Settings Page."""
    settings_page_content()


@me.page(
    path="/task_list",
    title="Task List",
    on_load=on_load,
    security_policy=security_policy,
)
def task_page():
    """Task List Page."""
    task_list_page(me.state(AppState))

# Setup the server global objects
app = FastAPI()
router = APIRouter()
agent_server = ConversationServer(router)
app.include_router(router)

app.mount(
    "/",
    WSGIMiddleware(
        me.create_wsgi_app(debug_mode=os.environ.get("DEBUG_MODE", "") == "true")
    ),
)

if __name__ == "__main__":    
    # if not os.getenv("GOOGLE_API_KEY"):
    #     print("GOOGLE_API_KEY environment variable not set.")
    #     exit(1)

    import uvicorn
    # Setup the connection details, these should be set in the environment
    host = os.environ.get("A2A_UI_HOST", "0.0.0.0")
    port = int(os.environ.get("A2A_UI_PORT", "12000"))

    # Set the client to talk to the server
    host_agent_service.server_url = f"http://{host}:{port}"

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        reload_includes=["*.py", "*.js"],
        timeout_graceful_shutdown=0,
    )
