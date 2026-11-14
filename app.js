const leadsContainer = document.getElementById("leads-container");
const filterButtons = document.querySelectorAll(".chip");
const waitlistForm = document.getElementById("waitlist-form");
const waitlistStatus = document.getElementById("waitlist-status");
const planSelect = document.getElementById("plan");

async function loadLeads(source = "all") {
  leadsContainer.innerHTML = '<div class="card muted">Загрузка демо-лидов...</div>';
  try {
    const query = source === "all" ? "" : `?source=${encodeURIComponent(source)}`;
    const res = await fetch(`/api/demo-leads${query}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderLeads(data.leads || []);
  } catch (err) {
    leadsContainer.innerHTML = `<div class="card muted">Не удалось загрузить лиды: ${err.message}</div>`;
  }
}

function renderLeads(leads) {
  if (!leads.length) {
    leadsContainer.innerHTML = '<div class="card muted">По выбранному источнику лидов пока нет.</div>';
    return;
  }

  leadsContainer.innerHTML = leads
    .map(
      (lead) => `
      <article class="card">
        <div class="lead-top">
          <span class="source-tag">${lead.source} • ${lead.channel}</span>
          <span class="score-tag">Intent ${lead.intent_score}/100</span>
        </div>
        <h3>${lead.title}</h3>
        <div class="lead-meta">
          <span>Бюджет: <strong>${lead.budget}</strong></span>
          <span>${lead.posted_ago}</span>
        </div>
        <div class="outreach-box">
          <span class="outreach-label">AI-отклик</span>
          ${lead.ai_outreach}
        </div>
      </article>
    `
    )
    .join("");
}

filterButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    filterButtons.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    loadLeads(btn.dataset.source);
  });
});

document.querySelectorAll("[data-select-plan]").forEach((link) => {
  link.addEventListener("click", () => {
    planSelect.value = link.dataset.selectPlan;
  });
});

waitlistForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  waitlistStatus.textContent = "Отправка...";
  const payload = {
    email: document.getElementById("email").value.trim(),
    niche: document.getElementById("niche").value.trim(),
    plan: planSelect.value,
  };

  try {
    const res = await fetch("/api/waitlist", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Ошибка отправки");
    waitlistStatus.textContent = data.message;
    waitlistForm.reset();
    planSelect.value = payload.plan;
  } catch (err) {
    waitlistStatus.textContent = `Ошибка: ${err.message}`;
  }
});

loadLeads("all");
