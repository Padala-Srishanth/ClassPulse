"""
app.api.v1.chatbot — ClassPulse AI Assistant Endpoints

Role gate: ONLY TEACHER, SCHOOL_ADMIN, and ADMIN may call these routes.
STUDENT (and any unauthenticated caller) is rejected with 403 / 401 before
the orchestrator — and therefore before any Firestore read — ever runs.
The role comes exclusively from the Firebase-verified `CurrentUser`
(`get_current_user`, backed by Firebase custom claims); nothing here trusts
a role or school_id supplied by the client.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentUser, get_current_user
from app.core.security import UserRole
from app.schemas.chatbot import ChatCapabilitiesResponse, ChatMessageRequest, ChatMessageResponse
from app.services.chatbot import orchestrator
from app.services.chatbot.scope import ChatbotAuthorizationError, resolve_scope
from app.utils.responses import success_response

router = APIRouter(tags=["ClassPulse Assistant"])

_ALLOWED_ROLES = {UserRole.TEACHER, UserRole.SCHOOL_ADMIN, UserRole.ADMIN}


def _require_chatbot_access(current_user: CurrentUser) -> CurrentUser:
    """Students (and any other/absent role) never reach the orchestrator."""
    if current_user.role not in _ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "CHATBOT_ACCESS_DENIED",
                "message": "The ClassPulse Assistant is available to teachers and principals only.",
            },
        )
    return current_user


@router.post("/message", summary="Send a message to the ClassPulse AI Assistant")
async def send_message(
    payload: ChatMessageRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    current_user = _require_chatbot_access(current_user)

    result: ChatMessageResponse = orchestrator.handle_message(
        user=current_user,
        message=payload.message,
        context=payload.context,
    )
    return success_response(data=result.model_dump())


@router.get("/capabilities", summary="Describe the assistant's capabilities for the current user")
async def get_capabilities(
    current_user: CurrentUser = Depends(get_current_user),
):
    current_user = _require_chatbot_access(current_user)

    try:
        scope = resolve_scope(current_user)
    except ChatbotAuthorizationError:
        return success_response(
            data=ChatCapabilitiesResponse(
                role=current_user.role.value if current_user.role else "",
                is_principal=False,
                school_id=current_user.school_id,
                authorized_class_count=0,
                example_questions=[],
            ).model_dump()
        )

    examples = (
        [
            "Show all high-risk students.",
            "Which class has the lowest attendance?",
            "Show students with attendance below 75% and declining test scores.",
            "Give me a complete summary of <student name>.",
            "Which high-risk students currently have no intervention?",
        ]
        if scope.is_principal
        else [
            "Who has attendance below 75%?",
            "Who has not completed homework?",
            "Which students in my class are currently high risk?",
            "Give me a summary of <student name>.",
        ]
    )

    return success_response(
        data=ChatCapabilitiesResponse(
            role=current_user.role.value if current_user.role else "",
            is_principal=scope.is_principal,
            school_id=scope.school_id,
            authorized_class_count=len(scope.classes),
            example_questions=examples,
        ).model_dump()
    )
