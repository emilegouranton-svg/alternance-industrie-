const DIPLOMA_LABELS = {
  "3": "CAP / Niveau 3",
  "4": "Bac / Niveau 4",
  "5": "Bac+2 (BTS, DUT) / Niveau 5",
  "6": "Bac+3 (Licence) / Niveau 6",
  "7": "Bac+5 (Master, Ingénieur) / Niveau 7",
};

let allOffers = [];

function formatDate(dateStr) {
  if (!dateStr || typeof dateStr !== "string") return null;
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return null;
  return d.toLocaleDateString("fr-FR", { day: "numeric", month: "short", year: "numeric" });
}

function diplomaLabel(code) {
  if (!code) return null;
  return DIPLOMA_LABELS[String(code)] || `Niveau ${code}`;
}

function buildCard(offer) {
  const card = document.createElement("article");
  card.className = "offer-card";

  const title = document.createElement("h2");
  title.textContent = offer.title;
  card.appendChild(title);

  const meta = document.createElement("div");
  meta.className = "offer-meta";

  const sectorBadge = document.createElement("span");
  sectorBadge.className = "offer-badge";
  sectorBadge.textContent = offer.sector_label || "Secteur non précisé";
  meta.appendChild(sectorBadge);

  if (offer.company_name) {
    const company = document.createElement("span");
    company.textContent = offer.company_name;
    meta.appendChild(company);
  }

  if (offer.address) {
    const addr = document.createElement("span");
    addr.textContent = offer.address;
    meta.appendChild(addr);
  }

  const dLabel = diplomaLabel(offer.target_diploma);
  if (dLabel) {
    const dip = document.createElement("span");
    dip.className = "offer-badge";
    dip.textContent = dLabel;
    meta.appendChild(dip);
  }

  const dateLabel = formatDate(offer.created_at);
  if (dateLabel) {
    const date = document.createElement("span");
    date.textContent = `Publiée le ${dateLabel}`;
    meta.appendChild(date);
  }

  card.appendChild(meta);

  if (offer.description) {
    const desc = document.createElement("p");
    desc.className = "offer-description";
    desc.textContent = offer.description;
    card.appendChild(desc);
  }

  const link = document.createElement("a");
  if (offer.apply_url) {
    link.href = offer.apply_url;
    link.target = "_blank";
    link.rel = "noopener";
    link.className = "offer-apply";
    link.textContent = "Voir l'offre";
  } else {
    link.className = "offer-apply disabled";
    link.textContent = "Lien indisponible";
    link.href = "#";
  }
  card.appendChild(link);

  return card;
}

function populateFilters(offers) {
  const sectorSelect = document.getElementById("filter-sector");
  const diplomaSelect = document.getElementById("filter-diploma");

  const sectors = new Map();
  const diplomas = new Set();

  offers.forEach((o) => {
    if (o.sector_id && !sectors.has(o.sector_id)) {
      sectors.set(o.sector_id, o.sector_label || o.sector_id);
    }
    if (o.target_diploma) diplomas.add(String(o.target_diploma));
  });

  [...sectors.entries()]
    .sort((a, b) => a[1].localeCompare(b[1], "fr"))
    .forEach(([id, label]) => {
      const opt = document.createElement("option");
      opt.value = id;
      opt.textContent = label;
      sectorSelect.appendChild(opt);
    });

  [...diplomas]
    .sort()
    .forEach((code) => {
      const opt = document.createElement("option");
      opt.value = code;
      opt.textContent = diplomaLabel(code);
      diplomaSelect.appendChild(opt);
    });
}

function applyFilters() {
  const sector = document.getElementById("filter-sector").value;
  const diploma = document.getElementById("filter-diploma").value;
  const text = document.getElementById("filter-text").value.trim().toLowerCase();

  const filtered = allOffers.filter((o) => {
    if (sector && o.sector_id !== sector) return false;
    if (diploma && String(o.target_diploma) !== diploma) return false;
    if (text) {
      const haystack = `${o.title || ""} ${o.company_name || ""} ${o.description || ""}`.toLowerCase();
      if (!haystack.includes(text)) return false;
    }
    return true;
  });

  renderOffers(filtered);
}

function renderOffers(offers) {
  const list = document.getElementById("offers-list");
  const emptyState = document.getElementById("empty-state");
  const count = document.getElementById("results-count");

  list.innerHTML = "";

  count.textContent = `${offers.length} offre${offers.length > 1 ? "s" : ""} affichée${offers.length > 1 ? "s" : ""}`;

  if (offers.length === 0) {
    emptyState.hidden = false;
    return;
  }
  emptyState.hidden = true;

  offers.forEach((o) => list.appendChild(buildCard(o)));
}

async function init() {
  try {
    const res = await fetch("data/offres.json", { cache: "no-store" });
    const data = await res.json();
    allOffers = data.offres || [];

    const updatedAtEl = document.getElementById("updated-at");
    if (data.generated_at) {
      const d = new Date(data.generated_at);
      if (!isNaN(d.getTime())) {
        updatedAtEl.textContent = `Dernière mise à jour : ${d.toLocaleString("fr-FR")}`;
      }
    } else {
      updatedAtEl.textContent = "Données de démonstration — en attente de la première synchronisation.";
    }

    populateFilters(allOffers);
    renderOffers(allOffers);

    document.getElementById("filter-sector").addEventListener("change", applyFilters);
    document.getElementById("filter-diploma").addEventListener("change", applyFilters);
    document.getElementById("filter-text").addEventListener("input", applyFilters);
  } catch (err) {
    document.getElementById("results-count").textContent = "Erreur de chargement des offres.";
    console.error(err);
  }
}

init();
