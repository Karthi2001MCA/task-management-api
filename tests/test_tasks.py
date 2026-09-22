import pytest

# ---------------------------------------------------------------- health


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ------------------------------------------------- POST /tasks (create)


def test_create_task_returns_201(client):
    response = client.post("/tasks", json={"title": "Write the tests"})
    assert response.status_code == 201


def test_create_task_returns_the_created_task(client):
    response = client.post(
        "/tasks",
        json={"title": "Write the tests", "description": "With pytest", "priority": "high"},
    )
    body = response.json()
    assert body["title"] == "Write the tests"
    assert body["description"] == "With pytest"
    assert body["priority"] == "high"


def test_create_task_generates_an_id(client):
    body = client.post("/tasks", json={"title": "Needs an id"}).json()
    assert isinstance(body["id"], int)
    assert body["id"] > 0


def test_create_task_applies_defaults(client):
    body = client.post("/tasks", json={"title": "Only a title"}).json()
    assert body["status"] == "todo"
    assert body["priority"] == "medium"
    assert body["description"] is None


def test_create_task_sets_created_at(client):
    body = client.post("/tasks", json={"title": "Timestamped"}).json()
    assert body["created_at"] is not None


def test_create_task_is_persisted(client):
    created = client.post("/tasks", json={"title": "Should survive"}).json()
    fetched = client.get(f"/tasks/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "Should survive"


def test_create_task_strips_whitespace_from_title(client):
    body = client.post("/tasks", json={"title": "   Padded title   "}).json()
    assert body["title"] == "Padded title"


def test_response_contains_only_schema_fields(client):
    body = client.post("/tasks", json={"title": "Field check"}).json()
    assert set(body) == {"id", "title", "description", "status", "priority", "created_at"}


# ---------------------------------------------------- GET /tasks (list)


def test_list_tasks_empty_returns_empty_list(client):
    response = client.get("/tasks")
    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_returns_all_tasks(client):
    client.post("/tasks", json={"title": "First task"})
    client.post("/tasks", json={"title": "Second task"})
    client.post("/tasks", json={"title": "Third task"})

    body = client.get("/tasks").json()
    assert len(body) == 3
    assert [task["title"] for task in body] == ["First task", "Second task", "Third task"]


def test_list_tasks_is_ordered_by_id(client):
    for letter in ("A", "B", "C"):
        client.post("/tasks", json={"title": f"Task {letter}"})

    ids = [task["id"] for task in client.get("/tasks").json()]
    assert ids == sorted(ids)


# ------------------------------------------------ GET /tasks/{id} (read)


def test_get_task_returns_the_correct_task(client, sample_task):
    response = client.get(f"/tasks/{sample_task['id']}")
    assert response.status_code == 200
    assert response.json() == sample_task


def test_get_task_not_found_returns_404(client):
    response = client.get("/tasks/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_get_task_with_non_integer_id_returns_422(client):
    assert client.get("/tasks/abc").status_code == 422


# --------------------------------------------- PUT /tasks/{id} (update)


def test_update_task_returns_200(client, sample_task):
    response = client.put(
        f"/tasks/{sample_task['id']}",
        json={"title": "Renamed", "status": "completed", "priority": "low"},
    )
    assert response.status_code == 200


def test_update_task_changes_the_values(client, sample_task):
    body = client.put(
        f"/tasks/{sample_task['id']}",
        json={"title": "Renamed", "status": "completed", "priority": "low"},
    ).json()
    assert body["title"] == "Renamed"
    assert body["status"] == "completed"
    assert body["priority"] == "low"


def test_update_task_persists_the_change(client, sample_task):
    client.put(
        f"/tasks/{sample_task['id']}",
        json={"title": "Persisted rename", "status": "in_progress"},
    )
    assert client.get(f"/tasks/{sample_task['id']}").json()["title"] == "Persisted rename"


def test_update_task_keeps_id_and_created_at(client, sample_task):
    body = client.put(f"/tasks/{sample_task['id']}", json={"title": "New title"}).json()
    assert body["id"] == sample_task["id"]
    assert body["created_at"] == sample_task["created_at"]


def test_update_task_replaces_omitted_fields_with_defaults(client, sample_task):
    # PUT is a full replacement: omitted fields fall back to schema defaults.
    body = client.put(f"/tasks/{sample_task['id']}", json={"title": "Title only"}).json()
    assert body["status"] == "todo"
    assert body["priority"] == "medium"


def test_update_task_not_found_returns_404(client):
    response = client.put("/tasks/9999", json={"title": "Does not exist"})
    assert response.status_code == 404


def test_update_task_with_invalid_data_returns_422(client, sample_task):
    response = client.put(f"/tasks/{sample_task['id']}", json={"title": "ab"})
    assert response.status_code == 422


# ------------------------------------------- DELETE /tasks/{id} (delete)


def test_delete_task_returns_204(client, sample_task):
    response = client.delete(f"/tasks/{sample_task['id']}")
    assert response.status_code == 204
    assert response.content == b""


def test_deleted_task_cannot_be_retrieved(client, sample_task):
    client.delete(f"/tasks/{sample_task['id']}")
    assert client.get(f"/tasks/{sample_task['id']}").status_code == 404


def test_deleted_task_is_removed_from_the_list(client, sample_task):
    client.delete(f"/tasks/{sample_task['id']}")
    assert client.get("/tasks").json() == []


def test_delete_task_twice_returns_404(client, sample_task):
    client.delete(f"/tasks/{sample_task['id']}")
    assert client.delete(f"/tasks/{sample_task['id']}").status_code == 404


def test_delete_task_not_found_returns_404(client):
    assert client.delete("/tasks/9999").status_code == 404


# ------------------------------------------ validation: required fields


def test_create_task_without_title_returns_422(client):
    response = client.post("/tasks", json={"description": "No title here"})
    assert response.status_code == 422


def test_create_task_with_empty_body_returns_422(client):
    assert client.post("/tasks", json={}).status_code == 422


def test_failed_validation_does_not_create_a_task(client):
    client.post("/tasks", json={"description": "No title here"})
    assert client.get("/tasks").json() == []


def test_validation_error_names_the_offending_field(client):
    body = client.post("/tasks", json={"description": "No title here"}).json()
    assert body["detail"][0]["loc"] == ["body", "title"]


# ----------------------------------------- validation: titles and types


@pytest.mark.parametrize("title", ["", "ab", "   ", "  ab  "])
def test_create_task_with_invalid_title_returns_422(client, title):
    assert client.post("/tasks", json={"title": title}).status_code == 422


def test_create_task_with_too_long_title_returns_422(client):
    assert client.post("/tasks", json={"title": "x" * 201}).status_code == 422


def test_create_task_with_wrong_title_type_returns_422(client):
    assert client.post("/tasks", json={"title": 12345}).status_code == 422


# -------------------------------------- validation: status and priority


@pytest.mark.parametrize("status", ["todo", "in_progress", "completed"])
def test_valid_status_is_accepted(client, status):
    response = client.post("/tasks", json={"title": "Status check", "status": status})
    assert response.status_code == 201
    assert response.json()["status"] == status


@pytest.mark.parametrize("status", ["urgent", "TODO", "done", "", None, 1])
def test_invalid_status_is_rejected(client, status):
    response = client.post("/tasks", json={"title": "Status check", "status": status})
    assert response.status_code == 422


@pytest.mark.parametrize("priority", ["low", "medium", "high"])
def test_valid_priority_is_accepted(client, priority):
    response = client.post("/tasks", json={"title": "Priority check", "priority": priority})
    assert response.status_code == 201
    assert response.json()["priority"] == priority


@pytest.mark.parametrize("priority", ["urgent", "HIGH", "critical", "", None, 1])
def test_invalid_priority_is_rejected(client, priority):
    response = client.post("/tasks", json={"title": "Priority check", "priority": priority})
    assert response.status_code == 422


# ----------------------------------------------------- 404 across verbs


@pytest.mark.parametrize(
    "method,kwargs",
    [
        ("get", {}),
        ("put", {"json": {"title": "Does not exist"}}),
        ("delete", {}),
    ],
)
def test_missing_task_returns_404_for_every_verb(client, method, kwargs):
    response = getattr(client, method)("/tasks/9999", **kwargs)
    assert response.status_code == 404


# ------------------------------------------------------------ isolation


def test_database_starts_empty(client):
    # Proves fixtures drop tables between tests: passes regardless of run order.
    assert client.get("/tasks").json() == []


# ------------------------------------------------------------- web UI


def test_index_serves_the_ui(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_static_assets_are_served(client):
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/style.css").status_code == 200


def test_ui_route_is_hidden_from_the_api_schema(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert "/" not in paths
