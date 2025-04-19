from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
from task_manager import AgentTaskManager
from agent import LeaveApprovalAgent
import click
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=10003)
def main(host, port):
    try:
        # if not os.getenv("GOOGLE_API_KEY"):
        #         raise MissingAPIKeyError("GOOGLE_API_KEY environment variable not set.")
        
        capabilities = AgentCapabilities(streaming=True)
        skill = AgentSkill(
            id="process_leave_approval",
            name="Process Leave Approval",
            description="Helps with the leave approval for users given the date of the leave.",
            tags=["Leave Approval"],
            examples=["I want to leave on 04/12/2001"],
        )
        agent_card = AgentCard(
            name="Leave Approval Agent",
            description="This agent handles the leave approval process for the employees given the date of the leave.",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=LeaveApprovalAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=LeaveApprovalAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )
        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(agent=LeaveApprovalAgent()),
            host=host,
            port=port,
        )
        server.start()
    except MissingAPIKeyError as e:
        logger.error(f"Error: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)
    
if __name__ == "__main__":
    print("Start LeaveApprovalAgent")
    main()

