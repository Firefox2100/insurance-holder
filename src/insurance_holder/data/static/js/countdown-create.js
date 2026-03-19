(function () {
  const CODE_TYPE_OPTIONS = [
    { value: "static", label: "Static Code" },
  ];

  const EFFECT_OPTIONS = [
    { value: "pacify", label: "Pacify" },
    { value: "trigger", label: "Trigger" },
    { value: "silentTrigger", label: "Silent Trigger" },
  ];

  function toNullableInt(value) {
    if (value === "") {
      return null;
    }
    const parsed = Number.parseInt(value, 10);
    if (!Number.isFinite(parsed)) {
      return null;
    }
    return parsed;
  }

  function showAlert(message, type) {
    const alertEl = document.getElementById("create-countdown-alert");
    if (!alertEl) {
      return;
    }
    alertEl.className = `alert alert-${type}`;
    alertEl.textContent = message;
  }

  function createSelect(options, className) {
    const select = document.createElement("select");
    select.className = className;
    options.forEach(function (option) {
      const optionEl = document.createElement("option");
      optionEl.value = option.value;
      optionEl.textContent = option.label;
      select.appendChild(optionEl);
    });
    return select;
  }

  function createCodeRow(index) {
    const wrapper = document.createElement("div");
    wrapper.className = "border rounded p-3";
    wrapper.dataset.codeRow = "1";

    const grid = document.createElement("div");
    grid.className = "row g-3 align-items-end";

    const typeCol = document.createElement("div");
    typeCol.className = "col-12 col-lg-3";
    const typeLabel = document.createElement("label");
    typeLabel.className = "form-label";
    typeLabel.textContent = "Code Type";
    const typeSelect = createSelect(CODE_TYPE_OPTIONS, "form-select js-code-type");
    typeSelect.name = `codes[${index}][code_type]`;
    typeCol.appendChild(typeLabel);
    typeCol.appendChild(typeSelect);

    const staticCol = document.createElement("div");
    staticCol.className = "col-12 col-lg-3 js-static-container";
    const staticLabel = document.createElement("label");
    staticLabel.className = "form-label";
    staticLabel.textContent = "Static Value";
    const staticInput = document.createElement("input");
    staticInput.className = "form-control js-static-value";
    staticInput.type = "text";
    staticInput.required = true;
    staticInput.name = `codes[${index}][staticValue]`;
    staticCol.appendChild(staticLabel);
    staticCol.appendChild(staticInput);

    const effectCol = document.createElement("div");
    effectCol.className = "col-12 col-md-6 col-lg-2";
    const effectLabel = document.createElement("label");
    effectLabel.className = "form-label";
    effectLabel.textContent = "Effect";
    const effectSelect = createSelect(EFFECT_OPTIONS, "form-select js-code-effect");
    effectSelect.name = `codes[${index}][effect]`;
    effectCol.appendChild(effectLabel);
    effectCol.appendChild(effectSelect);

    const delayCol = document.createElement("div");
    delayCol.className = "col-12 col-md-6 col-lg-2 js-delay-container d-none";
    const delayLabel = document.createElement("label");
    delayLabel.className = "form-label";
    delayLabel.textContent = "Delay (seconds)";
    const delayInput = document.createElement("input");
    delayInput.className = "form-control js-code-delay";
    delayInput.type = "number";
    delayInput.min = "0";
    delayInput.step = "1";
    delayInput.name = `codes[${index}][delay]`;
    delayCol.appendChild(delayLabel);
    delayCol.appendChild(delayInput);

    const actionCol = document.createElement("div");
    actionCol.className = "col-12 col-md-6 col-lg-2 d-grid ms-lg-auto";
    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "btn btn-outline-danger js-remove-code";
    removeBtn.textContent = "Remove";
    actionCol.appendChild(removeBtn);

    grid.appendChild(typeCol);
    grid.appendChild(staticCol);
    grid.appendChild(effectCol);
    grid.appendChild(delayCol);
    grid.appendChild(actionCol);
    wrapper.appendChild(grid);

    return wrapper;
  }

  function updateCodeTypeVisibility(rowEl) {
    const type = rowEl.querySelector(".js-code-type").value;
    const staticContainer = rowEl.querySelector(".js-static-container");
    const staticInput = rowEl.querySelector(".js-static-value");

    if (type === "static") {
      staticContainer.classList.remove("d-none");
      staticInput.required = true;
      return;
    }

    staticContainer.classList.add("d-none");
    staticInput.required = false;
  }

  function reindexRows(container) {
    const rows = Array.from(container.querySelectorAll("[data-code-row='1']"));
    rows.forEach(function (row, index) {
      row.querySelector(".js-code-type").name = `codes[${index}][code_type]`;
      row.querySelector(".js-static-value").name = `codes[${index}][staticValue]`;
      row.querySelector(".js-code-effect").name = `codes[${index}][effect]`;
      row.querySelector(".js-code-delay").name = `codes[${index}][delay]`;
    });
  }

  function updateEffectVisibility(rowEl) {
    const effect = rowEl.querySelector(".js-code-effect").value;
    const delayContainer = rowEl.querySelector(".js-delay-container");
    const delayInput = rowEl.querySelector(".js-code-delay");

    if (effect === "pacify") {
      delayContainer.classList.add("d-none");
      delayInput.value = "";
      return;
    }

    delayContainer.classList.remove("d-none");
  }

  function collectCodes(container) {
    const rows = Array.from(container.querySelectorAll("[data-code-row='1']"));
    return rows.map(function (row) {
      return {
        code_type: row.querySelector(".js-code-type").value,
        staticValue: row.querySelector(".js-static-value").value.trim(),
        effect: row.querySelector(".js-code-effect").value,
        delay: toNullableInt(row.querySelector(".js-code-delay").value),
      };
    });
  }

  function buildPayload(form, codesContainer) {
    return {
      name: form.elements.name.value.trim(),
      description: form.elements.description.value.trim() || null,
      enabled: form.elements.enabled.checked,
      public: form.elements.public.checked,
      time: toNullableInt(form.elements.time.value),
      notification: toNullableInt(form.elements.notification.value),
      grace: toNullableInt(form.elements.grace.value),
      firstRun: toNullableInt(form.elements.firstRun.value),
      codes: collectCodes(codesContainer),
    };
  }

  function validatePayload(payload) {
    if (!payload.name) {
      return "Name is required.";
    }
    if (!Number.isFinite(payload.time) || payload.time <= 0) {
      return "Countdown time must be a positive number.";
    }
    if (!Array.isArray(payload.codes) || payload.codes.length === 0) {
      return "At least one code is required.";
    }
    for (let i = 0; i < payload.codes.length; i += 1) {
      const code = payload.codes[i];
      if (code.code_type === "static" && !code.staticValue) {
        return `Code ${i + 1}: static value is required.`;
      }
      if (code.delay !== null && code.delay < 0) {
        return `Code ${i + 1}: delay must be zero or greater.`;
      }
    }
    return null;
  }

  async function submitPayload(payload) {
    const response = await window.fetch("/countdowns/create", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || "Failed to create countdown.");
    }

    return response.json();
  }

  function initCountdownCreatePage() {
    const form = document.getElementById("create-countdown-form");
    const codesContainer = document.getElementById("codes-container");
    const addCodeBtn = document.getElementById("add-code-btn");
    const submitBtn = document.getElementById("submit-btn");

    if (!form || !codesContainer || !addCodeBtn || !submitBtn) {
      return;
    }

    function addRow() {
      const index = codesContainer.querySelectorAll("[data-code-row='1']").length;
      const row = createCodeRow(index);
      codesContainer.appendChild(row);
      updateCodeTypeVisibility(row);
      updateEffectVisibility(row);
    }

    addCodeBtn.addEventListener("click", function () {
      addRow();
    });

    codesContainer.addEventListener("change", function (event) {
      const target = event.target;
      if (!(target instanceof Element)) {
        return;
      }
      if (target.classList.contains("js-code-type")) {
        const row = target.closest("[data-code-row='1']");
        if (row) {
          updateCodeTypeVisibility(row);
        }
      }
      if (target.classList.contains("js-code-effect")) {
        const row = target.closest("[data-code-row='1']");
        if (row) {
          updateEffectVisibility(row);
        }
      }
    });

    codesContainer.addEventListener("click", function (event) {
      const target = event.target;
      if (!(target instanceof Element)) {
        return;
      }
      if (!target.classList.contains("js-remove-code")) {
        return;
      }

      const rows = codesContainer.querySelectorAll("[data-code-row='1']");
      if (rows.length <= 1) {
        showAlert("At least one code is required.", "warning");
        return;
      }

      const row = target.closest("[data-code-row='1']");
      if (row) {
        row.remove();
        reindexRows(codesContainer);
      }
    });

    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      showAlert("", "secondary");
      document.getElementById("create-countdown-alert").classList.add("d-none");

      const payload = buildPayload(form, codesContainer);
      const error = validatePayload(payload);
      if (error) {
        showAlert(error, "warning");
        return;
      }

      submitBtn.disabled = true;
      submitBtn.textContent = "Creating...";

      try {
        await submitPayload(payload);
        showAlert("Countdown created successfully. Redirecting...", "success");
        window.setTimeout(function () {
          window.location.href = "/countdowns";
        }, 500);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to create countdown.";
        showAlert(message, "danger");
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Create Countdown";
      }
    });

    addRow();
  }

  window.InsuranceHolderCountdownCreate = {
    init: initCountdownCreatePage,
    buildPayload: buildPayload,
    validatePayload: validatePayload,
  };

  document.addEventListener("DOMContentLoaded", initCountdownCreatePage);
})();
