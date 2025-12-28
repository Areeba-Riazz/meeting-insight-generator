"""Project management routes."""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, ConfigDict

from src.core.database import get_db
from src.services.database_service import DatabaseService


router = APIRouter()


# Request/Response Models
class CreateProjectRequest(BaseModel):
    name: str
    description: Optional[str] = None


class UpdateProjectRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    name: str
    description: Optional[str]
    created_at: str
    updated_at: str
    meetings_count: Optional[int] = None


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int


@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def create_project(
    request: CreateProjectRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new project."""
    if not request.name or not request.name.strip():
        raise HTTPException(status_code=400, detail="Project name is required")

    db_service = DatabaseService(db)
    project = await db_service.create_project(
        name=request.name.strip(),
        description=request.description.strip() if request.description else None,
    )

    # Get meetings count
    meetings_count = await db_service.count_meetings_by_project(project.id)

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
        meetings_count=meetings_count,
    )


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get project by ID."""
    db_service = DatabaseService(db)
    project = await db_service.get_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get meetings count
    meetings_count = await db_service.count_meetings_by_project(project.id)

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
        meetings_count=meetings_count,
    )


@router.get("/projects", response_model=ProjectListResponse)
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """List all projects."""
    db_service = DatabaseService(db)
    projects = await db_service.list_projects(skip=skip, limit=limit)
    total = await db_service.count_projects()

    # Get meetings count for each project
    project_responses = []
    for project in projects:
        meetings_count = await db_service.count_meetings_by_project(project.id)
        project_responses.append(
            ProjectResponse(
                id=project.id,
                name=project.name,
                description=project.description,
                created_at=project.created_at.isoformat(),
                updated_at=project.updated_at.isoformat(),
                meetings_count=meetings_count,
            )
        )

    return ProjectListResponse(projects=project_responses, total=total)


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    request: UpdateProjectRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update project."""
    db_service = DatabaseService(db)
    project = await db_service.update_project(
        project_id=project_id,
        name=request.name.strip() if request.name else None,
        description=request.description.strip() if request.description else None,
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get meetings count
    meetings_count = await db_service.count_meetings_by_project(project.id)

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
        meetings_count=meetings_count,
    )


@router.delete("/projects/{project_id}", status_code=204)
async def delete_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete project (cascades to meetings)."""
    db_service = DatabaseService(db)
    success = await db_service.delete_project(project_id)

    if not success:
        raise HTTPException(status_code=404, detail="Project not found")

    return None

