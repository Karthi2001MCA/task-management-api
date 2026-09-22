const API = "/tasks";

const form = document.getElementById("create-form");
const formError = document.getElementById("form-error");
const listError = document.getElementById("list-error");
const list = document.getElementById("task-list");
const empty = document.getElementById("empty");
const count = document.getElementById("count");
const toast = document.getElementById("toast");
const template = document.getElementById("task-template");

const LABELS = {
  todo: "To do",
  in_progress: "In progress",
  completed: "Completed",
  low: "Low",
  medium: "Medium",
  high: "High",
};

let tasks = [];
let filter = "all";
let toastTimer;

/** Turn FastAPI's 422 body into one readable sentence. */
function describeError(status, body) {
  if (status === 422 && Array.isArray(body?.detail)) {
    return body.detail
      .map((e) => {
        const field = e.loc?.filter((p) => p !== "body").join(".") || "request";
        return `${field}: ${e.msg}`;
      })
      .join(" · ");
  }
  if (typeof body?.detail === "string") return body.detail;
  return `Request failed (${status})`;
}

async function request(method, path = "", payload) {
  const response = await fetch(API + path, {
    method,
    headers: payload ? { "Content-Type": "application/json" } : undefined,
    body: payload ? JSON.stringify(payload) : undefined,
  });

  if (response.status === 204) return null;

  const body = await response.json().catch(() => null);
  if (!response.ok) throw new Error(describeError(response.status, body));
  return body;
}

function showToast(message) {
  toast.textContent = message;
  toast.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (toast.hidden = true), 2600);
}

function showError(element, message) {
  element.textContent = message;
  element.hidden = false;
}

function hide(element) {
  element.hidden = true;
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function render() {
  const visible = filter === "all" ? tasks : tasks.filter((t) => t.status === filter);

  list.replaceChildren();
  for (const task of visible) {
    const node = template.content.cloneNode(true);
    const item = node.querySelector(".task");

    item.dataset.id = task.id;
    item.classList.toggle("is-done", task.status === "completed");
    node.querySelector(".task-title").textContent = task.title;
    node.querySelector(".task-desc").textContent = task.description ?? "";

    const status = node.querySelector(".badge-status");
    status.textContent = LABELS[task.status];
    status.classList.add(`status-${task.status}`);

    const priority = node.querySelector(".badge-priority");
    priority.textContent = LABELS[task.priority];
    priority.classList.add(`priority-${task.priority}`);

    node.querySelector(".task-date").textContent = formatDate(task.created_at);
    node.querySelector(".status-select").value = task.status;

    list.append(node);
  }

  empty.hidden = visible.length > 0;
  empty.textContent = tasks.length
    ? "No tasks with this status."
    : "No tasks yet. Add one above.";
  count.textContent = tasks.length ? `(${tasks.length})` : "";
}

async function load() {
  try {
    tasks = await request("GET");
    hide(listError);
    render();
  } catch (error) {
    showError(listError, error.message);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hide(formError);

  const data = new FormData(form);
  const description = data.get("description").trim();

  try {
    await request("POST", "", {
      title: data.get("title"),
      description: description || null,
      status: data.get("status"),
      priority: data.get("priority"),
    });
    form.reset();
    document.getElementById("priority").value = "medium";
    showToast("Task created");
    await load();
  } catch (error) {
    showError(formError, error.message);
  }
});

list.addEventListener("click", async (event) => {
  const button = event.target.closest(".btn-delete");
  if (!button) return;

  const id = button.closest(".task").dataset.id;
  const task = tasks.find((t) => String(t.id) === id);
  if (!confirm(`Delete "${task.title}"?`)) return;

  try {
    await request("DELETE", `/${id}`);
    showToast("Task deleted");
    await load();
  } catch (error) {
    showError(listError, error.message);
  }
});

list.addEventListener("change", async (event) => {
  const select = event.target.closest(".status-select");
  if (!select) return;

  const id = select.closest(".task").dataset.id;
  const task = tasks.find((t) => String(t.id) === id);

  try {
    // PUT replaces the whole resource, so every field is sent.
    await request("PUT", `/${id}`, {
      title: task.title,
      description: task.description,
      status: select.value,
      priority: task.priority,
    });
    showToast("Status updated");
    await load();
  } catch (error) {
    showError(listError, error.message);
    await load();
  }
});

for (const chip of document.querySelectorAll(".chip")) {
  chip.addEventListener("click", () => {
    document.querySelector(".chip.is-active").classList.remove("is-active");
    chip.classList.add("is-active");
    filter = chip.dataset.filter;
    render();
  });
}

load();
