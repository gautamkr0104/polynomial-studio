/* ═══════════════════════════════════════════════════════════════
   Polynomial Studio — Frontend Application
   Handles graph preview, API calls, video rendering, UI state
   ═══════════════════════════════════════════════════════════════ */

(function () {
    "use strict";

    // ── State ────────────────────────────────────────────────
    const state = {
        equations: [
            { id: 0, value: "x^3 - 3*x^2 + 2*x", color: "#00e5ff" }
        ],
        nextId: 1,
        selectedTheme: "neon",
        selectedPreset: "instagram_reel",
        currentJobId: null,
        lastVideoUrl: null,
        graphData: null,
        autoRangeY: { min: -6, max: 6 },
    };

    const COLORS = ["#00e5ff", "#e040fb", "#ff4081", "#7c4dff", "#ffab40"];

    // ── Theme & Preset Data ──────────────────────────────────
    const THEMES = {
        neon: { label: "Neon", bg: "#0a0a1a", curve: "#00e5ff", accent: "#7c4dff" },
        minimal: { label: "Minimal", bg: "#fafafa", curve: "#212121", accent: "#757575" },
        aurora: { label: "Aurora", bg: "#0d0221", curve: "#00e5ff", accent: "#d500f9" },
        chalkboard: { label: "Chalk", bg: "#1a2a1a", curve: "#e8e8c8", accent: "#a8b8a8" },
        mathematical: { label: "Math", bg: "#1a1a2e", curve: "#f5a623", accent: "#3498db" },
    };

    const PRESETS = {
        preview:       { label: "Preview",           res: "640×360" },
        instagram_45:  { label: "Instagram 4:5",     res: "1080×1350" },
        instagram_sq:  { label: "Instagram Square",  res: "1080×1080" },
        instagram_reel:{ label: "Instagram Reel",    res: "1080×1920" },
        youtube:       { label: "YouTube",           res: "1920×1080" },
        high:          { label: "High Quality",      res: "1920×1080" },
    };

    // ── DOM References ───────────────────────────────────────
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    // ── Initialize ───────────────────────────────────────────
    document.addEventListener("DOMContentLoaded", init);

    function init() {
        renderEquationList();
        renderThemeGrid();
        renderPresetGrid();
        bindEvents();
    }

    // ── Equation List ────────────────────────────────────────
    function renderEquationList() {
        const container = $("#equationList");
        container.innerHTML = "";

        state.equations.forEach((eq, idx) => {
            const row = document.createElement("div");
            row.className = "equation-row";
            row.innerHTML = `
                <input type="color" class="color-picker-btn" value="${eq.color}"
                       data-id="${eq.id}" title="Curve color">
                <input type="text" value="${escapeHtml(eq.value)}"
                       placeholder="y = x^2" data-id="${eq.id}"
                       class="eq-input" spellcheck="false" autocomplete="off">
                ${state.equations.length > 1 ? `<button class="btn-remove-eq" data-id="${eq.id}" title="Remove">&times;</button>` : ""}
            `;
            container.appendChild(row);
        });

        // Bind events
        container.querySelectorAll(".eq-input").forEach((input) => {
            input.addEventListener("keydown", (e) => {
                if (e.key === "Enter") {
                    e.preventDefault();
                    generatePreview();
                }
            });
            input.addEventListener("input", (e) => {
                const id = parseInt(e.target.dataset.id);
                const eq = state.equations.find((eq) => eq.id === id);
                if (eq) eq.value = e.target.value;
            });
        });

        container.querySelectorAll(".color-picker-btn").forEach((picker) => {
            picker.addEventListener("input", (e) => {
                const id = parseInt(e.target.dataset.id);
                const eq = state.equations.find((eq) => eq.id === id);
                if (eq) {
                    eq.color = e.target.value;
                    if (state.graphData) generatePreview();
                }
            });
        });

        container.querySelectorAll(".btn-remove-eq").forEach((btn) => {
            btn.addEventListener("click", (e) => {
                const id = parseInt(e.target.dataset.id);
                state.equations = state.equations.filter((eq) => eq.id !== id);
                renderEquationList();
            });
        });
    }

    // ── Theme Grid ───────────────────────────────────────────
    function renderThemeGrid() {
        const container = $("#themeGrid");
        container.innerHTML = "";

        Object.entries(THEMES).forEach(([key, theme]) => {
            const btn = document.createElement("button");
            btn.className = `theme-btn ${key === state.selectedTheme ? "active" : ""}`;
            btn.dataset.theme = key;
            btn.innerHTML = `
                <span class="theme-name">${theme.label}</span>
                <div class="theme-preview">
                    <span class="theme-swatch" style="background:${theme.bg};"></span>
                    <span class="theme-swatch" style="background:${theme.curve};"></span>
                    <span class="theme-swatch" style="background:${theme.accent};"></span>
                </div>
            `;
            btn.addEventListener("click", () => {
                state.selectedTheme = key;
                container.querySelectorAll(".theme-btn").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
            });
            container.appendChild(btn);
        });
    }

    // ── Preset Grid ──────────────────────────────────────────
    function renderPresetGrid() {
        const container = $("#presetGrid");
        container.innerHTML = "";

        Object.entries(PRESETS).forEach(([key, preset]) => {
            const btn = document.createElement("button");
            btn.className = `preset-btn ${key === state.selectedPreset ? "active" : ""}`;
            btn.dataset.preset = key;
            btn.innerHTML = `
                <span>${preset.label}</span>
                <span class="preset-res">${preset.res}</span>
            `;
            btn.addEventListener("click", () => {
                state.selectedPreset = key;
                container.querySelectorAll(".preset-btn").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
            });
            container.appendChild(btn);
        });
    }

    // ── Event Binding ────────────────────────────────────────
    function bindEvents() {
        $("#btnAddEquation").addEventListener("click", addEquation);
        $("#btnPreview").addEventListener("click", generatePreview);
        $("#btnRender").addEventListener("click", startRender);
        $("#btnReset").addEventListener("click", resetAll);
        $("#btnAutoRange").addEventListener("click", autoRange);
        $("#btnDownload").addEventListener("click", downloadVideo);
        $("#btnRenderAgain").addEventListener("click", () => {
            $("#videoContainer").style.display = "none";
            $("#previewPlaceholder").style.display = "flex";
            $(".preview-container").style.display = "flex";
        });

        // Draw speed slider
        const speedSlider = $("#optDrawSpeed");
        const speedValue = $("#drawSpeedValue");
        speedSlider.addEventListener("input", () => {
            speedValue.textContent = parseFloat(speedSlider.value).toFixed(1) + "s";
        });
    }

    // ── Add Equation ─────────────────────────────────────────
    function addEquation() {
        if (state.equations.length >= 5) return;
        const colorIdx = state.equations.length % COLORS.length;
        state.equations.push({
            id: state.nextId++,
            value: "",
            color: COLORS[colorIdx],
        });
        renderEquationList();
        // Focus the new input
        const inputs = $$(".eq-input");
        if (inputs.length) inputs[inputs.length - 1].focus();
    }

    // ── Generate Preview ─────────────────────────────────────
    async function generatePreview() {
        const equations = state.equations
            .map((eq) => eq.value.trim())
            .filter((v) => v.length > 0);

        if (equations.length === 0) {
            showError("Please enter at least one polynomial equation.", "Try something like: y = x² - 2x + 1");
            return;
        }

        hideError();
        hideVideo();

        const xMin = parseFloat($("#xMin").value) || -6;
        const xMax = parseFloat($("#xMax").value) || 6;
        const colors = state.equations.map((eq) => eq.color);

        try {
            const [previewRes, analyzeRes] = await Promise.all([
                fetch("/api/preview", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        equations,
                        x_min: xMin,
                        x_max: xMax,
                        colors,
                    }),
                }),
                fetch("/api/analyze", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ equations }),
                }),
            ]);

            const previewData = await previewRes.json();
            const analyzeData = await analyzeRes.json();

            if (previewData.success) {
                state.graphData = previewData;
                // Auto-update y range from data
                state.autoRangeY = { min: previewData.y_min, max: previewData.y_max };
                drawGraph(previewData);
            } else {
                showError(previewData.error || "Preview failed.", "");
            }

            if (analyzeData.success) {
                renderAnalysis(analyzeData.results);
            }

        } catch (err) {
            showError("Could not connect to server. Is Flask running?", err.message);
        }
    }

    // ── Canvas Graph Rendering ───────────────────────────────
    function drawGraph(data) {
        const canvas = $("#graphCanvas");
        const container = $(".preview-container");
        const placeholder = $("#previewPlaceholder");

        placeholder.style.display = "none";
        canvas.style.display = "block";
        container.style.display = "flex";

        // Size canvas to container
        const rect = container.getBoundingClientRect();
        const W = Math.floor(rect.width - 48);
        const H = Math.floor(rect.height - 48);
        canvas.width = W * window.devicePixelRatio;
        canvas.height = H * window.devicePixelRatio;
        canvas.style.width = W + "px";
        canvas.style.height = H + "px";

        const ctx = canvas.getContext("2d");
        const dpr = window.devicePixelRatio;
        ctx.scale(dpr, dpr);

        const theme = THEMES[state.selectedTheme] || THEMES.neon;

        // Background
        ctx.fillStyle = theme.bg;
        ctx.fillRect(0, 0, W, H);

        // Coordinate mapping
        const pad = { left: 50, right: 30, top: 30, bottom: 40 };
        const plotW = W - pad.left - pad.right;
        const plotH = H - pad.top - pad.bottom;

        const xMin = data.x_min;
        const xMax = data.x_max;
        const yMin = data.y_min;
        const yMax = data.y_max;

        function toCanvasX(v) { return pad.left + ((v - xMin) / (xMax - xMin)) * plotW; }
        function toCanvasY(v) { return pad.top + ((yMax - v) / (yMax - yMin)) * plotH; }

        // Grid
        ctx.strokeStyle = "rgba(255,255,255,0.06)";
        ctx.lineWidth = 1;
        const xStep = niceStep(xMax - xMin, 10);
        const yStep = niceStep(yMax - yMin, 10);

        for (let v = Math.ceil(xMin / xStep) * xStep; v <= xMax; v += xStep) {
            const cx = toCanvasX(v);
            ctx.beginPath();
            ctx.moveTo(cx, pad.top);
            ctx.lineTo(cx, pad.top + plotH);
            ctx.stroke();
        }
        for (let v = Math.ceil(yMin / yStep) * yStep; v <= yMax; v += yStep) {
            const cy = toCanvasY(v);
            ctx.beginPath();
            ctx.moveTo(pad.left, cy);
            ctx.lineTo(pad.left + plotW, cy);
            ctx.stroke();
        }

        // Axes
        ctx.strokeStyle = "rgba(255,255,255,0.25)";
        ctx.lineWidth = 1.5;

        // X-axis
        if (yMin <= 0 && yMax >= 0) {
            const y0 = toCanvasY(0);
            ctx.beginPath();
            ctx.moveTo(pad.left, y0);
            ctx.lineTo(pad.left + plotW, y0);
            ctx.stroke();
        }

        // Y-axis
        if (xMin <= 0 && xMax >= 0) {
            const x0 = toCanvasX(0);
            ctx.beginPath();
            ctx.moveTo(x0, pad.top);
            ctx.lineTo(x0, pad.top + plotH);
            ctx.stroke();
        }

        // Axis labels
        ctx.fillStyle = "rgba(255,255,255,0.4)";
        ctx.font = "11px 'JetBrains Mono', monospace";
        ctx.textAlign = "center";

        for (let v = Math.ceil(xMin / xStep) * xStep; v <= xMax; v += xStep) {
            if (Math.abs(v) < 0.001) continue;
            ctx.fillText(formatNum(v), toCanvasX(v), pad.top + plotH + 16);
        }

        ctx.textAlign = "right";
        for (let v = Math.ceil(yMin / yStep) * yStep; v <= yMax; v += yStep) {
            if (Math.abs(v) < 0.001) continue;
            ctx.fillText(formatNum(v), pad.left - 8, toCanvasY(v) + 4);
        }

        // Draw curves
        data.series.forEach((series) => {
            ctx.strokeStyle = series.color;
            ctx.lineWidth = series.thickness || 3;
            ctx.globalAlpha = series.opacity || 1;
            ctx.lineJoin = "round";
            ctx.lineCap = "round";

            if (series.type === "implicit" && series.segments_x) {
                // Implicit contour: draw each segment separately
                for (let s = 0; s < series.segments_x.length; s++) {
                    const segX = series.segments_x[s];
                    const segY = series.segments_y[s];
                    ctx.beginPath();
                    let started = false;
                    for (let i = 0; i < segX.length; i++) {
                        const cx = toCanvasX(segX[i]);
                        const cy = toCanvasY(segY[i]);
                        if (!isFinite(cx) || !isFinite(cy)) {
                            started = false;
                            continue;
                        }
                        if (!started) {
                            ctx.moveTo(cx, cy);
                            started = true;
                        } else {
                            ctx.lineTo(cx, cy);
                        }
                    }
                    ctx.stroke();
                }
            } else {
                // Explicit curve
                ctx.beginPath();
                let started = false;
                for (let i = 0; i < series.x.length; i++) {
                    const xVal = series.x[i];
                    const yVal = series.y[i];
                    if (isNaN(yVal) || !isFinite(yVal)) {
                        started = false;
                        continue;
                    }
                    const cx = toCanvasX(xVal);
                    const cy = toCanvasY(yVal);

                    // Clip to plot area
                    if (cy < pad.top - 20 || cy > pad.top + plotH + 20) {
                        started = false;
                        continue;
                    }

                    if (!started) {
                        ctx.moveTo(cx, cy);
                        started = true;
                    } else {
                        ctx.lineTo(cx, cy);
                    }
                }
                ctx.stroke();
            }
            ctx.globalAlpha = 1;
        });

        // Legend
        if (data.series.length > 1) {
            const legendX = pad.left + 12;
            let legendY = pad.top + 16;
            data.series.forEach((series) => {
                ctx.fillStyle = series.color;
                ctx.beginPath();
                ctx.arc(legendX, legendY, 4, 0, Math.PI * 2);
                ctx.fill();

                ctx.fillStyle = "rgba(255,255,255,0.7)";
                ctx.font = "11px 'Inter', sans-serif";
                ctx.textAlign = "left";
                const label = series.latex.replace("\\", "").replace("{", "").replace("}", "");
                ctx.fillText(label, legendX + 10, legendY + 4);
                legendY += 18;
            });
        }
    }

    function niceStep(range, maxTicks) {
        const rough = range / maxTicks;
        const mag = Math.pow(10, Math.floor(Math.log10(rough)));
        const norm = rough / mag;
        let step;
        if (norm <= 1.5) step = 1;
        else if (norm <= 3) step = 2;
        else if (norm <= 7) step = 5;
        else step = 10;
        return step * mag;
    }

    function formatNum(v) {
        if (Number.isInteger(v)) return v.toString();
        return v.toFixed(1);
    }

    // ── Analysis Rendering ───────────────────────────────────
    function renderAnalysis(results) {
        const container = $("#analysisContent");
        container.innerHTML = "";

        if (!results || results.length === 0) {
            container.innerHTML = '<div class="analysis-placeholder"><p>No results.</p></div>';
            return;
        }

        results.forEach((r, idx) => {
            const div = document.createElement("div");

            if (!r.success) {
                div.innerHTML = `
                    <div class="analysis-eq-header">Equation ${idx + 1}: ${escapeHtml(r.equation)}</div>
                    <div class="analysis-item">
                        <div class="analysis-label">Error</div>
                        <div class="analysis-value" style="color:var(--error);">${escapeHtml(r.error)}</div>
                    </div>
                `;
                container.appendChild(div);
                return;
            }

            const a = r.analysis || {};
            div.innerHTML = `
                <div class="analysis-eq-header" style="border-left: 3px solid ${state.equations[idx]?.color || '#00e5ff'}; padding-left: 0.5rem;">
                    ${escapeHtml(r.equation || "")}
                </div>
                <div class="analysis-item">
                    <div class="analysis-label">LaTeX</div>
                    <div class="analysis-value analysis-latex">${r.latex || ""}</div>
                </div>
                <div class="analysis-item">
                    <div class="analysis-label">Degree</div>
                    <div class="analysis-value highlight">${a.degree ?? "—"}</div>
                </div>
                <div class="analysis-item">
                    <div class="analysis-label">Leading Coefficient</div>
                    <div class="analysis-value">${a.leading_coefficient ?? "—"}</div>
                </div>
                <div class="analysis-item">
                    <div class="analysis-label">Real Roots</div>
                    <div class="analysis-value">${a.roots_real && a.roots_real.length > 0 ? a.roots_real.join(", ") : "None"}</div>
                </div>
                ${a.roots_complex && a.roots_complex.length > 0 ? `
                <div class="analysis-item">
                    <div class="analysis-label">Complex Roots</div>
                    <div class="analysis-value">${a.roots_complex.join(", ")}</div>
                </div>` : ""}
                <div class="analysis-item">
                    <div class="analysis-label">Y-intercept</div>
                    <div class="analysis-value">${a.y_intercept ? `(${a.y_intercept.x}, ${a.y_intercept.y})` : "—"}</div>
                </div>
                <div class="analysis-item">
                    <div class="analysis-label">Derivative</div>
                    <div class="analysis-value">${a.derivative || "—"}</div>
                </div>
                ${a.local_maxima && a.local_maxima.length > 0 ? `
                <div class="analysis-item">
                    <div class="analysis-label">Local Maxima</div>
                    <div class="analysis-value">${a.local_maxima.map(p => `(${p.x}, ${p.y})`).join(", ")}</div>
                </div>` : ""}
                ${a.local_minima && a.local_minima.length > 0 ? `
                <div class="analysis-item">
                    <div class="analysis-label">Local Minima</div>
                    <div class="analysis-value">${a.local_minima.map(p => `(${p.x}, ${p.y})`).join(", ")}</div>
                </div>` : ""}
                ${a.end_behavior && a.end_behavior.description ? `
                <div class="analysis-item">
                    <div class="analysis-label">End Behavior</div>
                    <div class="analysis-value">${escapeHtml(a.end_behavior.description)}</div>
                </div>` : ""}
                ${a.factorized_form ? `
                <div class="analysis-item">
                    <div class="analysis-label">Factorized Form</div>
                    <div class="analysis-value">${escapeHtml(a.factorized_form)}</div>
                </div>` : ""}
            `;
            container.appendChild(div);

            // Re-typeset MathJax
            if (window.MathJax && window.MathJax.typesetPromise) {
                window.MathJax.typesetPromise([div]);
            }
        });
    }

    // ── Render (Manim) ───────────────────────────────────────
    async function startRender() {
        const equations = state.equations
            .map((eq) => eq.value.trim())
            .filter((v) => v.length > 0);

        if (equations.length === 0) {
            showError("Please enter at least one polynomial equation.", "");
            return;
        }

        hideError();
        hideVideo();
        showProgress("Submitting render job...", 10);

        const colors = state.equations.map((eq) => eq.color);

        try {
            const res = await fetch("/api/render", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    equations,
                    colors,
                    quality: state.selectedPreset,
                    theme: state.selectedTheme,
                    animation_options: {
                        show_equation: $("#optShowEquation").checked,
                        show_roots: $("#optShowRoots").checked,
                        show_extrema: $("#optShowExtrema").checked,
                        show_y_intercept: $("#optShowYIntercept").checked,
                        show_labels: $("#optShowLabels").checked,
                        explain_mode: $("#optExplainMode").checked,
                        sequential: $("#optSequential").checked,
                        draw_speed: parseFloat($("#optDrawSpeed").value) || 2.0,
                    },
                }),
            });

            const data = await res.json();

            if (!data.success) {
                hideProgress();
                showError(data.error || "Failed to submit render job.", "");
                return;
            }

            state.currentJobId = data.job_id;
            pollRenderStatus(data.job_id);

        } catch (err) {
            hideProgress();
            showError("Could not connect to server. Is Flask running?", err.message);
        }
    }

    function pollRenderStatus(jobId) {
        const poll = async () => {
            try {
                const res = await fetch(`/api/render-status/${jobId}`);
                const data = await res.json();

                if (!data.success) {
                    hideProgress();
                    showError(
                        "Job not found — the server may have restarted.",
                        "Try submitting the render again."
                    );
                    return;
                }

                const status = data.status;

                if (status.status === "generating") {
                    updateProgress("Generating Manim scene...", status.progress || 20);
                } else if (status.status === "rendering") {
                    updateProgress("Rendering animation with Manim...", status.progress || 50);
                } else if (status.status === "complete") {
                    hideProgress();
                    showVideo(status.video_filename, status.duration);
                    return;
                } else if (status.status === "failed") {
                    hideProgress();
                    showError(status.error || "Rendering failed.", "Check logs/app.log for details.");
                    return;
                }

                // Continue polling
                setTimeout(poll, 1000);
            } catch (err) {
                hideProgress();
                showError("Lost connection during render.", err.message);
            }
        };

        poll();
    }

    // ── Video Display ────────────────────────────────────────
    function showVideo(filename, duration) {
        hideProgress();

        const videoUrl = `/api/video/${filename}`;
        state.lastVideoUrl = videoUrl;

        const preset = PRESETS[state.selectedPreset] || PRESETS.instagram_reel;

        const container = $("#videoContainer");
        container.style.display = "flex";

        $(".preview-container").style.display = "none";

        const player = $("#videoPlayer");
        player.src = videoUrl;
        player.load();

        const meta = $("#videoMeta");
        const durStr = duration ? `${duration.toFixed(1)}s render time` : "";
        meta.textContent = `${preset.label} (${preset.res})${durStr ? " · " + durStr : ""}`;
    }

    function hideVideo() {
        $("#videoContainer").style.display = "none";
        const player = $("#videoPlayer");
        player.pause();
        player.src = "";
    }

    function downloadVideo() {
        if (!state.lastVideoUrl) return;
        const filename = state.lastVideoUrl.split("/").pop();
        window.location.href = `/api/video-download/${filename}`;
    }

    // ── Auto Range ───────────────────────────────────────────
    function autoRange() {
        const y = state.autoRangeY;
        $("#yMin").value = Math.floor(y.min);
        $("#yMax").value = Math.ceil(y.max);
        if (state.graphData) generatePreview();
    }

    // ── Reset ────────────────────────────────────────────────
    function resetAll() {
        state.equations = [{ id: 0, value: "x^3 - 3*x^2 + 2*x", color: COLORS[0] }];
        state.nextId = 1;
        state.graphData = null;
        state.lastVideoUrl = null;

        $("#xMin").value = -6;
        $("#xMax").value = 6;
        $("#yMin").value = -6;
        $("#yMax").value = 6;

        renderEquationList();
        hideVideo();
        hideError();
        hideProgress();

        const canvas = $("#graphCanvas");
        canvas.style.display = "none";
        $("#previewPlaceholder").style.display = "flex";
        $(".preview-container").style.display = "flex";

        $("#analysisContent").innerHTML = '<div class="analysis-placeholder"><p>Analysis will appear here after generating a preview.</p></div>';
    }

    // ── UI Helpers ───────────────────────────────────────────
    function showError(msg, hint) {
        const container = $("#errorDisplay");
        container.style.display = "flex";
        $("#errorMessage").textContent = msg;
        $("#errorHint").textContent = hint || "";
        hideProgress();
    }

    function hideError() {
        $("#errorDisplay").style.display = "none";
    }

    function showProgress(text, pct) {
        const container = $("#renderProgress");
        container.style.display = "flex";
        $("#progressText").textContent = text;
        $("#progressBar").style.width = pct + "%";
    }

    function updateProgress(text, pct) {
        $("#progressText").textContent = text;
        $("#progressBar").style.width = pct + "%";
    }

    function hideProgress() {
        $("#renderProgress").style.display = "none";
    }

    function escapeHtml(str) {
        if (!str) return "";
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

})();
