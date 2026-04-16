let mapInstance = null;
let markerInstance = null;

// ── Issue #6: Ausgewaehlte Dateien zaehlen ─────────────────────────────────────
function updateSelectedCount() {
  const checkboxes = document.querySelectorAll('input[name="selected_files"]');
  const checked = Array.from(checkboxes).filter(cb => cb.checked).length;
  const span = document.getElementById('selected-count');
  const btn  = document.getElementById('apply-btn');

  if (span) {
    if (checked === 0) {
      span.textContent = 'Keine Dateien ausgewaehlt';
      span.className = 'selected-count count-empty';
    } else if (checked === 1) {
      span.textContent = '1 Datei ausgewaehlt';
      span.className = 'selected-count count-active';
    } else {
      span.textContent = `${checked} Dateien ausgewaehlt`;
      span.className = 'selected-count count-active';
    }
  }
  if (btn) btn.disabled = checked === 0;
}

function initSelectedCount() {
  const checkboxes = document.querySelectorAll('input[name="selected_files"]');
  checkboxes.forEach(cb => cb.addEventListener('change', updateSelectedCount));

  // Auch "Alle auswaehlen" mitverfolgen
  const selectAll = document.getElementById('select-all');
  if (selectAll) {
    selectAll.addEventListener('change', updateSelectedCount);
  }

  updateSelectedCount(); // initialer Stand
}

// ── Issue #7: Ausgewaehlte Zeile in sichtbaren Bereich scrollen ────────────────
function scrollToSelected() {
  const selected = document.querySelector('.file-row.selected');
  if (selected) {
    selected.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }
}

// Konvertiert datetime-local Wert in EXIF-Format "YYYY:MM:DD HH:MM:SS"
function syncDateTimeToExif() {
  const dtInput = document.getElementById("dt-picker");
  const hidden = document.getElementById("exif-datetime-hidden");
  if (!dtInput || !hidden || !dtInput.value) {
    hidden.value = "";
    return;
  }
  const raw = dtInput.value;
  const [datePart, timePart] = raw.split("T");
  if (!datePart || !timePart) {
    hidden.value = "";
    return;
  }
  const exifDate = datePart.replace(/-/g, ":");
  let t = timePart;
  if (t.length === 5) {
    t = t + ":00";
  }
  hidden.value = `${exifDate} ${t}`;
}

function initDateBinding() {
  const dtInput = document.getElementById("dt-picker");
  if (!dtInput) return;
  dtInput.addEventListener("change", syncDateTimeToExif);
  dtInput.addEventListener("input", syncDateTimeToExif);
  syncDateTimeToExif();
}

function initMap() {
  const mapEl = document.getElementById("map");
  const latInput = document.getElementById("lat");
  const lonInput = document.getElementById("lon");
  if (!mapEl || !latInput || !lonInput || !window.L) return;

  const defaultLat = 48.401;
  const defaultLon = 16.168;
  let lat = parseFloat(latInput.value) || defaultLat;
  let lon = parseFloat(lonInput.value) || defaultLon;

  const map = L.map(mapEl).setView([lat, lon], 10);
  mapInstance = map;

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap-Mitwirkende",
  }).addTo(map);

  let marker = L.marker([lat, lon], { draggable: true }).addTo(map);
  markerInstance = marker;

  function updateInputsFrom(lat, lon) {
    latInput.value = lat.toFixed(6);
    lonInput.value = lon.toFixed(6);
    syncDateTimeToExif();
  }

  map.on("click", (e) => {
    const { lat, lng } = e.latlng;
    marker.setLatLng([lat, lng]);
    updateInputsFrom(lat, lng);
  });

  marker.on("dragend", () => {
    const { lat, lng } = marker.getLatLng();
    updateInputsFrom(lat, lng);
  });

  if (L.Control && L.Control.Geocoder) {
    L.Control.geocoder({
      defaultMarkGeocode: false,
      placeholder: "Ort suchen...",
      geocoder: L.Control.Geocoder.nominatim(),
    }).on("markgeocode", (e) => {
      const center = e.geocode.center;
      marker.setLatLng(center);
      map.setView(center, 14);
      updateInputsFrom(center.lat, center.lng);
    }).addTo(map);
  } else {
    console.warn("Leaflet Geocoder plugin not available - no search box on map");
  }
}

async function rotatePhoto(direction) {
  const fileInput = document.getElementById("preview-file");
  const subdirInput = document.getElementById("hidden-subdir");
  const img = document.getElementById("photo-preview");
  if (!fileInput || !fileInput.value || !img) return;

  const fd = new FormData();
  fd.append("file", fileInput.value);
  fd.append("subdir", subdirInput ? subdirInput.value : "");
  fd.append("direction", direction);

  try {
    const resp = await fetch("/rotate", { method: "POST", body: fd });
    if (!resp.ok) {
      const data = await resp.json().catch(() => ({}));
      alert("Fehler beim Drehen: " + (data.error || resp.status));
      return;
    }
    window.location.reload();
  } catch (err) {
    alert("Netzwerkfehler beim Drehen: " + err);
  }
}

async function searchPlace() {
  const input = document.getElementById("place-search");
  const latInput = document.getElementById("lat");
  const lonInput = document.getElementById("lon");
  if (!input || !latInput || !lonInput || !mapInstance || !markerInstance) return;

  const q = input.value.trim();
  if (!q) return;

  try {
    const resp = await fetch(
      "https://nominatim.openstreetmap.org/search?format=json&q=" +
        encodeURIComponent(q)
    );
    if (!resp.ok) {
      alert("Fehler bei der Ortssuche: " + resp.status);
      return;
    }
    const data = await resp.json();
    if (!data.length) {
      alert("Kein Ort gefunden.");
      return;
    }
    const lat = parseFloat(data[0].lat);
    const lon = parseFloat(data[0].lon);
    markerInstance.setLatLng([lat, lon]);
    mapInstance.setView([lat, lon], 14);
    latInput.value = lat.toFixed(6);
    lonInput.value = lon.toFixed(6);
    syncDateTimeToExif();
  } catch (err) {
    alert("Netzwerkfehler bei der Ortssuche: " + err);
  }
}

function navigate(subdir) {
  window.location.href = '/?subdir=' + encodeURIComponent(subdir);
}

function navigateSelected(subdir, file) {
  const url = '/?subdir=' + encodeURIComponent(subdir || '') + '&selected=' + encodeURIComponent(file);
  window.location.href = url;
}

window.addEventListener("DOMContentLoaded", () => {
  initDateBinding();
  initMap();
  initSelectedCount();
  scrollToSelected();
});
