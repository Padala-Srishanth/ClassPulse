"""
app.services.chatbot — ClassPulse AI Assistant

A role-aware natural-language interface for TEACHER and PRINCIPAL/ADMIN
users, built entirely on top of the existing ClassPulse services. Students
have no access to this package's endpoints.

Architecture (see docs/CHATBOT.md for full details):

    API layer (app/api/v1/chatbot.py)
        -> role gate (TEACHER / SCHOOL_ADMIN / ADMIN only)
        -> scope.resolve_scope()            (WHO can see WHAT)
        -> nlu.parse_message()              (WHAT is being asked)
        -> orchestrator.handle_message()    (glues it together)
              -> tools.py                   (controlled, read-only data access
                                              — reuses the existing services)
              -> responder.py               (deterministic template reply,
                                              optionally polished by an LLM)

The LLM (when configured) is used ONLY to phrase the final natural-language
sentence from already-retrieved, already-authorized structured data. It is
never given database access, credentials, or the ability to choose what data
to fetch — that is 100% deterministic backend logic.
"""
