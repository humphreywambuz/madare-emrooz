"""Fitness path (spec section 9). Pure Python: no Flask, no SQLAlchemy."""
import uuid
from dataclasses import dataclass
from datetime import datetime

from .enums import FitnessGoal


@dataclass
class FitnessProfile:
    user_id: uuid.UUID
    goal: FitnessGoal
    goal_note: str | None = None  # her own explanation of the goal
    specialist_visit_completed: bool = False
    specialist_visit_at: datetime | None = None

    @property
    def dashboard_unlocked(self) -> bool:
        """Until the specialist visit the dashboard asks her to visit the specialist."""
        return self.specialist_visit_completed

    def update_goal(self, goal: FitnessGoal, goal_note: str | None) -> None:
        self.goal, self.goal_note = goal, goal_note

    def record_specialist_visit(self, at: datetime) -> None:
        self.specialist_visit_completed = True
        self.specialist_visit_at = at
