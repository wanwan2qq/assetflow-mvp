from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.core.database import get_db_session
from app.models.user import User
from app.models.action_plan import ActionPlan, ActionCategory, ActionStatus, ActionPlanStep, ActionStepStatus, ActionPlanRead
from app.services.action_reasoner import get_action_reasoner

router = APIRouter()

@router.get("/", response_model=List[ActionPlanRead])
async def read_plans(
    status: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    session=Depends(get_db_session)
) -> Any:
    """
    Retrieve action plans.
    """
    stmt = select(ActionPlan).where(ActionPlan.user_id == current_user.id)
    
    if status:
        stmt = stmt.where(ActionPlan.status == status)
    if category:
        stmt = stmt.where(ActionPlan.category == category)
        
    stmt = stmt.order_by(ActionPlan.created_at.desc()).offset(skip).limit(limit).options(selectinload(ActionPlan.steps_list))
    result = await session.execute(stmt)
    plans = result.scalars().all()
    return plans

@router.get("/stats")
async def get_plan_stats(
    current_user: User = Depends(get_current_user),
    session=Depends(get_db_session)
) -> Any:
    """
    Get statistics of action plans.
    """
    # Count by status
    stmt = select(ActionPlan.status, func.count(ActionPlan.id)).where(
        ActionPlan.user_id == current_user.id
    ).group_by(ActionPlan.status)
    
    result = await session.execute(stmt)
    stats = {row[0]: row[1] for row in result.all()}
    
    return {
        "total": sum(stats.values()),
        "in_progress": stats.get("in_progress", 0),
        "completed": stats.get("completed", 0),
        "pending": stats.get("pending", 0),
        "stats_by_status": stats
    }

@router.get("/{id}", response_model=ActionPlanRead)
async def read_plan(
    id: int,
    current_user: User = Depends(get_current_user),
    session=Depends(get_db_session)
) -> Any:
    """
    Get a specific action plan by ID.
    """
    stmt = select(ActionPlan).where(ActionPlan.id == id, ActionPlan.user_id == current_user.id).options(selectinload(ActionPlan.steps_list))
    result = await session.execute(stmt)
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan

@router.post("/{id}/adopt", response_model=ActionPlanRead)
async def adopt_plan(
    id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Adopt an action plan (Pending -> In Progress).
    """
    reasoner = get_action_reasoner()
    # verify ownership logic is missing in logic service, assume logic service handles user verification? 
    # reasoner.adopt_plan simply takes id.
    # We should verify ownership first.
    
    # Ownership check via simple query first?
    # Or strict implementation inside adopt_plan (pass user_id).
    # Current adopt_plan signature only takes plan_id.
    # Let's trust logic service or verify here.
    
    # Verify ownership
    # Verify ownership
    # We verify ownership by querying with user_id below.
    
    async for session in get_db_session():
         stmt = select(ActionPlan).where(ActionPlan.id == id, ActionPlan.user_id == current_user.id)
         result = await session.execute(stmt)
         plan = result.scalar_one_or_none()
         if not plan:
             raise HTTPException(status_code=404, detail="Plan not found")
         break # Close session generator
         
    updated_plan = await reasoner.adopt_plan(id)
    if not updated_plan:
        raise HTTPException(status_code=400, detail="Cannot adopt plan")
        
    return updated_plan

class DismissPlanRequest(BaseModel):
    reason: Optional[str] = None

@router.post("/{id}/dismiss", response_model=bool)
async def dismiss_plan(
    id: int,
    request: DismissPlanRequest = None,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Dismiss an action plan (Pending -> Dismissed).
    """
    reasoner = get_action_reasoner()
    
    # Ownership verification
    async for session in get_db_session():
         stmt = select(ActionPlan).where(ActionPlan.id == id, ActionPlan.user_id == current_user.id)
         result = await session.execute(stmt)
         plan = result.scalar_one_or_none()
         if not plan:
             raise HTTPException(status_code=404, detail="Plan not found")
         break

    success = await reasoner.dismiss_plan(id, request.reason if request else None)
    return success

@router.patch("/{plan_id}/steps/{step_id}", response_model=bool)
async def update_step_status(
    plan_id: int,
    step_id: int,
    status: str,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update the status of a specific step.
    """
    if status not in [s.value for s in ActionStepStatus]:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    reasoner = get_action_reasoner()
    
    # Ownership verification (Plan ownership implies step ownership)
    async for session in get_db_session():
         stmt = select(ActionPlan).where(ActionPlan.id == plan_id, ActionPlan.user_id == current_user.id)
         result = await session.execute(stmt)
         plan = result.scalar_one_or_none()
         if not plan:
             raise HTTPException(status_code=404, detail="Plan not found")
         break
         
    success = await reasoner.update_step_status(step_id, status, notes)
    return success

from pydantic import BaseModel
class RefinePlanRequest(BaseModel):
    feedback: str

@router.post("/{id}/refine", response_model=ActionPlan)
async def refine_plan(
    id: int,
    request: RefinePlanRequest,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Refine an action plan based on user feedback.
    """
    reasoner = get_action_reasoner()
    
    # Ownership verification
    async for session in get_db_session():
         stmt = select(ActionPlan).where(ActionPlan.id == id, ActionPlan.user_id == current_user.id)
         result = await session.execute(stmt)
         plan = result.scalar_one_or_none()
         if not plan:
             raise HTTPException(status_code=404, detail="Plan not found")
         break

    refined_plan = await reasoner.refine_plan(id, request.feedback)
    if not refined_plan:
         raise HTTPException(status_code=400, detail="Cannot refine plan")
         
    return refined_plan

@router.get("/{id}/steps", response_model=List[ActionPlanStep])
async def read_plan_steps(
    id: int,
    current_user: User = Depends(get_current_user),
    session=Depends(get_db_session)
) -> Any:
    """
    Get detailed steps for a plan.
    """
    # Verify ownership
    stmt = select(ActionPlan).where(ActionPlan.id == id, ActionPlan.user_id == current_user.id)
    result = await session.execute(stmt)
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
        
    step_stmt = select(ActionPlanStep).where(ActionPlanStep.plan_id == id).order_by(ActionPlanStep.step_number)
    step_result = await session.execute(step_stmt)
    return step_result.scalars().all()
