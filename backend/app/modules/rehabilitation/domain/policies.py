def is_advanced_locked(*, specialist_visit_completed: bool, has_active_approval: bool) -> bool:
    """Advanced exercises stay locked until a specialist visit has taken place
    and a doctor has approved the rehabilitation plan (spec section 11)."""
    return not (specialist_visit_completed and has_active_approval)
