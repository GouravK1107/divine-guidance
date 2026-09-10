(function () {
  // ===================================================================
  // MOCK DATA LAYER — swap fetchGuidance() for a real Django endpoint:
  //   POST /api/guidance/  { source, question }  ->  same return shape
  // ===================================================================

  // ===================================================================
  // REAL DJANGO RAG API
  // ===================================================================

  async function fetchGuidance(source, question) {
    const apiUrl = document.getElementById("submitBtn").dataset.apiUrl;

    const response = await fetch(apiUrl, {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCSRFToken(),
      },

      body: JSON.stringify({
        source: source,
        question: question,
      }),
    });

    let data;

    try {
      data = await response.json();
    } catch {
      throw new Error("The server returned an invalid response.");
    }

    if (!response.ok) {
      throw new Error(
        data.error || "Something went wrong while seeking guidance.",
      );
    }

    return data;
  }

  // ===================================================================
  // CSRF TOKEN
  // ===================================================================

  function getCSRFToken() {
    const cookie = document.cookie
      .split("; ")
      .find((row) => row.startsWith("csrftoken="));

    if (!cookie) {
      return "";
    }

    return decodeURIComponent(cookie.split("=")[1]);
  }
  // ===================================================================
  // AMBIENT PARTICLE FIELD — slow drifting dust/incense specks
  // ===================================================================

  const reduceMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)",
  ).matches;
  const canvas = document.getElementById("particles");
  const ctx = canvas.getContext("2d");
  let particles = [];
  let w, h;

  function resize() {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
  }

  function makeParticles() {
    const count = Math.min(34, Math.floor((w * h) / 42000));
    particles = Array.from({ length: count }, () => ({
      x: Math.random() * w,
      y: Math.random() * h,
      r: 0.6 + Math.random() * 1.4,
      speed: 0.1 + Math.random() * 0.22,
      drift: (Math.random() - 0.5) * 0.12,
      alpha: 0.08 + Math.random() * 0.22,
      phase: Math.random() * Math.PI * 2,
    }));
  }

  function drawParticles(t) {
    ctx.clearRect(0, 0, w, h);
    particles.forEach((p) => {
      const flicker = 0.7 + 0.3 * Math.sin(t / 1400 + p.phase);
      ctx.beginPath();
      ctx.fillStyle = `rgba(205,168,106,${p.alpha * flicker})`;
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fill();

      if (!reduceMotion) {
        p.y -= p.speed;
        p.x += p.drift;
        if (p.y < -10) {
          p.y = h + 10;
          p.x = Math.random() * w;
        }
        if (p.x < -10) p.x = w + 10;
        if (p.x > w + 10) p.x = -10;
      }
    });
  }

  function loop(t) {
    drawParticles(t);
    if (!reduceMotion) requestAnimationFrame(loop);
  }

  resize();
  makeParticles();
  requestAnimationFrame(loop);
  window.addEventListener("resize", () => {
    resize();
    makeParticles();
  });

  // ===================================================================
  // CURSOR SPOTLIGHT (desktop only, throttled)
  // ===================================================================

  const spotlight = document.getElementById("spotlight");
  let ticking = false;
  window.addEventListener("mousemove", (e) => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => {
      spotlight.style.setProperty("--mx", e.clientX + "px");
      spotlight.style.setProperty("--my", e.clientY + "px");
      ticking = false;
    });
  });

  // ===================================================================
  // UI WIRING
  // ===================================================================

  const sourceCards = document.querySelectorAll(".source-card");
  const questionEl = document.getElementById("question");
  const submitBtn = document.getElementById("submitBtn");
  const responseEl = document.getElementById("response");
  let selectedSource = null;

  function spawnRipple(card, evt) {
    const rect = card.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height) * 1.4;
    const ripple = document.createElement("span");
    ripple.className = "ripple";
    const originX =
      evt && evt.clientX ? evt.clientX - rect.left : rect.width / 2;
    const originY =
      evt && evt.clientY ? evt.clientY - rect.top : rect.height / 2;
    ripple.style.width = ripple.style.height = size + "px";
    ripple.style.left = originX - size / 2 + "px";
    ripple.style.top = originY - size / 2 + "px";
    card.appendChild(ripple);
    ripple.addEventListener("animationend", () => ripple.remove());
  }

  function selectSource(card, evt) {
    sourceCards.forEach((c) => {
      c.classList.remove("selected");
      c.setAttribute("aria-pressed", "false");
    });
    card.classList.add("selected");
    card.setAttribute("aria-pressed", "true");
    selectedSource = card.dataset.source;
    spawnRipple(card, evt);
  }

  sourceCards.forEach((card) => {
    card.addEventListener("click", (e) => selectSource(card, e));
    card.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        selectSource(card);
      }
    });
  });

  document.querySelectorAll(".example-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      questionEl.value = chip.textContent;
      questionEl.focus();
    });
  });

  function nudge(el) {
    el.style.borderColor = "rgba(205,168,106,0.5)";
    setTimeout(() => {
      el.style.borderColor = "";
    }, 900);
  }

  async function handleSubmit() {
    const question = questionEl.value.trim();

    // --------------------------------------------------
    // Source validation
    // --------------------------------------------------

    if (!selectedSource) {
      document.getElementById("sources").scrollIntoView({
        behavior: "smooth",
        block: "center",
      });

      sourceCards.forEach(nudge);

      return;
    }

    // --------------------------------------------------
    // Question validation
    // --------------------------------------------------

    if (!question) {
      questionEl.focus();

      nudge(questionEl);

      return;
    }

    // --------------------------------------------------
    // Loading state
    // --------------------------------------------------

    submitBtn.classList.add("loading");
    submitBtn.disabled = true;

    try {
      // ==================================================
      // REAL RAG REQUEST
      // ==================================================

      const data = await fetchGuidance(selectedSource, question);

      const result = data.result;

      // ==================================================
      // RESPONSE TITLE
      // ==================================================

      document.getElementById("responseTitle").textContent =
        `Guidance from the ${data.label}`;

      // ==================================================
      // SITUATION
      // ==================================================

      document.getElementById("situationText").textContent = question;

      // ==================================================
      // RELEVANT TEACHING
      // ==================================================

      document.getElementById("scriptureText").textContent =
        `"${result.english}"`;

      document.getElementById("scriptureRef").textContent = result.source;

      // ==================================================
      // REFLECTION
      //
      // Gemini is NOT connected yet.
      // So for now we keep this explicit instead of
      // pretending that an AI reflection was generated.
      // ==================================================

      document
        .getElementById("reflectionText")
        .textContent = data.guidance;
      // ==================================================
      // SOURCES
      //
      // Show all retrieved verses, but keep the UI clean.
      // ==================================================

      const list = document.getElementById("sourcesList");

      list.innerHTML = "";

      data.results.forEach((item) => {
        const li = document.createElement("li");

        li.textContent = `${item.source} · relevance ${item.score}`;

        list.appendChild(li);
      });

      // ==================================================
      // LOADING OFF
      // ==================================================

      submitBtn.classList.remove("loading");
      submitBtn.disabled = false;

      // ==================================================
      // SHOW RESPONSE
      // ==================================================

      responseEl.classList.add("open");

      // ==================================================
      // STAGGERED REVEAL
      // ==================================================

      const blocks = [
        "rb-situation",
        "rb-teaching",
        "rb-reflection",
        "rb-sources",
      ];

      blocks.forEach((id) => {
        document.getElementById(id).classList.remove("reveal");
      });

      blocks.forEach((id, i) => {
        setTimeout(
          () => {
            document.getElementById(id).classList.add("reveal");
          },
          120 + i * 160,
        );
      });

      // ==================================================
      // SCROLL TO RESPONSE
      // ==================================================

      setTimeout(() => {
        responseEl.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }, 180);
    } catch (error) {
      console.error("Guidance request failed:", error);

      // --------------------------------------------------
      // User-friendly error
      // --------------------------------------------------

      submitBtn.classList.remove("loading");
      submitBtn.disabled = false;

      // Don't create another ugly UI component.
      // Use the existing question area for feedback.
      nudge(questionEl);

      console.error(error.message);

      alert(error.message || "Something went wrong while seeking guidance.");
    }
  }

  submitBtn.addEventListener("click", handleSubmit);
})();
