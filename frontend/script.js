// =============================================================================
// Configuration
// =============================================================================

const API_BASE_URL = "http://localhost:8000";
const WS_BASE_URL = "ws://localhost:8000";

// Video processing settings
const VIDEO_FRAME_SKIP = 2; // Process every Nth frame (1 = all, 2 = half, 3 = third)

// =============================================================================
// State
// =============================================================================

const state = {
    currentMode: "image",
    selectedImageFile: null,
    selectedVideoFile: null,
    // Camera
    cameraStream: null,
    cameraVideo: null,
    cameraSocket: null,
    isCameraRunning: false,
    // Video
    videoSocket: null,
    isVideoProcessing: false,
};

// =============================================================================
// DOM Elements
// =============================================================================

const els = {
    // Theme
    themeToggle: document.getElementById("themeToggle"),

    // Mode Tabs
    modeTabs: document.querySelectorAll(".input-tab"),
    inputPanels: {
        image: document.getElementById("imageInputPanel"),
        video: document.getElementById("videoInputPanel"),
        camera: document.getElementById("cameraInputPanel"),
    },

    // Image Input
    imageInput: document.getElementById("imageInput"),
    imageUploadSection: document.getElementById("imageUploadSection"),
    imageFileName: document.getElementById("imageFileName"),
    processImageBtn: document.getElementById("processImageBtn"),

    // Video Input
    videoInput: document.getElementById("videoInput"),
    videoUploadSection: document.getElementById("videoUploadSection"),
    videoFileName: document.getElementById("videoFileName"),
    processVideoBtn: document.getElementById("processVideoBtn"),

    // Camera Input
    startCameraBtn: document.getElementById("startCameraBtn"),
    stopCameraBtn: document.getElementById("stopCameraBtn"),

    // Controls
    confSlider: document.getElementById("confSlider"),
    iouSlider: document.getElementById("iouSlider"),
    confValue: document.getElementById("confValue"),
    iouValue: document.getElementById("iouValue"),

    // Results
    resultTabs: document.querySelectorAll(".tab-btn"),
    visualResult: document.getElementById("visualResult"),
    jsonResult: document.getElementById("jsonResult"),
    loading: document.getElementById("loading"),
    error: document.getElementById("error"),
};

// =============================================================================
// Utilities
// =============================================================================

const getThresholds = () => ({
    conf: els.confSlider.value,
    iou: els.iouSlider.value,
});

function setLoading(
    isLoading,
    text = "Processing...",
    { dimVisual = true } = {}
) {
    if (isLoading) {
        els.loading.style.display = "flex";
        els.loading.querySelector("p").textContent = text;
        els.error.style.display = "none";
        els.visualResult.style.opacity = dimVisual ? "0.5" : "1";
    } else {
        els.loading.style.display = "none";
        els.visualResult.style.opacity = "1";
    }
}

function showError(msg) {
    els.error.style.display = "block";
    els.error.textContent = `Error: ${msg}`;
    setTimeout(() => (els.error.style.display = "none"), 5000);
}

function displayVisualResult(html) {
    els.visualResult.innerHTML = html;
}

function displayJsonResult(data) {
    els.jsonResult.innerHTML = `<pre>${syntaxHighlight(
        JSON.stringify(data, null, 2)
    )}</pre>`;
}

function syntaxHighlight(json) {
    const escaped = json
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

    return escaped.replace(
        /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g,
        (match) => {
            let cls = "json-number";
            if (/^"/.test(match)) {
                cls = /:$/.test(match) ? "json-key" : "json-string";
            } else if (/true|false/.test(match)) {
                cls = "json-boolean";
            } else if (/null/.test(match)) {
                cls = "json-null";
            }
            return `<span class="${cls}">${match}</span>`;
        }
    );
}

function resetResultsArea() {
    els.visualResult.innerHTML =
        '<div class="image-placeholder">Select a mode and start processing</div>';
    els.jsonResult.innerHTML = "<pre>No results yet</pre>";
}

function hideUploadText(section) {
    section.querySelector(".upload-icon").style.display = "none";
    section.querySelector(".upload-text").style.display = "none";
    section
        .querySelectorAll(".upload-subtext")
        .forEach((el) => (el.style.display = "none"));
}

function setupFileUpload(section, input, onSelect) {
    section.addEventListener("click", () => input.click());

    input.addEventListener("change", (e) => {
        if (e.target.files[0]) onSelect(e.target.files[0]);
    });

    section.addEventListener("dragover", (e) => {
        e.preventDefault();
        section.classList.add("drag-over");
    });

    section.addEventListener("dragleave", () => {
        section.classList.remove("drag-over");
    });

    section.addEventListener("drop", (e) => {
        e.preventDefault();
        section.classList.remove("drag-over");
        if (e.dataTransfer.files[0]) onSelect(e.dataTransfer.files[0]);
    });
}

// =============================================================================
// Theme
// =============================================================================

function initTheme() {
    const savedTheme = localStorage.getItem("theme") || "dark";
    document.documentElement.setAttribute("data-theme", savedTheme);

    els.themeToggle.addEventListener("click", () => {
        const current = document.documentElement.getAttribute("data-theme");
        const next = current === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", next);
        localStorage.setItem("theme", next);
    });
}

// =============================================================================
// Tab Navigation
// =============================================================================

function initTabs() {
    // Mode tabs (image/video/camera)
    els.modeTabs.forEach((btn) => {
        btn.addEventListener("click", () => {
            const mode = btn.dataset.mode;
            state.currentMode = mode;

            els.modeTabs.forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");

            Object.values(els.inputPanels).forEach((p) =>
                p.classList.remove("active")
            );
            els.inputPanels[mode].classList.add("active");

            if (!state.isCameraRunning) {
                resetResultsArea();
            }

            if (mode !== "camera" && state.isCameraRunning) {
                stopCamera();
            }
        });
    });

    // Result tabs (visual/json)
    els.resultTabs.forEach((btn) => {
        btn.addEventListener("click", () => {
            const tab = btn.dataset.tab;

            els.resultTabs.forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");

            document
                .querySelectorAll(".tab-panel")
                .forEach((p) => p.classList.remove("active"));
            document.getElementById(`${tab}Tab`).classList.add("active");
        });
    });
}

// =============================================================================
// Sliders
// =============================================================================

function initSliders() {
    els.confSlider.addEventListener("input", (e) => {
        els.confValue.textContent = e.target.value;
    });

    els.iouSlider.addEventListener("input", (e) => {
        els.iouValue.textContent = e.target.value;
    });
}

// =============================================================================
// Image Processing
// =============================================================================

function initImageProcessing() {
    setupFileUpload(els.imageUploadSection, els.imageInput, (file) => {
        state.selectedImageFile = file;
        els.imageFileName.textContent = file.name;

        const reader = new FileReader();
        reader.onload = (e) => {
            els.imageUploadSection.style.backgroundImage = `url(${e.target.result})`;
            els.imageUploadSection.style.backgroundSize = "cover";
            els.imageUploadSection.style.backgroundPosition = "center";
            hideUploadText(els.imageUploadSection);
        };
        reader.readAsDataURL(file);
    });

    els.processImageBtn.addEventListener("click", processImage);
}

async function processImage() {
    if (!state.selectedImageFile) {
        showError("Please select an image first");
        return;
    }

    setLoading(true, "Processing image...");

    try {
        const { conf, iou } = getThresholds();

        const formData1 = new FormData();
        formData1.append("file", state.selectedImageFile);

        const formData2 = new FormData();
        formData2.append("file", state.selectedImageFile);

        const [detectRes, imgRes] = await Promise.all([
            fetch(`${API_BASE_URL}/detect?conf=${conf}&iou=${iou}`, {
                method: "POST",
                body: formData1,
            }),
            fetch(`${API_BASE_URL}/detect/image?conf=${conf}&iou=${iou}`, {
                method: "POST",
                body: formData2,
            }),
        ]);

        if (!detectRes.ok) {
            throw new Error(
                (await detectRes.json()).detail || "Detection failed"
            );
        }
        if (!imgRes.ok) {
            throw new Error("Failed to get image");
        }

        const data = await detectRes.json();
        const blob = await imgRes.blob();
        const url = URL.createObjectURL(blob);

        displayVisualResult(
            `<img src="${url}" class="image-display" alt="Result" />`
        );
        displayJsonResult(data);
    } catch (err) {
        showError(err.message);
    } finally {
        setLoading(false);
    }
}

// =============================================================================
// Video Processing
// =============================================================================

function initVideoProcessing() {
    setupFileUpload(els.videoUploadSection, els.videoInput, (file) => {
        state.selectedVideoFile = file;
        els.videoFileName.textContent = file.name;

        els.videoUploadSection.style.backgroundImage = "none";
        hideUploadText(els.videoUploadSection);

        const icon = els.videoUploadSection.querySelector(".upload-icon");
        const text = els.videoUploadSection.querySelector(".upload-text");
        icon.style.display = "block";
        text.textContent = "Video Selected";
        text.style.display = "block";
    });

    els.processVideoBtn.addEventListener("click", toggleVideoProcessing);
}

async function toggleVideoProcessing() {
    if (state.isVideoProcessing) {
        stopVideoProcessing();
        return;
    }

    if (!state.selectedVideoFile) {
        showError("Please select a video first");
        return;
    }

    await startVideoProcessing();
}

function stopVideoProcessing() {
    if (state.videoSocket) {
        state.videoSocket.close();
        state.videoSocket = null;
    }
    state.isVideoProcessing = false;
    els.processVideoBtn.textContent = "Process Video";
    setLoading(false);
}

async function startVideoProcessing() {
    setLoading(true, "Uploading video...", { dimVisual: false });
    els.processVideoBtn.textContent = "Stop Processing";
    state.isVideoProcessing = true;

    const { conf, iou } = getThresholds();

    try {
        // Upload video
        const formData = new FormData();
        formData.append("file", state.selectedVideoFile);

        const uploadRes = await fetch(`${API_BASE_URL}/detect/video/upload`, {
            method: "POST",
            body: formData,
        });

        if (!uploadRes.ok) {
            const err = await uploadRes.json();
            throw new Error(err.detail || "Upload failed");
        }

        const { session_id } = await uploadRes.json();

        setLoading(true, "Processing video frames...", { dimVisual: false });

        // Connect WebSocket with frame_skip for faster processing
        state.videoSocket = new WebSocket(
            `${WS_BASE_URL}/ws/video/${session_id}?conf=${conf}&iou=${iou}&frame_skip=${VIDEO_FRAME_SKIP}`
        );
        state.videoSocket.binaryType = "arraybuffer";

        let frameCount = 0;
        let lastUrl = null;
        let metadata = null;

        state.videoSocket.onmessage = (event) => {
            if (!state.isVideoProcessing) return;

            if (typeof event.data === "string") {
                const msg = JSON.parse(event.data);
                if (msg.type === "metadata") {
                    metadata = msg;
                } else if (msg.type === "done") {
                    stopVideoProcessing();
                    displayJsonResult({
                        message: "Video processed successfully",
                        filename: state.selectedVideoFile.name,
                        frames_processed: msg.frames_processed,
                        frame_skip: metadata?.frame_skip || 1,
                    });
                } else if (msg.error) {
                    showError(msg.error);
                    stopVideoProcessing();
                }
            } else {
                frameCount++;
                if (lastUrl) URL.revokeObjectURL(lastUrl);

                const blob = new Blob([event.data], { type: "image/jpeg" });
                const url = URL.createObjectURL(blob);
                lastUrl = url;

                const img = els.visualResult.querySelector("img.video-stream");
                if (!img) {
                    els.visualResult.innerHTML = `<img class="image-display video-stream" src="${url}" />`;
                } else {
                    img.src = url;
                }

                const totalFrames = metadata?.total_frames || 0;
                const progress =
                    totalFrames > 0
                        ? Math.round((frameCount / totalFrames) * 100)
                        : 0;
                setLoading(
                    true,
                    `Processing: ${frameCount}/${totalFrames} frames (${progress}%)`,
                    {
                        dimVisual: false,
                    }
                );

                displayJsonResult({
                    status: "Processing",
                    total_frames: totalFrames,
                    original_frames: metadata?.original_frames,
                    fps: metadata?.fps,
                    frame_skip: metadata?.frame_skip,
                    frames_processed: frameCount,
                    progress: `${progress}%`,
                });
            }
        };

        state.videoSocket.onerror = () => {
            showError("Video processing connection error");
            stopVideoProcessing();
        };

        state.videoSocket.onclose = () => {
            if (state.isVideoProcessing) stopVideoProcessing();
        };
    } catch (err) {
        showError(err.message);
        stopVideoProcessing();
    }
}

// =============================================================================
// Camera Processing
// =============================================================================

function initCameraProcessing() {
    els.startCameraBtn.addEventListener("click", startCamera);
    els.stopCameraBtn.addEventListener("click", stopCamera);
}

async function startCamera() {
    try {
        els.startCameraBtn.classList.add("hidden");
        els.stopCameraBtn.classList.remove("hidden");

        const stream = await navigator.mediaDevices.getUserMedia({
            video: { width: { ideal: 640 }, height: { ideal: 480 } },
        });
        state.cameraStream = stream;

        state.cameraVideo = document.createElement("video");
        state.cameraVideo.srcObject = stream;
        state.cameraVideo.play();
        state.cameraVideo.muted = true;

        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d", { willReadFrequently: true });

        const { conf, iou } = getThresholds();
        state.cameraSocket = new WebSocket(
            `${WS_BASE_URL}/ws?conf=${conf}&iou=${iou}`
        );

        let lastUrl = null;
        let pendingFrames = 0;
        const MAX_PENDING = 2; // Allow up to 2 in-flight frames for pipelining
        const TARGET_FPS = 15; // Cap sending rate
        const FRAME_INTERVAL = 1000 / TARGET_FPS;
        let lastFrameTime = 0;
        let sendLoopId = null;

        state.cameraSocket.onopen = () => {
            state.isCameraRunning = true;
            els.visualResult.innerHTML =
                '<div class="image-placeholder">Connecting to server...</div>';
            // Start the send loop (decoupled from receive)
            sendLoop();
        };

        state.cameraSocket.onmessage = (event) => {
            if (!state.isCameraRunning) return;

            pendingFrames = Math.max(0, pendingFrames - 1);

            if (lastUrl) URL.revokeObjectURL(lastUrl);

            const url = URL.createObjectURL(event.data);
            lastUrl = url;

            const img = els.visualResult.querySelector("img.camera-stream");
            if (!img) {
                els.visualResult.innerHTML = `<img class="image-display camera-stream" src="${url}" style="display: block;" />`;
            } else {
                img.src = url;
                img.style.display = "block";
            }
        };

        state.cameraSocket.onerror = (error) => {
            console.error("WebSocket error", error);
            showError("WebSocket connection error");
            stopCamera();
        };

        state.cameraSocket.onclose = () => {
            if (sendLoopId) cancelAnimationFrame(sendLoopId);
            if (state.isCameraRunning) stopCamera();
        };

        function sendLoop(timestamp = 0) {
            if (
                !state.isCameraRunning ||
                !state.cameraSocket ||
                state.cameraSocket.readyState !== WebSocket.OPEN
            ) {
                return;
            }

            sendLoopId = requestAnimationFrame(sendLoop);

            // Throttle to target FPS
            if (timestamp - lastFrameTime < FRAME_INTERVAL) return;

            // Skip if too many frames pending (backpressure)
            if (pendingFrames >= MAX_PENDING) return;

            if (
                state.cameraVideo.readyState !==
                state.cameraVideo.HAVE_ENOUGH_DATA
            ) {
                return;
            }

            lastFrameTime = timestamp;

            // Use smaller resolution for faster processing
            const targetWidth = 320;
            const scale = targetWidth / state.cameraVideo.videoWidth;
            canvas.width = targetWidth;
            canvas.height = state.cameraVideo.videoHeight * scale;
            ctx.drawImage(state.cameraVideo, 0, 0, canvas.width, canvas.height);

            canvas.toBlob(
                (blob) => {
                    if (
                        blob &&
                        state.cameraSocket &&
                        state.cameraSocket.readyState === WebSocket.OPEN
                    ) {
                        pendingFrames++;
                        state.cameraSocket.send(blob);
                    }
                },
                "image/jpeg",
                0.6 // Slightly better quality since we're sending fewer frames
            );
        }

        displayJsonResult({ status: "Camera streaming started" });
    } catch (err) {
        showError(`Camera error: ${err.message}`);
        stopCamera();
    }
}

function stopCamera() {
    state.isCameraRunning = false;

    if (state.cameraVideo) {
        state.cameraVideo.pause();
        state.cameraVideo.srcObject = null;
        state.cameraVideo = null;
    }

    if (state.cameraStream) {
        state.cameraStream.getTracks().forEach((track) => track.stop());
        state.cameraStream = null;
    }

    if (state.cameraSocket) {
        state.cameraSocket.close();
        state.cameraSocket = null;
    }

    els.startCameraBtn.classList.remove("hidden");
    els.stopCameraBtn.classList.add("hidden");

    els.visualResult.innerHTML =
        '<div class="image-placeholder">Camera stopped</div>';
}

// =============================================================================
// Initialize
// =============================================================================

function init() {
    initTheme();
    initTabs();
    initSliders();
    initImageProcessing();
    initVideoProcessing();
    initCameraProcessing();
}

init();
