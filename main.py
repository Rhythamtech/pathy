import asyncio
import logging
from typing import Any
from agno.workflow import Workflow, StepOutput, WorkflowExecutionInput
from pydantic import BaseModel

from cli import _run_pipeline, ask_requirement
from utils.logging import setup_logging
from utils.models import UserRequirement


class RoadmapWorkflow(Workflow):
    """Workflow executing the sequential steps of the Pathy RoadMap AI pipeline."""
    pass


def run_pipeline_step(step_input: StepOutput) -> StepOutput:
    """Executes the core async agent pipeline orchestration."""
    requirement = step_input.input
    if not isinstance(requirement, UserRequirement):
        raise TypeError("Input to run_pipeline_step must be a UserRequirement")

    logging.info("Workflow stepping into pipeline execution.")
    asyncio.run(_run_pipeline(requirement))
    return StepOutput(content="Roadmap generation finished successfully.")


# Instantiate the mixed sequential workflow
workflow = RoadmapWorkflow(
    name="Pathy Roadmap mixed execution pipeline",
    steps=[
        run_pipeline_step,
    ]
)


def start() -> None:
    """Invoked to boot the prompt config and fire the workflow."""
    setup_logging()
    logging.info("Starting workflow.")
    requirement = ask_requirement()
    workflow.run(input=requirement)


if __name__ == "__main__":
    start()