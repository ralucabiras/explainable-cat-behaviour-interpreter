from pydantic import Field, model_validator

from app.models.common import APIModel
from app.models.observation import BehaviourState, ObservationContext
from app.models.pet import PetCreate


class EvaluationInput(APIModel):
    text_description: str = Field(min_length=1, max_length=5000)
    context: ObservationContext = Field(default_factory=ObservationContext)


class EvaluationScenario(APIModel):
    id: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    pet: PetCreate
    observation: EvaluationInput
    expected_state: BehaviourState
    expected_safety_escalation: bool = False
    notes: str | None = None


class EvaluationDataset(APIModel):
    dataset_version: str = Field(min_length=1)
    description: str = Field(min_length=1)
    synthetic_data_notice: str = Field(min_length=1)
    scenarios: list[EvaluationScenario] = Field(min_length=1)

    @model_validator(mode="after")
    def scenario_ids_must_be_unique(self) -> "EvaluationDataset":
        ids = [scenario.id for scenario in self.scenarios]
        duplicates = sorted({scenario_id for scenario_id in ids if ids.count(scenario_id) > 1})
        if duplicates:
            raise ValueError(f"Duplicate scenario IDs: {', '.join(duplicates)}")
        return self
