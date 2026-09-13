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

export function parseNextRainEntityId(entityId) {
  const prefix = `sensor.${DOMAIN}_`;
  const suffix = `_${SENSOR_KEY}`;
  if (entityId.startsWith(prefix) && entityId.endsWith(suffix)) {
    const slug = entityId.slice(prefix.length, -suffix.length);
    if (slug) {
      return { slug };
    }
  }
  throw new Error("entity must be a MeteoSwiss Rain-Start next rain sensor");
}

export function relatedEntityIds(primaryEntityId) {
  const { slug } = parseNextRainEntityId(primaryEntityId);
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

/** How old the newest radar measurement frame is (not time until next HA poll). */
function formatRadarDataAge(value) {
  if (value == null) {
    return null;
  }
  const minutes = Math.round(value);
  if (minutes <= 0) {
    return "now";
  }
  if (minutes === 1) {
    return "1 min ago";
  }
  return `${minutes} min ago`;
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

const ICONS = {
  wet: "mdi:weather-pouring",
  soon: "mdi:weather-rainy",
  dry: "mdi:weather-partly-rainy",
  muted: "mdi:weather-partly-cloudy",
  error: "mdi:alert-circle-outline",
};

function emptyLayout(overrides) {
  return {
    subtitle: null,
    attribute: null,
    unit: "",
    value: "—",
    stats: [],
    problem: null,
    timeline: [],
    maxRate: 0,
    ...overrides,
  };
}

export function buildCardViewModel({ entityIds, states }) {
  const nextRain = readState(states, entityIds.next_rain);
  const parser = readState(states, entityIds.parser_problem);
  const locationName =
    nextRain?.attributes?.location_name ??
    nextRain?.attributes?.friendly_name?.replace(/^Next rain in /i, "") ??
    "Rain-Start";

  if (parser?.state === "on") {
    return emptyLayout({
      status: "problem",
      locationName,
      hero: "Parser problem",
      heroTone: "error",
      stateLabel: "Problem",
      icon: ICONS.error,
      problem: {
        detail: parser.attributes?.parse_detail ?? "broken",
      },
    });
  }

  if (!nextRain || nextRain.state === "unavailable") {
    return emptyLayout({
      status: "unavailable",
      locationName,
      hero: "Unavailable",
      heroTone: "error",
      stateLabel: "Unavailable",
      icon: ICONS.error,
    });
  }

  const raining = readState(states, entityIds.raining)?.state === "on";
  const nextRainMinutes = numericState(states, entityIds.next_rain);
  const nearestKm = numericState(states, entityIds.nearest_rain);
  const precipitation = numericState(states, entityIds.precipitation);
  const rainEnd = numericState(states, entityIds.rain_end);
  const dataAge = numericState(states, entityIds.data_age);

  let hero;
  let heroTone;
  let stateLabel;
  let value;
  let unit = "";
  let subtitle = null;
  let attribute = null;

  if (raining || nextRainMinutes === 0) {
    hero = "Raining now";
    heroTone = "wet";
    stateLabel = "Raining";
    value = "Now";
    attribute = formatRate(precipitation);
  } else if (nextRain?.state === "unknown" || nextRainMinutes == null) {
    hero = "No rain expected";
    heroTone = "muted";
    stateLabel = "Clear";
    value = "—";
  } else {
    const minutes = Math.round(nextRainMinutes);
    hero = `Rain in ${minutes} min`;
    heroTone = nextRainMinutes <= 30 ? "soon" : "dry";
    stateLabel = "Rain";
    value = String(minutes);
    unit = "min";
    if (nearestKm != null && nearestKm > 0) {
      attribute = formatDistanceKm(nearestKm);
      subtitle = `Nearest rain ${attribute} away`;
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
  const stats = [
    precipitation != null ? { label: "Now", value: formatRate(precipitation) } : null,
    rainEnd != null ? { label: "Ends", value: formatMinutes(rainEnd) } : null,
    dataAge != null
      ? {
          label: "Radar data",
          value: formatRadarDataAge(dataAge),
          title:
            "How long ago the newest MeteoSwiss radar frame was observed (not when Home Assistant last fetched).",
        }
      : null,
  ].filter(Boolean);

  return {
    status: "ok",
    locationName,
    hero,
    heroTone,
    stateLabel,
    value,
    unit,
    attribute,
    icon: ICONS[heroTone],
    subtitle,
    stats,
    problem: null,
    timeline,
    maxRate,
  };
}

function timelineLabelAnchor(index, count, padX, width, barW) {
  if (index === 0) {
    return { x: padX, anchor: "start" };
  }
  if (index === count - 1) {
    return { x: width - padX, anchor: "end" };
  }
  return { x: padX + index * barW + barW / 2, anchor: "middle" };
}

export function renderTimelineSvg(series, maxRate = null) {
  if (!series?.length) {
    return (
      '<svg class="timeline" viewBox="0 0 400 72" preserveAspectRatio="xMidYMid meet">' +
      '<text x="200" y="40" text-anchor="middle" class="timeline-empty">No timeline</text></svg>'
    );
  }

  const width = 400;
  const height = 72;
  const padX = 22;
  const padTop = 4;
  const labelBand = 16;
  const ymax = maxRate ?? Math.max(4, ...series.map((item) => item.rate_lo));
  const plotW = width - padX * 2;
  const plotH = height - padTop - labelBand;
  const barW = plotW / series.length;
  const plotBottom = padTop + plotH;
  const bars = series
    .map((item, index) => {
      const rate = item.rate_lo ?? 0;
      const barHeight = ymax <= 0 ? 1 : Math.max(1, (rate / ymax) * plotH);
      const x = padX + index * barW + 1;
      const y = plotBottom - barHeight;
      const fill =
        rate <= 0
          ? "var(--disabled-color, var(--divider-color))"
          : item.kind === "measurement"
            ? "var(--blue-color, var(--info-color))"
            : "var(--cyan-color, var(--info-color))";
      return `<rect class="${item.kind}" x="${x.toFixed(1)}" y="${y.toFixed(1)}" ` +
        `width="${Math.max(1, barW - 2).toFixed(1)}" height="${barHeight.toFixed(1)}" fill="${fill}" rx="1"/>`;
    })
    .join("");
  const labelY = height - 3;
  const labels = [0, Math.floor(series.length / 2), series.length - 1]
    .filter((value, index, all) => all.indexOf(value) === index)
    .map((index) => {
      const { x, anchor } = timelineLabelAnchor(
        index,
        series.length,
        padX,
        width,
        barW,
      );
      return `<text x="${x.toFixed(1)}" y="${labelY}" text-anchor="${anchor}" class="timeline-label">${clockLabel(series[index].timestamp)}</text>`;
    })
    .join("");

  return (
    `<svg class="timeline" viewBox="0 0 ${width} ${height}" preserveAspectRatio="xMidYMid meet">` +
    bars +
    labels +
    "</svg>"
  );
}
