from pydantic import BaseModel, ConfigDict, Field

from app.modules.fitness.domain.enums import FitnessGoal


class FitnessBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal: FitnessGoal
    goal_note: str | None = Field(default=None, max_length=2000)
