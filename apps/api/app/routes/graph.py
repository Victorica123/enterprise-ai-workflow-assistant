from fastapi import APIRouter, Header, HTTPException

from app.auth import require_write_role, validate_actor_role
from app.graph_store import find_paths, get_graph_overview, list_entities, list_relations, rebuild_graph
from app.models import (
    GraphEntityResponse,
    GraphOverviewResponse,
    GraphPathQueryResponse,
    GraphPathResponse,
    GraphPathStepResponse,
    GraphRebuildResponse,
    GraphRelationResponse,
)


router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/overview", response_model=GraphOverviewResponse)
def graph_overview() -> GraphOverviewResponse:
    return GraphOverviewResponse(**get_graph_overview())


@router.get("/entities", response_model=list[GraphEntityResponse])
def graph_entities(entity_type: str = "", keyword: str = "", limit: int = 100) -> list[GraphEntityResponse]:
    return [GraphEntityResponse(**entity.to_dict()) for entity in list_entities(entity_type, keyword, limit)]


@router.get("/relations", response_model=list[GraphRelationResponse])
def graph_relations(entity: str = "", relation_type: str = "", limit: int = 200) -> list[GraphRelationResponse]:
    return [GraphRelationResponse(**relation.to_dict()) for relation in list_relations(entity, relation_type, limit)]


@router.get("/paths", response_model=GraphPathQueryResponse)
def graph_paths(source: str, target: str, max_depth: int = 3) -> GraphPathQueryResponse:
    if not source.strip() or not target.strip():
        raise HTTPException(status_code=400, detail="source 和 target 不能为空。")
    paths = find_paths(source.strip(), target.strip(), max_depth)
    return GraphPathQueryResponse(
        source=source.strip(),
        target=target.strip(),
        max_depth=max_depth,
        paths=[
            GraphPathResponse(
                steps=[
                    GraphPathStepResponse(
                        source=step.source,
                        relation=step.relation,
                        target=step.target,
                        forward=step.forward,
                        display=step.display(),
                    )
                    for step in path
                ],
                display=" ; ".join(step.display() for step in path),
            )
            for path in paths
        ],
    )


@router.post("/rebuild", response_model=GraphRebuildResponse)
def graph_rebuild(x_user_role: str = Header(default="viewer")) -> GraphRebuildResponse:
    require_write_role(validate_actor_role(x_user_role))
    return GraphRebuildResponse(**rebuild_graph())
