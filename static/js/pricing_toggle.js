const ShareplatePricing = {
  toggle(radioEl) {
    const saleFields = document.getElementById("sale-fields");
    if (!saleFields) return;
    if (radioEl.value === "sale") {
      saleFields.classList.remove("hidden");
      document.getElementById("sale_price").required = true;
    } else {
      saleFields.classList.add("hidden");
      document.getElementById("sale_price").required = false;
    }
  },
};
