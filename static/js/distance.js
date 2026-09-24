(function () {
  function haversineKm(lat1, lng1, lat2, lng2) {
    const R = 6371;
    const dLat = ((lat2 - lat1) * Math.PI) / 180;
    const dLng = ((lng2 - lng1) * Math.PI) / 180;
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos((lat1 * Math.PI) / 180) *
        Math.cos((lat2 * Math.PI) / 180) *
        Math.sin(dLng / 2) *
        Math.sin(dLng / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }

  const ngoLat = window.SHAREPLATE_NGO_LAT;
  const ngoLng = window.SHAREPLATE_NGO_LNG;

  document.querySelectorAll(".listing-card").forEach((card) => {
    const label = card.querySelector(".distance-label");
    if (!label) return;

    const lat = parseFloat(card.dataset.lat);
    const lng = parseFloat(card.dataset.lng);

    if (!ngoLat || !ngoLng || isNaN(lat) || isNaN(lng)) {
      label.textContent = "Distance: unknown (location not set)";
      return;
    }

    const km = haversineKm(parseFloat(ngoLat), parseFloat(ngoLng), lat, lng);
    label.textContent = `Distance: ${km.toFixed(1)} km`;

    card.dataset.distance = km;
  });

  // Sort cards by distance when possible
  const grid = document.getElementById("listing-grid");
  if (grid && ngoLat && ngoLng) {
    const cards = Array.from(grid.children);
    const sortable = cards.every((c) => c.dataset.distance !== undefined);
    if (sortable) {
      cards.sort((a, b) => parseFloat(a.dataset.distance) - parseFloat(b.dataset.distance));
      cards.forEach((c) => grid.appendChild(c));
    }
  }
})();
