// Konvertiert datetime-local Wert in EXIF-Format "YYYY:MM:DD HH:MM:SS"
function syncDateTimeToExif() {
  const dtInput = document.getElementById("dt-picker");
  const hidden = document.getElementById("exif-datetime-hidden");
  if (!dtInput || !hidden || !dtInput.value) {
    hidden.value = "";
    return;
  }
  // Browser liefert z.B. 2026-03-30T17:45
  const raw = dtInput.value;
  const [datePart, timePart] = raw.split("T");
  if (!datePart || !timePart) {
    hidden.value = "";
    return;
  }
  const exifDate = datePart.replace(/-/g, ":");
  // Sekunden optional → falls fehlen, auf 00 setzen
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
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap-Mitwirkende",
  }).addTo(map);

  let marker = L.marker([lat, lon], { draggable: true }).addTo(map);

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
}

window.addEventListener("DOMContentLoaded", () => {
  initDateBinding();
  initMap();
});
