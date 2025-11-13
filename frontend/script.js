const API_BASE_URL = "http://localhost:8000";

const fileInput = document.getElementById("fileInput");
const uploadSection = document.getElementById("uploadSection");
const fileName = document.getElementById("fileName");
const confSlider = document.getElementById("confSlider");
const iouSlider = document.getElementById("iouSlider");
const confValue = document.getElementById("confValue");
const iouValue = document.getElementById("iouValue");
const processBtn = document.getElementById("processBtn");
const loading = document.getElementById("loading");
const errorDiv = document.getElementById("error");
const imageResult = document.getElementById("imageResult");
const jsonResult = document.getElementById("jsonResult");

let selectedFile = null;
let lastDetectionData = null;

// Tab switching
document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
        const tabName = btn.dataset.tab;

        // Update active tab button
        document
            .querySelectorAll(".tab-btn")
            .forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");

        // Update active tab panel
        document
            .querySelectorAll(".tab-panel")
            .forEach((panel) => panel.classList.remove("active"));
        document.getElementById(tabName + "Tab").classList.add("active");
    });
});

// Update slider values
confSlider.addEventListener("input", (e) => {
    confValue.textContent = e.target.value;
});

iouSlider.addEventListener("input", (e) => {
    iouValue.textContent = e.target.value;
});

// Upload section click
uploadSection.addEventListener("click", () => fileInput.click());

// File input change
fileInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) {
        handleFileSelect(file);
    }
});

// Drag and drop
uploadSection.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadSection.classList.add("drag-over");
});

uploadSection.addEventListener("dragleave", () => {
    uploadSection.classList.remove("drag-over");
});

uploadSection.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadSection.classList.remove("drag-over");

    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith("image/")) {
        handleFileSelect(file);
    }
});

// Handle file selection
function handleFileSelect(file) {
    selectedFile = file;
    fileName.textContent = file.name;

    // Show preview in upload section
    const reader = new FileReader();
    reader.onload = (e) => {
        uploadSection.style.backgroundImage = `url(${e.target.result})`;
        uploadSection.style.backgroundSize = "cover";
        uploadSection.style.backgroundPosition = "center";
        uploadSection.querySelector(".upload-icon").style.display = "none";
        uploadSection.querySelector(".upload-text").style.display = "none";
        uploadSection
            .querySelectorAll(".upload-subtext")
            .forEach((el) => (el.style.display = "none"));
    };
    reader.readAsDataURL(file);
}

// Process button click
processBtn.addEventListener("click", () => {
    if (selectedFile) {
        processImage();
    } else {
        showError("Please select an image first");
    }
});

async function processImage() {
    if (!selectedFile) return;

    // Show loading
    loading.style.display = "flex";
    errorDiv.style.display = "none";
    imageResult.innerHTML =
        '<div class="image-placeholder">Processing...</div>';
    jsonResult.innerHTML = "<pre>Processing...</pre>";

    try {
        const formData = new FormData();
        formData.append("file", selectedFile);

        const conf = parseFloat(confSlider.value);
        const iou = parseFloat(iouSlider.value);

        // Get detection results
        const [detectionResponse, imageResponse] = await Promise.all([
            fetch(`${API_BASE_URL}/detect?conf=${conf}&iou=${iou}`, {
                method: "POST",
                body: formData,
            }),
            fetch(`${API_BASE_URL}/detect/image?conf=${conf}&iou=${iou}`, {
                method: "POST",
                body: formData,
            }),
        ]);

        if (!detectionResponse.ok) {
            const errorData = await detectionResponse.json();
            throw new Error(errorData.detail || "Detection failed");
        }

        if (!imageResponse.ok) {
            throw new Error("Failed to get annotated image");
        }

        const detectionData = await detectionResponse.json();
        const imageBlob = await imageResponse.blob();
        const imageUrl = URL.createObjectURL(imageBlob);

        lastDetectionData = detectionData;

        // Display results
        displayImageResult(imageUrl, detectionData);
        displayJsonResult(detectionData);

        loading.style.display = "none";
    } catch (error) {
        loading.style.display = "none";
        showError(error.message);
    }
}

function displayImageResult(imageUrl, data) {
    imageResult.innerHTML = `<img src="${imageUrl}" alt="Detection Result" class="image-display" />`;
}

function displayJsonResult(data) {
    const detections = data.detections || [];
    const count = data.detection_count || 0;

    // Show detection list
    let html = `<div class="detections-summary">Detected ${count} object${
        count !== 1 ? "s" : ""
    }</div>`;

    if (count > 0) {
        html += '<div class="detections-list">';

        detections.forEach((detection) => {
            const confidence = (detection.confidence * 100).toFixed(1);
            const bbox = detection.bbox;

            // Use Vietnamese class_name if available, otherwise use class key
            const displayName = detection.class_name || detection.class;
            const classKey = detection.class;

            html += `
        <div class="detection-item">
          <div class="detection-header">
            <span class="detection-class">#${
                detection.index
            } ${displayName}</span>
            <span class="detection-confidence">${confidence}%</span>
          </div>
          ${
              detection.class_name
                  ? `<div class="detection-key">Class: ${classKey}</div>`
                  : ""
          }
          <div class="detection-bbox">
            Box: [${Math.round(bbox.x1)}, ${Math.round(bbox.y1)}, ${Math.round(
                bbox.x2
            )}, ${Math.round(bbox.y2)}]
          </div>
        </div>
      `;
        });

        html += "</div>";
    }

    // Add raw JSON with syntax highlighting
    html +=
        '<div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #3a4055;">';
    html +=
        '<div style="color: #b0b3b8; font-size: 0.85rem; margin-bottom: 10px; font-family: system-ui;">Raw JSON:</div>';
    const formatted = syntaxHighlight(JSON.stringify(data, null, 2));
    html += `<div class="json-display"><pre>${formatted}</pre></div>`;
    html += "</div>";

    jsonResult.innerHTML = html;
}

function syntaxHighlight(json) {
    json = json
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    return json.replace(
        /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
        function (match) {
            let cls = "json-number";
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

function showError(message) {
    errorDiv.style.display = "block";
    errorDiv.textContent = `Error: ${message}`;
    setTimeout(() => {
        errorDiv.style.display = "none";
    }, 5000);
}
