"""观测端点：指标、请求日志、工具调用审计。

隐私分层：/metrics/* 是聚合数据对所有角色开放；
/chat-logs、/tool-calls 含问题原文与工具入参，仅 operator/admin 可见。
"""
from fastapi import APIRouter, Header, HTTPException

from app.auth import require_operator_role, validate_actor_role
from app.database import (
    get_chat_log,
    get_chat_metrics_summary,
    list_chat_logs,
    set_chat_log_feedback,
)
from app.models import (
    ChatLogDetailResponse,
    ChatLogResponse,
    ChatMetricsSummary,
    FeedbackRequest,
    FeedbackResponse,
    ToolCallLogResponse,
    ToolMetricsSummary,
)
from app.ticket_store import get_tool_metrics_summary, list_tool_call_logs


router = APIRouter(tags=["observability"])


@router.get("/metrics/summary", response_model=ChatMetricsSummary)
def get_metrics_summary() -> ChatMetricsSummary:
    return ChatMetricsSummary(**get_chat_metrics_summary())


@router.get("/metrics/tools", response_model=ToolMetricsSummary)
def get_tool_metrics() -> ToolMetricsSummary:
    return ToolMetricsSummary(**get_tool_metrics_summary())


@router.get("/tool-calls", response_model=list[ToolCallLogResponse])
def get_tool_calls(
    limit: int = 50,
    x_user_role: str = Header(default="viewer"),
) -> list[ToolCallLogResponse]:
    require_operator_role(validate_actor_role(x_user_role))
    return [ToolCallLogResponse(**item) for item in list_tool_call_logs(limit=limit)]


@router.get("/chat-logs", response_model=list[ChatLogResponse])
def get_chat_logs(
    outcome: str = "",
    limit: int = 50,
    x_user_role: str = Header(default="viewer"),
) -> list[ChatLogResponse]:
    require_operator_role(validate_actor_role(x_user_role))
    return [ChatLogResponse(**item) for item in list_chat_logs(outcome=outcome, limit=limit)]


@router.get("/chat-logs/{log_id}", response_model=ChatLogDetailResponse)
def get_chat_log_detail(
    log_id: int,
    x_user_role: str = Header(default="viewer"),
) -> ChatLogDetailResponse:
    require_operator_role(validate_actor_role(x_user_role))
    log = get_chat_log(log_id)
    if log is None:
        raise HTTPException(status_code=404, detail="Chat log not found.")
    return ChatLogDetailResponse(**log)


@router.post("/chat-logs/{log_id}/feedback", response_model=FeedbackResponse)
def submit_chat_feedback(log_id: int, request: FeedbackRequest) -> FeedbackResponse:
    feedback = 1 if request.rating == "up" else -1
    if not set_chat_log_feedback(log_id, feedback, request.note):
        raise HTTPException(status_code=404, detail="Chat log not found.")
    return FeedbackResponse(log_id=log_id, feedback=feedback, feedback_note=request.note)
