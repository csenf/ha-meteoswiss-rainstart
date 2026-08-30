import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  buildCardViewModel,
  parseNextRainEntityId,
  relatedEntityIds,
  renderTimelineSvg,
} from "../../custom_components/meteoswiss_rainstart/frontend/rainstart-card-model.mjs";

function state(entityId, state, attributes = {}) {
  return { entity_id: entityId, state, attributes };
}

function belpStates(overrides = {}) {
  const ids = relatedEntityIds("sensor.meteoswiss_rainstart_belp_next_rain_minutes");
  const base = {
    [ids.next_rain]: state(ids.next_rain, "23", {
      location_name: "Belp",
      friendly_name: "Next rain in Belp",
    }),
    [ids.raining]: state(ids.raining, "off"),
    [ids.precipitation]: state(ids.precipitation, "0", {
      intensity_series: [
        { timestamp: "2026-08-29T17:25:00+02:00", rate_lo: 0, kind: "measurement" },
        { timestamp: "2026-08-29T17:40:00+02:00", rate_lo: 2, kind: "forecast" },
      ],
    }),
    [ids.nearest_rain]: state(ids.nearest_rain, "4.5"),
    [ids.rain_end]: state(ids.rain_end, "45"),
    [ids.data_age]: state(ids.data_age, "8"),
    [ids.next_fetch]: state(ids.next_fetch, "2026-08-29T17:35:00+02:00"),
    [ids.parser_problem]: state(ids.parser_problem, "off", { parse_detail: "ok" }),
  };
  return { ...base, ...overrides };
}

describe("parseNextRainEntityId", () => {
  it("parses slugged primary entity", () => {
    const parsed = parseNextRainEntityId(
      "sensor.meteoswiss_rainstart_belp_next_rain_minutes",
    );
    assert.equal(parsed.slug, "belp");
    assert.equal(parsed.legacyPrimary, false);
  });

  it("parses legacy primary entity", () => {
    const parsed = parseNextRainEntityId("sensor.meteoswiss_rainstart_next_rain_minutes");
    assert.equal(parsed.slug, null);
    assert.equal(parsed.legacyPrimary, true);
  });
});

describe("relatedEntityIds", () => {
  it("derives sibling entities from slug", () => {
    const ids = relatedEntityIds("sensor.meteoswiss_rainstart_belp_next_rain_minutes");
    assert.equal(ids.raining, "binary_sensor.meteoswiss_rainstart_belp_raining");
  });
});

describe("buildCardViewModel", () => {
  it("shows rain countdown when dry and rain is approaching", () => {
    const ids = relatedEntityIds("sensor.meteoswiss_rainstart_belp_next_rain_minutes");
    const model = buildCardViewModel({
      entityIds: ids,
      states: belpStates(),
    });
    assert.equal(model.status, "ok");
    assert.equal(model.locationName, "Belp");
    assert.equal(model.hero, "Rain in 23 min");
    assert.match(model.subtitle, /4\.5 km/);
    assert.equal(model.timeline.length, 2);
  });

  it("shows raining now when next rain is zero", () => {
    const ids = relatedEntityIds("sensor.meteoswiss_rainstart_belp_next_rain_minutes");
    const states = belpStates({
      [ids.next_rain]: state(ids.next_rain, "0", { location_name: "Belp" }),
      [ids.raining]: state(ids.raining, "on"),
      [ids.nearest_rain]: state(ids.nearest_rain, "0"),
    });
    const model = buildCardViewModel({ entityIds: ids, states });
    assert.equal(model.hero, "Raining now");
    assert.equal(model.heroTone, "wet");
  });

  it("shows no rain expected for unknown horizon", () => {
    const ids = relatedEntityIds("sensor.meteoswiss_rainstart_belp_next_rain_minutes");
    const states = belpStates({
      [ids.next_rain]: state(ids.next_rain, "unknown", { location_name: "Belp" }),
      [ids.nearest_rain]: state(ids.nearest_rain, "unknown"),
    });
    const model = buildCardViewModel({ entityIds: ids, states });
    assert.equal(model.hero, "No rain expected");
    assert.equal(model.heroTone, "muted");
  });

  it("shows parser problem banner and hides rain hero", () => {
    const ids = relatedEntityIds("sensor.meteoswiss_rainstart_belp_next_rain_minutes");
    const states = belpStates({
      [ids.parser_problem]: state(ids.parser_problem, "on", {
        parse_detail: "no_frames",
      }),
      [ids.next_rain]: state(ids.next_rain, "unavailable", { location_name: "Belp" }),
    });
    const model = buildCardViewModel({ entityIds: ids, states });
    assert.equal(model.status, "problem");
    assert.equal(model.problem.detail, "no_frames");
  });

  it("shows unavailable when next rain sensor is unavailable", () => {
    const ids = relatedEntityIds("sensor.meteoswiss_rainstart_belp_next_rain_minutes");
    const states = belpStates({
      [ids.next_rain]: state(ids.next_rain, "unavailable", { location_name: "Belp" }),
    });
    const model = buildCardViewModel({ entityIds: ids, states });
    assert.equal(model.status, "unavailable");
  });
});

describe("renderTimelineSvg", () => {
  it("renders bars for measurement and forecast", () => {
    const svg = renderTimelineSvg([
      { rate_lo: 0, kind: "measurement", timestamp: "2026-08-29T17:25:00+02:00" },
      { rate_lo: 2, kind: "forecast", timestamp: "2026-08-29T17:40:00+02:00" },
    ]);
    assert.match(svg, /^<svg/);
    assert.match(svg, /measurement/);
    assert.match(svg, /forecast/);
  });
});
