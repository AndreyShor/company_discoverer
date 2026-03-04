from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status

from core.logging import get_logger
from models.company_models import CompanyReportRequest, CompanyReportResponse
from services.task_manager import TaskStatus, task_manager

logger = get_logger(__name__)

router = APIRouter(prefix="/company", tags=["company"])


@router.post("/report", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def request_company_report(
    body: CompanyReportRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    """Enqueue an asynchronous company intelligence report generation task."""
    task_id = await task_manager.create_task(
        task_type="company_report",
        payload={"company_name": body.company_name, "country": body.country},
    )
    background_tasks.add_task(_generate_report_task, task_id, body)
    logger.info("company_report_requested", task_id=task_id, company=body.company_name)
    return {"task_id": task_id, "status": TaskStatus.PENDING}


@router.get("/report/{task_id}", response_model=dict)
async def get_report_status(task_id: str) -> dict:
    """Poll the status of a company report generation task."""
    state = await task_manager.get_task(task_id)
    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return state


@router.delete("/report/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_report(task_id: str) -> None:
    """Cancel a pending or running report generation task."""
    cancelled = await task_manager.cancel_task(task_id)
    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task could not be cancelled (not found or already finished)",
        )


async def _generate_report_task(task_id: str, body: CompanyReportRequest) -> None:
    """Background worker: run the report pipeline and update task state."""
    await task_manager.update_task(task_id, status=TaskStatus.RUNNING)
    try:
        if await task_manager.is_cancelled(task_id):
            return

        # Placeholder: real implementation would call the LLM pipeline
        result = CompanyReportResponse(
            company_name=body.company_name,
            country=body.country,
            summary=f"Placeholder intelligence report for {body.company_name} ({body.country}).",
            sources=[],
        ).model_dump()

        await task_manager.update_task(task_id, status=TaskStatus.COMPLETED, result=result)
        logger.info("company_report_completed", task_id=task_id)
    except Exception as exc:
        logger.error("company_report_failed", task_id=task_id, error=str(exc))
        await task_manager.update_task(task_id, status=TaskStatus.FAILED, error=str(exc))
