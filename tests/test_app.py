from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture(autouse=True)
def reset_activities_state():
    """Arrange: preserve and restore the global activity state between tests."""
    original_activities = deepcopy(app_module.activities)
    yield
    app_module.activities = original_activities


@pytest.fixture
def client():
    """Arrange: create a TestClient for the FastAPI app."""
    return TestClient(app_module.app)


def test_get_activities_returns_all_activities(client):
    # Arrange
    expected_activity_count = len(app_module.activities)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    json_data = response.json()
    assert isinstance(json_data, dict)
    assert len(json_data) == expected_activity_count
    assert "Chess Club" in json_data


def test_signup_for_activity_adds_participant(client):
    # Arrange
    activity_name = "Chess Club"
    new_email = "newstudent@mergington.edu"
    assert new_email not in app_module.activities[activity_name]["participants"]

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": new_email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {new_email} for {activity_name}"}
    assert new_email in app_module.activities[activity_name]["participants"]


def test_signup_for_activity_returns_404_when_activity_missing(client):
    # Arrange
    activity_name = "Nonexistent Club"
    email = "missing@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_for_activity_returns_400_for_existing_participant(client):
    # Arrange
    activity_name = "Programming Class"
    existing_email = app_module.activities[activity_name]["participants"][0]

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": existing_email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_remove_participant_removes_existing_student(client):
    # Arrange
    activity_name = "Gym Class"
    participant_email = app_module.activities[activity_name]["participants"][0]
    assert participant_email in app_module.activities[activity_name]["participants"]

    # Act
    response = client.delete(f"/activities/{activity_name}/participants", params={"email": participant_email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {participant_email} from {activity_name}"}
    assert participant_email not in app_module.activities[activity_name]["participants"]


def test_remove_participant_returns_404_when_activity_missing(client):
    # Arrange
    activity_name = "No Club"
    email = "nobody@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/participants", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_returns_404_when_student_not_registered(client):
    # Arrange
    activity_name = "Mathletes"
    email = "notregistered@mergington.edu"
    assert email not in app_module.activities[activity_name]["participants"]

    # Act
    response = client.delete(f"/activities/{activity_name}/participants", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
