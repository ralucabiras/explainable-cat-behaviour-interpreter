import pytest
from pydantic import ValidationError

from app.models.observation import ObservationCreate
from app.models.pet import PetCreate


def test_pet_scope_is_currently_limited_to_cats() -> None:
    with pytest.raises(ValidationError):
        PetCreate(name="Rex", species="dog")


def test_observation_has_safe_empty_context_defaults() -> None:
    observation = ObservationCreate(pet_id="pet-id", text_description="Hiding under the bed")
    assert observation.context.known_triggers == []
    assert observation.video is None
    assert observation.audio is None

