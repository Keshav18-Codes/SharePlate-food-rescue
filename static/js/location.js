const ShareplateLocation = {
  fill(latFieldId, lngFieldId) {
    const hint = document.getElementById("location-hint");
    if (!navigator.geolocation) {
      if (hint) hint.textContent = "Geolocation isn't supported by this browser.";
      return;
    }
    if (hint) hint.textContent = "Locating...";
    navigator.geolocation.getCurrentPosition(
      (position) => {
        document.getElementById(latFieldId).value = position.coords.latitude;
        document.getElementById(lngFieldId).value = position.coords.longitude;
        if (hint) hint.textContent = "Location captured.";
      },
      () => {
        if (hint) hint.textContent = "Couldn't get your location. You can leave this blank.";
      }
    );
  },
};
