const cameraUrlInput = document.getElementById("cameraUrl");
const analyzeButton = document.getElementById("analyzeButton");
const statusMessage = document.getElementById("statusMessage");
const totalSlotsElement = document.getElementById("totalSlots");
const occupiedSlotsElement = document.getElementById("occupiedSlots");
const freeSlotsElement = document.getElementById("freeSlots");
const imagePlaceholder = document.getElementById("imagePlaceholder");
const parkingImage = document.getElementById("parkingImage");
const slotList = document.getElementById("slotList");

analyzeButton.addEventListener("click", handleAnalyze);

async function handleAnalyze() {
  const cameraUrl = cameraUrlInput.value.trim();

  if (!cameraUrl) {
    setStatus("Enter an RTSP or HTTP camera URL before running the analysis.", "error");
    return;
  }

  setLoadingState(true);
  setStatus("Capturing one frame and analyzing parking slots...", "idle");

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ camera_url: cameraUrl }),
    });

    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.detail || "Parking analysis failed.");
    }

    renderCounts(payload.counts);
    renderAnnotatedImage(payload.annotated_image);
    renderSlots(payload.slot_statuses);
    setStatus("Processed one frame successfully.", "success");
  } catch (error) {
    setStatus(error.message || "Parking analysis failed.", "error");
  } finally {
    setLoadingState(false);
  }
}

function setLoadingState(isLoading) {
  analyzeButton.disabled = isLoading;
  analyzeButton.textContent = isLoading ? "Processing..." : "Show Parking Area";
}

function setStatus(message, tone) {
  statusMessage.textContent = message;
  statusMessage.className = `status status-${tone}`;
}

function renderCounts(counts) {
  totalSlotsElement.textContent = counts.total_slots;
  occupiedSlotsElement.textContent = counts.occupied_slots;
  freeSlotsElement.textContent = counts.free_slots;
}

function renderAnnotatedImage(base64Image) {
  parkingImage.src = `data:image/jpeg;base64,${base64Image}`;
  parkingImage.hidden = false;
  imagePlaceholder.hidden = true;
}

function renderSlots(slots) {
  if (!slots.length) {
    slotList.className = "slot-list empty-state";
    slotList.textContent = "No slots were returned by the backend.";
    return;
  }

  slotList.className = "slot-list";
  slotList.innerHTML = slots
    .map((slot) => {
      const badgeClass = slot.state === "FREE" ? "free" : "occupied";
      const overlapPercent = `${(slot.overlap * 100).toFixed(1)}% overlap`;
      return `
        <article class="slot-item">
          <div>
            <strong>${slot.id}</strong>
            <div class="slot-meta">
              (${slot.x}, ${slot.y}) · ${slot.width} x ${slot.height} · ${overlapPercent}
            </div>
          </div>
          <span class="slot-badge ${badgeClass}">${slot.state}</span>
        </article>
      `;
    })
    .join("");
}
