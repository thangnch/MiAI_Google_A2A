from common.client import A2AClient, A2ACardResolver
from common.types import TaskState, Task
from common.utils.push_notification_auth import PushNotificationReceiverAuth
import asyncclick as click
import asyncio
from uuid import uuid4
import urllib

@click.command()
@click.option("--agent", default="http://localhost:10003")
@click.option("--session", default=0)
@click.option("--history", default=False)
@click.option("--use_push_notifications", default=False)
@click.option("--push_notification_receiver", default="http://localhost:5000")
async def cli(agent, session, history, use_push_notifications: bool, push_notification_receiver: str):
    card_resolver = A2ACardResolver(agent)
    card = card_resolver.get_agent_card()

    print("======= Agent Card ========")
    print(card.model_dump_json(exclude_none=True))

    notif_receiver_parsed = urllib.parse.urlparse(push_notification_receiver)
    notification_receiver_host = notif_receiver_parsed.hostname
    notification_receiver_port = notif_receiver_parsed.port

    if use_push_notifications:
        from hosts.cli.push_notification_listener import PushNotificationListener
        notification_receiver_auth = PushNotificationReceiverAuth()
        await notification_receiver_auth.load_jwks(f"{agent}/.well-known/jwks.json")

        push_notification_listener = PushNotificationListener(
            host = notification_receiver_host,
            port = notification_receiver_port,
            notification_receiver_auth=notification_receiver_auth,
        )
        push_notification_listener.start()
        
    client = A2AClient(agent_card=card)
    if session == 0:
        sessionId = uuid4().hex
    else:
        sessionId = session

    continue_loop = True
    streaming = card.capabilities.streaming

    while continue_loop:
        taskId = uuid4().hex
        print("=========  starting a new task ======== ")
        continue_loop = await completeTask(client, streaming, use_push_notifications, notification_receiver_host, notification_receiver_port, taskId, sessionId)

        if history and continue_loop:
            print("========= history ======== ")
            task_response = await client.get_task({"id": taskId, "historyLength": 10})
            print(task_response.model_dump_json(include={"result": {"history": True}}))

async def completeTask(client: A2AClient, streaming, use_push_notifications: bool, notification_receiver_host: str, notification_receiver_port: int, taskId, sessionId):
    prompt = click.prompt(
        "\nWhat do you want to send to the agent? (:q or quit to exit)"
    )
    if prompt == ":q" or prompt == "quit":
        return False

    payload = {
        "id": taskId,
        "sessionId": sessionId,
        "acceptedOutputModes": ["text"],
        "message": {
            "role": "user",
            "parts": [
                {
                    "type": "text",
                    "text": prompt,
                }
            ],
        },
    }

    # if use_push_notifications:
    #     payload["pushNotification"] = {
    #         "url": f"http://{notification_receiver_host}:{notification_receiver_port}/notify",
    #         "authentication": {
    #             "schemes": ["bearer"],
    #         },
    #     }

    taskResult = None
    if streaming:
        response_stream = client.send_task_streaming(payload)
        async for result in response_stream:
            print(result)
            print(f"stream event => {result.model_dump_json(exclude_none=True)}")
        taskResult = await client.get_task({"id": taskId})
    else:
        taskResult = await client.send_task(payload)
        print(f"\n{taskResult.model_dump_json(exclude_none=True)}")

    ## if the result is that more input is required, loop again.
    state = TaskState(taskResult.result.status.state)
    if state.name == TaskState.INPUT_REQUIRED.name:
        return await completeTask(
            client,
            streaming,
            use_push_notifications,
            notification_receiver_host,
            notification_receiver_port,
            taskId,
            sessionId
        )
    else:
        ## task is complete
        return True


if __name__ == "__main__":
    asyncio.run(cli())
