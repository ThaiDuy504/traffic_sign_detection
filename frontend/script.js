const API_BASE_URL = "http://localhost:8000";
const WS_BASE_URL = "ws://localhost:8000";

// State
let currentMode = "image";
let selectedImageFile = null;
let selectedVideoFile = null;
let cameraStream = null;
let socket = null;
let isCameraRunning = false;

// DOM Elements
const els = {
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
    resultPanels: {
        visual: document.getElementById("visualTab"),
        json: document.getElementById("jsonTab"),
    },
    visualResult: document.getElementById("visualResult"),
    jsonResult: document.getElementById("jsonResult"),
    loading: document.getElementById("loading"),
    error: document.getElementById("error"),
};

// --- Initialization ---

// Mode Tab Switching
els.modeTabs.forEach((btn) => {
    btn.addEventListener("click", () => {
        const mode = btn.dataset.mode;
        currentMode = mode;

        // Update tabs
        els.modeTabs.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");

        // Update panels
        Object.values(els.inputPanels).forEach((p) =>
            p.classList.remove("active")
        );
        els.inputPanels[mode].classList.add("active");

        // Reset results area
        if (!isCameraRunning) {
            els.visualResult.innerHTML =
                '<div class="image-placeholder">Select a mode and start processing</div>';
            els.jsonResult.innerHTML = "<pre>No results yet</pre>";
        }

        // Stop camera if switching away from camera mode
        if (mode !== "camera" && isCameraRunning) {
            stopCamera();
        }
    });
});

// Result Tab Switching
els.resultTabs.forEach((btn) => {
    btn.addEventListener("click", () => {
        const tab = btn.dataset.tab; // 'visual' or 'json'

        els.resultTabs.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");

        document
            .querySelectorAll(".tab-panel")
            .forEach((p) => p.classList.remove("active"));
        document.getElementById(tab + "Tab").classList.add("active");
    });
});

// Slider Updates
els.confSlider.addEventListener(
    "input",
    (e) => (els.confValue.textContent = e.target.value)
);
els.iouSlider.addEventListener(
    "input",
    (e) => (els.iouValue.textContent = e.target.value)
);

// --- Image Logic ---

setupFileUpload(els.imageUploadSection, els.imageInput, (file) => {
    selectedImageFile = file;
    els.imageFileName.textContent = file.name;
    // Preview
    const reader = new FileReader();
    reader.onload = (e) => {
        els.imageUploadSection.style.backgroundImage = `url(${e.target.result})`;
        els.imageUploadSection.style.backgroundSize = "cover";
        els.imageUploadSection.style.backgroundPosition = "center";
        hideUploadText(els.imageUploadSection);
    };
    reader.readAsDataURL(file);
});

els.processImageBtn.addEventListener("click", async () => {
    if (!selectedImageFile) {
        showError("Please select an image first");
        return;
    }

    setLoading(true, "Processing image...");

    try {
        const formData1 = new FormData();
        formData1.append("file", selectedImageFile);

        const formData2 = new FormData();
        formData2.append("file", selectedImageFile);

        const conf = els.confSlider.value;
        const iou = els.iouSlider.value;

        // Parallel fetch: detection data + annotated image
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

        if (!detectRes.ok)
            throw new Error(
                (await detectRes.json()).detail || "Detection failed"
            );
        if (!imgRes.ok) throw new Error("Failed to get image");

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
});

// --- Video Logic ---

setupFileUpload(els.videoUploadSection, els.videoInput, (file) => {
    selectedVideoFile = file;
    els.videoFileName.textContent = file.name;
    // For video preview we might need more logic, or just show icon
    els.videoUploadSection.style.backgroundImage = "none";
    hideUploadText(els.videoUploadSection);
    els.videoUploadSection.querySelector(".upload-icon").style.display =
        "block"; // Keep icon
    els.videoUploadSection.querySelector(".upload-text").textContent =
        "Video Selected";
    els.videoUploadSection.querySelector(".upload-text").style.display =
        "block";
});

let videoSocket = null;
let isVideoProcessing = false;

els.processVideoBtn.addEventListener("click", async () => {
    if (!selectedVideoFile) {
        showError("Please select a video first");
        return;
    }

    if (isVideoProcessing) {
        // Stop processing
        if (videoSocket) {
            videoSocket.close();
            videoSocket = null;
        }
        isVideoProcessing = false;
        els.processVideoBtn.textContent = "Process Video";
        setLoading(false);
        return;
    }

    setLoading(true, "Uploading video...", { dimVisual: false });
    els.processVideoBtn.textContent = "Stop Processing";
    isVideoProcessing = true;

    const conf = els.confSlider.value;
    const iou = els.iouSlider.value;

    try {
        // Step 1: Upload video via HTTP POST
        const formData = new FormData();
        formData.append("file", selectedVideoFile);

        const uploadRes = await fetch(`${API_BASE_URL}/detect/video/upload`, {
            method: "POST",
            body: formData,
        });

        if (!uploadRes.ok) {
            const err = await uploadRes.json();
            throw new Error(err.detail || "Upload failed");
        }

        const { session_id, total_frames, fps } = await uploadRes.json();

        setLoading(true, "Processing video frames...", { dimVisual: false });

        // Step 2: Connect WebSocket with session ID
        videoSocket = new WebSocket(
            `${WS_BASE_URL}/ws/video/${session_id}?conf=${conf}&iou=${iou}`
        );
        videoSocket.binaryType = "arraybuffer";

        let frameCount = 0;
        let lastUrl = null;

        videoSocket.onmessage = (event) => {
            if (!isVideoProcessing) return;

            if (typeof event.data === "string") {
                const msg = JSON.parse(event.data);
                if (msg.type === "done") {
                    setLoading(false);
                    isVideoProcessing = false;
                    els.processVideoBtn.textContent = "Process Video";
                    displayJsonResult({
                        message: "Video processed successfully",
                        filename: selectedVideoFile.name,
                        frames_processed: msg.frames_processed,
                    });
                } else if (msg.error) {
                    throw new Error(msg.error);
                }
            } else {
                // Binary frame data
                frameCount++;

                if (lastUrl) URL.revokeObjectURL(lastUrl);

                const blob = new Blob([event.data], { type: "image/jpeg" });
                const url = URL.createObjectURL(blob);
                lastUrl = url;

                let img = els.visualResult.querySelector("img.video-stream");
                if (!img) {
                    els.visualResult.innerHTML = `<img class="image-display video-stream" src="${url}" />`;
                } else {
                    img.src = url;
                }

                const progress =
                    total_frames > 0
                        ? Math.round((frameCount / total_frames) * 100)
                        : 0;
                setLoading(
                    true,
                    `Processing: ${frameCount}/${total_frames} frames (${progress}%)`,
                    { dimVisual: false }
                );

                displayJsonResult({
                    status: "Processing",
                    total_frames,
                    fps,
                    frames_processed: frameCount,
                    progress: `${progress}%`,
                });
            }
        };

        videoSocket.onerror = () => {
            showError("Video processing connection error");
            cleanup();
        };

        videoSocket.onclose = () => {
            if (isVideoProcessing) cleanup();
        };

        function cleanup() {
            setLoading(false);
            isVideoProcessing = false;
            els.processVideoBtn.textContent = "Process Video";
            videoSocket = null;
        }
    } catch (err) {
        showError(err.message);
        setLoading(false);
        isVideoProcessing = false;
        els.processVideoBtn.textContent = "Process Video";
    }
});

// --- Camera Logic ---

els.startCameraBtn.addEventListener("click", startCamera);
els.stopCameraBtn.addEventListener("click", stopCamera);

async function startCamera() {
    try {
        els.startCameraBtn.classList.add("hidden");
        els.stopCameraBtn.classList.remove("hidden");

        // Get camera stream
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { width: { ideal: 640 }, height: { ideal: 480 } },
        });
        cameraStream = stream;

        // Setup hidden processing elements
        const video = document.createElement("video");
        video.srcObject = stream;
        video.play();
        video.muted = true;

        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");

        // Setup WebSocket
        const conf = els.confSlider.value;
        const iou = els.iouSlider.value;
        socket = new WebSocket(`${WS_BASE_URL}/ws?conf=${conf}&iou=${iou}`);

        let lastUrl = null;
        let isProcessing = false; // Track if we're waiting for a response

        socket.onopen = () => {
            isCameraRunning = true;
            // Switch visual tab to active
            els.visualResult.innerHTML =
                '<div class="image-placeholder">Connecting to server...</div>';
            processFrame();
        };

        socket.onmessage = (event) => {
            if (!isCameraRunning) return;

            isProcessing = false; // Response received, ready for next frame

            // Revoke previous URL to prevent memory leak
            if (lastUrl) {
                URL.revokeObjectURL(lastUrl);
            }

            const url = URL.createObjectURL(event.data);
            lastUrl = url;

            // Update UI efficiently
            // Check if we already have an img tag
            let img = els.visualResult.querySelector("img.camera-stream");
            if (!img) {
                els.visualResult.innerHTML = `<img class="image-display camera-stream" src="${url}" style="display: block;" />`;
            } else {
                img.src = url;
                img.style.display = "block";
            }

            // Request next frame only after we've displayed this one
            requestAnimationFrame(processFrame);
        };

        socket.onerror = (error) => {
            console.error("WebSocket error", error);
            showError("WebSocket connection error");
            stopCamera();
        };

        socket.onclose = () => {
            if (isCameraRunning) stopCamera();
        };

        function processFrame() {
            if (!isCameraRunning || socket.readyState !== WebSocket.OPEN)
                return;

            // Skip if we're still waiting for previous frame to be processed
            if (isProcessing) {
                requestAnimationFrame(processFrame);
                return;
            }

            if (video.readyState === video.HAVE_ENOUGH_DATA) {
                // Reduce resolution for faster processing
                const scaleFactor = 0.5; // Send at 50% resolution
                canvas.width = video.videoWidth * scaleFactor;
                canvas.height = video.videoHeight * scaleFactor;
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

                isProcessing = true; // Mark as processing

                canvas.toBlob(
                    (blob) => {
                        if (blob && socket.readyState === WebSocket.OPEN) {
                            socket.send(blob);
                        } else {
                            isProcessing = false; // Reset if send failed
                        }
                    },
                    "image/jpeg",
                    0.5 // Lower quality for faster transfer
                );
            } else {
                requestAnimationFrame(processFrame);
            }
        }

        displayJsonResult({ status: "Camera streaming started" });
    } catch (err) {
        showError("Camera error: " + err.message);
        stopCamera();
    }
}

function stopCamera() {
    isCameraRunning = false;

    if (cameraStream) {
        cameraStream.getTracks().forEach((track) => track.stop());
        cameraStream = null;
    }

    if (socket) {
        socket.close();
        socket = null;
    }

    els.startCameraBtn.classList.remove("hidden");
    els.stopCameraBtn.classList.add("hidden");
}

// --- Helper Functions ---

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

function hideUploadText(section) {
    section.querySelector(".upload-icon").style.display = "none";
    section.querySelector(".upload-text").style.display = "none";
    section
        .querySelectorAll(".upload-subtext")
        .forEach((el) => (el.style.display = "none"));
}

function setLoading(isLoading, text = "Processing...", options = {}) {
    const { dimVisual = true } = options;
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
    els.error.textContent = "Error: " + msg;
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
    json = json
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    return json.replace(
        /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
        function (match) {
            var cls = "json-number";
            if (/^"/.test(match)) {
                if (/:$/.test(match)) {
                    cls = "json-key";
                } else {
                    cls = "json-string";
                }
            } else if (/true|false/.test(match)) {
                cls = "json-boolean";
            } else if (/null/.test(match)) {
                cls = "json-null";
            }
            return '<span class="' + cls + '">' + match + "</span>";
        }
    );
}
