import asyncio
import base64
import threading
import os
import uuid
from typing import Any
from fastapi import APIRouter
from fastapi import Request, Response
from common.types import Message, Task, FilePart, FileContent
from .in_memory_manager import InMemoryFakeAgentManager
from .application_manager import ApplicationManager
from .adk_host_manager import ADKHostManager, get_message_id
from service.types import (
    Conversation,
    Event,
    CreateConversationResponse,
    ListConversationResponse,
    SendMessageResponse,
    MessageInfo,
    ListMessageResponse,
    PendingMessageResponse,
    ListTaskResponse,
    RegisterAgentResponse,
    ListAgentResponse,
    GetEventResponse
)


adk = ADKHostManager()


async def _send_message(request: Request):
    message_data = await request.json()
    message = Message(**message_data['params'])
    message = adk.sanitize_message(message)
    await adk.process_message(message)
    return SendMessageResponse(result=MessageInfo(
        message_id=message.metadata['message_id'],
        conversation_id=message.metadata['conversation_id'] if 'conversation_id' in message.metadata else '',
    ))