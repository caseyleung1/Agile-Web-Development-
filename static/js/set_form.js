(function () {
  let qIndex = 0;

  function el(id) {
    return document.getElementById(id);
  }

  function nextIndex() {
    qIndex += 1;
    return qIndex;
  }

  function questionBlock(i) {
    return `
<div class="question-card mb-8 rounded-2xl border-2 border-brand-purple/50 bg-white p-6 shadow-sm" data-q="${i}">
  <div class="mb-4 flex items-center justify-between">
    <h3 class="font-bold text-slate-900">Question ${i}</h3>
    <button type="button" class="rounded-lg border-2 border-red-400 px-2 py-1 text-red-600 js-remove-q" data-i="${i}" title="Remove">&#128465;</button>
  </div>
  <label class="text-sm font-semibold">Question (Term) *</label>
  <input name="term_${i}" required class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm" />
  <label class="mt-4 block text-sm font-semibold">Correct Answer (Definition) *</label>
  <input name="def_${i}" required class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm" />
  <p class="mt-4 text-sm font-medium text-slate-700">Multiple Choice Options for Quiz (include the correct answer)</p>
  <div class="mt-2 grid grid-cols-2 gap-3">
    <input name="opt_${i}_0" placeholder="Option 1" class="rounded-xl border border-slate-200 px-3 py-2 text-sm" />
    <input name="opt_${i}_1" placeholder="Option 2" class="rounded-xl border border-slate-200 px-3 py-2 text-sm" />
    <input name="opt_${i}_2" placeholder="Option 3" class="rounded-xl border border-slate-200 px-3 py-2 text-sm" />
    <input name="opt_${i}_3" placeholder="Option 4" class="rounded-xl border border-slate-200 px-3 py-2 text-sm" />
  </div>
</div>`;
  }

  function bindRemove(root) {
    root.querySelectorAll(".js-remove-q").forEach((btn) => {
      btn.addEventListener("click", () => {
        const card = btn.closest(".question-card");
        if (document.querySelectorAll(".question-card").length <= 1) return;
        card.remove();
      });
    });
  }

  window.initSetForm = function (startIndex) {
    qIndex = startIndex;
    const container = el("questions-container");
    const addBtn = el("add-question-btn");
    if (addBtn) {
      addBtn.addEventListener("click", () => {
        const i = nextIndex();
        const wrap = document.createElement("div");
        wrap.innerHTML = questionBlock(i).trim();
        const node = wrap.firstElementChild;
        container.appendChild(node);
        bindRemove(node);
      });
    }
    bindRemove(document);
  };

  window.generateAI = async function () {
    const prompt = (el("ai-prompt").value || "").trim();
    const status = el("ai-status");
    if (!prompt) {
      status.textContent = "Enter notes or a prompt first.";
      return;
    }
    status.textContent = "Generating…";
    try {
      const res = await fetch("/api/ai/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      const data = await res.json();
      if (!data.ok) {
        status.textContent = data.message || data.error || "Failed";
        return;
      }
      el("ai-preview").classList.remove("hidden");
      el("pv-q").value = data.question;
      el("pv-a").value = data.answer;
      window._aiOptions = data.options;
      window._aiCorrect = data.correct_index;
      status.textContent = "Ready — click Add to Set";
    } catch (e) {
      status.textContent = "Network error";
    }
  };

  window.applyAICard = function () {
    const i = nextIndex();
    const container = el("questions-container");
    const wrap = document.createElement("div");
    wrap.innerHTML = questionBlock(i).trim();
    const node = wrap.firstElementChild;
    const q = el("pv-q").value;
    const a = el("pv-a").value;
    const opts = window._aiOptions || [a, a, a, a];
    node.querySelector(`input[name="term_${i}"]`).value = q;
    node.querySelector(`input[name="def_${i}"]`).value = a;
    for (let j = 0; j < 4; j++) {
      node.querySelector(`input[name="opt_${i}_${j}"]`).value = opts[j] || "";
    }
    container.appendChild(node);
    bindRemove(node);
    el("ai-preview").classList.add("hidden");
    el("ai-status").textContent = "Added to form.";
  };
})();
