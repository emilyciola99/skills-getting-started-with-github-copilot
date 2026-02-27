import copy
import pytest
from fastapi.testclient import TestClient

from src import app as application
from src.app import activities

client = TestClient(application.app)

@pytest.fixture(autouse=True)
def reset_activities():
    """Arrange: make a deep copy of the original state and restore it after each test."""
    original = copy.deepcopy(activities)
    yield
    # Assert/cleanup: restore the global activities dict so tests don't interfere
    activities.clear()
    activities.update(original)


def test_root_redirect():
    # Act: avoid following the redirect so we can inspect headers directly
    response = client.get("/", follow_redirects=False)
    # Assert
    assert response.status_code == 307
    assert response.headers.get("location", "").endswith("/static/index.html")


def test_get_activities():
    # Arrange (state provided by fixture)
    # Act
    response = client.get("/activities")
    # Assert
    assert response.status_code == 200
    assert response.json() == activities


def test_successful_signup():
    # Arrange
    activity = next(iter(activities))
    email = "newstudent@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert email in activities[activity]["participants"]


def test_signup_nonexistent_activity():
    # Arrange
    email = "student@mergington.edu"

    # Act
    response = client.post("/activities/NoSuchActivity/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate():
    # Arrange
    activity = next(iter(activities))
    existing_email = activities[activity]["participants"][0]

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": existing_email})

    # Assert
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]


def test_remove_participant_success():
    # Arrange
    activity = next(iter(activities))
    email = activities[activity]["participants"][0]

    # Act
    response = client.delete(f"/activities/{activity}/participants", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert email not in activities[activity]["participants"]


def test_remove_nonexistent_participant():
    # Arrange
    activity = next(iter(activities))
    email = "absent@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity}/participants", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert "not registered" in response.json()["detail"]


def test_remove_from_nonexistent_activity():
    # Arrange
    email = "student@mergington.edu"

    # Act
    response = client.delete("/activities/NoSuchActivity/participants", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
