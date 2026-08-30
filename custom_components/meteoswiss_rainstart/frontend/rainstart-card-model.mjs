/** Pure view-model helpers for the MeteoSwiss Rain-Start Lovelace card. */

const DOMAIN = "meteoswiss_rainstart";
const SENSOR_KEY = "next_rain_minutes";

const ROLE_KEYS = {
  next_rain: ["sensor", SENSOR_KEY],
  precipitation: ["sensor", "precipitation"],
  nearest_rain: ["sensor", "nearest_rain"],
  rain_end: ["sensor", "rain_end_minutes"],
  data_age: ["sensor", "data_age_minutes"],
  next_fetch: ["sensor", "next_fetch"],
  raining: ["binary_sensor", "raining"],
  parser_problem: ["binary_sensor", "parser_problem"],
  intensity_graph: ["image", "intensity_graph"],
};

const LEGACY_PRIMARY = `sensor.${DOMAIN}_${SENSOR_KEY}`;

const UMLAUT_MAP = {
  ä: "ae",
  ö: "oe",
  ü: "ue",
  ß: "ss",
  Ä: "Ae",
  Ö: "Oe",
  Ü: "Ue",
};

export function slugifyLocationName(name) {
  let text = String(name ?? "");
  for (const [from, to] of Object.entries(UMLAUT_MAP)) {
    text = text.split(from).join(to);
  }
  text = text
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
  const slug = text.replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");
  return slug || "location";
}

export function parseNextRainEntityId(entityId) {
  if (entityId === LEGACY_PRIMARY) {
    return { slug: null, legacyPrimary: true };
  }
  const prefix = `sensor.${DOMAIN}_`;
  const suffix = `_${SENSOR_KEY}`;
  if (entityId.startsWith(prefix) && entityId.endsWith(suffix)) {
    const slug = entityId.slice(prefix.length, -suffix.length);
    if (slug) {
      return { slug, legacyPrimary: false };
    }
  }
  throw new Error("entity must be a MeteoSwiss Rain-Start next rain sensor");
}

export function relatedEntityIds(primaryEntityId, locationName = null) {
  const parsed = parseNextRainEntityId(primaryEntityId);
  let slug;
  if (parsed.legacyPrimary) {
    if (!locationName) {
      throw new Error("location_name is required for legacy next rain entity");
    }
    slug = slugifyLocationName(locationName);
  } else {
    slug = parsed.slug;
  }
  const related = {};
  for (const [role, [platform, key]] of Object.entries(ROLE_KEYS)) {
    related[role] = `${platform}.${DOMAIN}_${slug}_${key}`;
  }
  related.next_rain = primaryEntityId;
  return related;
}

function readState(states, entityId) {
  if (!entityId || !states) {
    return null;
  }
  return states[entityId] ?? null;
}

function numericState(states, entityId) {
  const item = readState(states, entityId);
  if (!item || item.state === "unavailable" || item.state === "unknown") {
    return null;
  }
  const value = Number(item.state);
  return Number.isFinite(value) ? value : null;
}

function formatMinutes(value) {
  if (value == null) {
    return null;
  }
  if (value === 0) {
    return "0 min";
  }
  return `${Math.round(value)} min`;
}

function formatRate(value) {
  if (value == null) {
    return null;
  }
  return `${value} mm/h`;
}

function formatDistanceKm(value) {
  if (value == null) {
    return null;
  }
  if (value === 0) {
    return "0 km";
  }
  return `${value} km`;
}

function clockLabel(timestamp) {
  const text = String(timestamp ?? "");
  if (text.includes("T") && text.length >= 16) {
    return text.slice(11, 16);
  }
  return text.slice(0, 5);
}

export function buildCardViewModel({ entityIds, states }) {
  const nextRain = readState(states, entityIds.next_rain);
  const parser = readState(states, entityIds.parser_problem);
  const locationName =
    nextRain?.attributes?.location_name ??
    nextRain?.attributes?.friendly_name?.replace(/^Next rain in /i, "") ??
    "Rain-Start";

  if (parser?.state === "on") {
    return {
      status: "problem",
      locationName,
      hero: "Parser problem",
      heroTone: "error",
      subtitle: null,
      footer: { precipitation: null, rainEnd: null, dataAge: null },
      problem: {
        detail: parser.attributes?.parse_detail ?? "broken",
      },
      timeline: [],
      maxRate: 0,
    };
  }

  if (!nextRain || nextRain.state === "unavailable") {
    return {
      status: "unavailable",
      locationName,
      hero: "Unavailable",
      heroTone: "error",
      subtitle: null,
      footer: { precipitation: null, rainEnd: null, dataAge: null },
      problem: null,
      timeline: [],
      maxRate: 0,
    };
  }

  const raining = readState(states, entityIds.raining)?.state === "on";
  const nextRainMinutes = numericState(states, entityIds.next_rain);
  const nearestKm = numericState(states, entityIds.nearest_rain);
  const precipitation = numericState(states, entityIds.precipitation);
  const rainEnd = numericState(states, entityIds.rain_end);
  const dataAge = numericState(states, entityIds.data_age);

  let hero;
  let heroTone;
  let subtitle = null;

  if (raining || nextRainMinutes === 0) {
    hero = "Raining now";
    heroTone = "wet";
  } else if (nextRain?.state === "unknown" || nextRainMinutes == null) {
    hero = "No rain expected";
    heroTone = "muted";
  } else {
    hero = `Rain in ${Math.round(nextRainMinutes)} min`;
    heroTone = nextRainMinutes <= 30 ? "soon" : "dry";
    if (nearestKm != null && nearestKm > 0) {
      subtitle = `Nearest rain ${formatDistanceKm(nearestKm)} away`;
    }
  }

  const precipitationState = readState(states, entityIds.precipitation);
  const series = Array.isArray(precipitationState?.attributes?.intensity_series)
    ? precipitationState.attributes.intensity_series
    : [];
  const timeline = series.map((item) => ({
    rate_lo: Math.max(0, Number(item.rate_lo) || 0),
    kind: item.kind === "measurement" ? "measurement" : "forecast",
    timestamp: item.timestamp ?? "",
  }));
  const maxRate = Math.max(4, ...timeline.map((item) => item.rate_lo), 0);

  return {
    status: "ok",
    locationName,
    hero,
    heroTone,
    subtitle,
    footer: {
      precipitation: formatRate(precipitation),
      rainEnd: rainEnd == null ? null : `Ends in ${formatMinutes(rainEnd)}`,
      dataAge: dataAge == null ? null : `Radar ${formatMinutes(dataAge)} old`,
    },
    problem: null,
    timeline,
    maxRate,
  };
}

export function renderTimelineSvg(series, maxRate = null) {
  if (!series?.length) {
    return (
      '<svg class="timeline" viewBox="0 0 400 72" preserveAspectRatio="none">' +
      '<text x="200" y="40" text-anchor="middle" class="timeline-empty">No timeline</text></svg>'
    );
  }

  const width = 400;
  const height = 72;
  const pad = 4;
  const ymax = maxRate ?? Math.max(4, ...series.map((item) => item.rate_lo));
  const plotW = width - pad * 2;
  const plotH = height - pad * 2;
  const barW = plotW / series.length;
  const bars = series
    .map((item, index) => {
      const rate = item.rate_lo ?? 0;
      const barHeight = ymax <= 0 ? 1 : Math.max(1, (rate / ymax) * plotH);
      const x = pad + index * barW + 1;
      const y = pad + plotH - barHeight;
      const fill =
        rate <= 0 ? "var(--divider-color, #e5e7eb)" : item.kind === "measurement"
          ? "#2563eb"
          : "#38bdf8";
      return `<rect class="${item.kind}" x="${x.toFixed(1)}" y="${y.toFixed(1)}" ` +
        `width="${Math.max(1, barW - 2).toFixed(1)}" height="${barHeight.toFixed(1)}" fill="${fill}" rx="1"/>`;
    })
    .join("");
  const labels = [0, Math.floor(series.length / 2), series.length - 1]
    .filter((value, index, all) => all.indexOf(value) === index)
    .map((index) => {
      const x = pad + index * barW + barW / 2;
      return `<text x="${x.toFixed(1)}" y="${height - 1}" text-anchor="middle" class="timeline-label">${clockLabel(series[index].timestamp)}</text>`;
    })
    .join("");

  return (
    `<svg class="timeline" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">` +
    bars +
    labels +
    "</svg>"
  );
}
