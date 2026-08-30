import {
  buildCardViewModel,
  parseNextRainEntityId,
  relatedEntityIds,
  renderTimelineSvg,
} from "./rainstart-card-model.mjs";

const CARD_TAG = "meteoswiss-rainstart-card";
const DOCUMENTATION_URL =
  "https://github.com/csenf/ha-meteoswiss-rainstart";

const CARD_STYLES = `
  :host {
    display: block;
    height: 100%;
  }
  ha-card {
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    box-sizing: border-box;
    cursor: pointer;
    outline: none;
    padding: var(--ha-space-4, 16px) 0;
  }
  .content {
    display: flex;
    flex-wrap: nowrap;
    justify-content: space-between;
    align-items: center;
    padding: 0 var(--ha-space-4, 16px);
  }
  .content + .forecast,
  .content + .alert,
  .content + .stats {
    padding-top: var(--ha-space-4, 16px);
  }
  .icon-image {
    display: flex;
    align-items: center;
    min-width: 64px;
    margin-inline-end: var(--ha-space-4, 16px);
    margin-inline-start: initial;
  }
  .icon-image > * {
    flex: 0 0 64px;
    height: 64px;
  }
  .weather-icon {
    --mdc-icon-size: 64px;
    color: var(--state-icon-color);
  }
  .tone-wet .weather-icon { color: var(--info-color); }
  .tone-soon .weather-icon { color: var(--warning-color); }
  .tone-dry .weather-icon { color: var(--state-icon-color); }
  .tone-muted .weather-icon { color: var(--secondary-text-color); }
  .tone-error .weather-icon { color: var(--error-color); }
  .info {
    display: flex;
    justify-content: space-between;
    flex-grow: 1;
    overflow: hidden;
  }
  .name-state {
    overflow: hidden;
    padding-inline-end: var(--ha-space-3, 12px);
    padding-inline-start: initial;
    width: 100%;
  }
  .name,
  .attribute {
    color: var(--secondary-text-color);
    font-size: var(--ha-font-size-m);
    line-height: var(--ha-line-height-condensed);
  }
  .state,
  .temp-attribute .temp {
    font-size: var(--ha-font-size-3xl);
    line-height: var(--ha-line-height-condensed);
  }
  .name,
  .state {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .temp-attribute {
    text-align: var(--float-end, end);
  }
  .temp-attribute .temp {
    direction: ltr;
    white-space: nowrap;
  }
  .temp .unit {
    color: var(--secondary-text-color);
    font-size: var(--ha-font-size-l);
    margin-inline-start: 2px;
  }
  .attribute {
    white-space: nowrap;
    direction: ltr;
  }
  .alert {
    padding: 0 var(--ha-space-4, 16px);
  }
  .forecast {
    padding: 0 var(--ha-space-4, 16px);
  }
  svg.timeline {
    display: block;
    height: 72px;
    width: 100%;
  }
  .timeline-label,
  .timeline-empty {
    fill: var(--secondary-text-color);
    font-size: var(--ha-font-size-s, 12px);
  }
  .stats {
    display: flex;
    justify-content: space-around;
    padding: var(--ha-space-3, 12px) var(--ha-space-4, 16px) 0;
    gap: var(--ha-space-2, 8px);
  }
  .stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 0;
    gap: var(--ha-space-1, 4px);
  }
  .stat-value {
    font-size: var(--ha-font-size-m);
    line-height: var(--ha-line-height-condensed);
    white-space: nowrap;
  }
  .stat-label {
    color: var(--secondary-text-color);
    font-size: var(--ha-font-size-s);
    line-height: 1;
  }
  .error {
    color: var(--error-color);
    font-size: var(--ha-font-size-l);
    padding: var(--ha-space-4, 16px);
    text-align: center;
  }

  :host([data-width="narrow"]) .icon-image {
    min-width: 52px;
  }
  :host([data-width="narrow"]) .icon-image > *,
  :host([data-width="narrow"]) .icon-image .weather-icon {
    flex-basis: 52px;
    height: 52px;
    --mdc-icon-size: 52px;
  }
  :host([data-width="narrow"]) .state,
  :host([data-width="narrow"]) .temp-attribute .temp {
    font-size: var(--ha-font-size-xl);
  }

  :host([data-width="very-narrow"]) .name,
  :host([data-width="very-narrow"]) .attribute {
    display: none;
  }
  :host([data-width="very-narrow"]) .info {
    flex-direction: column;
    align-items: flex-start;
  }
  :host([data-width="very-narrow"]) .name-state {
    padding-inline-end: 0;
  }

  :host([data-width="very-very-narrow"]) .content {
    flex-direction: column;
    flex-wrap: wrap;
    justify-content: center;
  }
  :host([data-width="very-very-narrow"]) .info {
    align-items: center;
    padding-top: var(--ha-space-1, 4px);
  }
  :host([data-width="very-very-narrow"]) .icon-image {
    min-width: 48px;
    margin-inline-end: 0;
  }
  :host([data-width="very-very-narrow"]) .icon-image > * {
    flex: 0 0 48px;
    height: 48px;
    --mdc-icon-size: 48px;
  }
  :host([data-width="very-very-narrow"]) .content + .forecast,
  :host([data-width="very-very-narrow"]) .content + .alert,
  :host([data-width="very-very-narrow"]) .content + .stats {
    padding-top: var(--ha-space-2, 8px);
  }

  :host([data-height="short"]) .state,
  :host([data-height="short"]) .temp-attribute .temp {
    font-size: var(--ha-font-size-xl);
  }
  :host([data-height="short"]) .content + .forecast,
  :host([data-height="short"]) .content + .alert,
  :host([data-height="short"]) .content + .stats {
    padding-top: var(--ha-space-3, 12px);
  }
  :host([data-height="short"]) svg.timeline {
    height: 56px;
  }
`;

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function isNextRainEntity(entityId) {
  try {
    parseNextRainEntityId(entityId);
    return true;
  } catch {
    return false;
  }
}

function firstNextRainEntity(hass) {
  if (!hass?.states) {
    return "";
  }
  return Object.keys(hass.states).find((entityId) => isNextRainEntity(entityId)) ?? "";
}

function stateSignature(hass, entityIds) {
  return Object.values(entityIds)
    .map((entityId) => {
      const item = hass.states?.[entityId];
      return item ? `${entityId}:${item.state}:${item.last_updated}` : `${entityId}:`;
    })
    .join("|");
}

class MeteoSwissRainStartCard extends HTMLElement {
  static getStubConfig(hass) {
    return {
      entity:
        firstNextRainEntity(hass) ||
        "sensor.meteoswiss_rainstart_example_next_rain_minutes",
    };
  }

  static getConfigForm() {
    return {
      schema: [
        {
          name: "entity",
          required: true,
          selector: {
            entity: {
              filter: {
                domain: "sensor",
                integration: "meteoswiss_rainstart",
              },
            },
          },
        },
      ],
      computeHelper: (schema) => {
        if (schema.name === "entity") {
          return "Next rain minutes sensor for one location";
        }
        return undefined;
      },
    };
  }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = undefined;
    this._hass = undefined;
    this._signature = undefined;
  }

  setConfig(config) {
    if (!config?.entity) {
      throw new Error("Set the next rain minutes entity");
    }
    this._config = config;
    this._signature = undefined;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 4;
  }

  getGridOptions() {
    return {
      columns: 12,
      rows: 4,
      min_columns: 6,
      min_rows: 3,
    };
  }

  connectedCallback() {
    if (this.shadowRoot.getElementById("root")) {
      return;
    }
    this.shadowRoot.innerHTML = `<style>${CARD_STYLES}</style><div id="root"></div>`;
    this.shadowRoot.addEventListener("click", this._onClick);
    this.shadowRoot.addEventListener("keydown", this._onKeydown);
    this._resizeObserver = new ResizeObserver((entries) => {
      const rect = entries[0]?.contentRect;
      if (!rect) {
        return;
      }
      const width =
        rect.width < 180
          ? "very-very-narrow"
          : rect.width < 300
            ? "very-narrow"
            : rect.width < 375
              ? "narrow"
              : "regular";
      const height = rect.height < 200 ? "short" : "tall";
      if (this.dataset.width !== width) {
        this.dataset.width = width;
      }
      if (this.dataset.height !== height) {
        this.dataset.height = height;
      }
    });
    this._resizeObserver.observe(this);
    this._render();
  }

  disconnectedCallback() {
    this._resizeObserver?.disconnect();
    this._resizeObserver = undefined;
  }

  _onClick = () => {
    this._openMoreInfo();
  };

  _onKeydown = (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      this._openMoreInfo();
    }
  };

  _openMoreInfo() {
    if (!this._config?.entity) {
      return;
    }
    this.dispatchEvent(
      new CustomEvent("hass-more-info", {
        bubbles: true,
        composed: true,
        detail: { entityId: this._config.entity },
      }),
    );
  }

  _render() {
    const root = this.shadowRoot?.getElementById("root");
    if (!root || !this._config?.entity || !this._hass) {
      return;
    }

    let entityIds;
    try {
      entityIds = relatedEntityIds(this._config.entity);
    } catch (error) {
      root.innerHTML = `<ha-card class="rainstart-card"><div class="error">${escapeHtml(error.message)}</div></ha-card>`;
      return;
    }

    const signature = stateSignature(this._hass, entityIds);
    if (signature === this._signature && root.childElementCount) {
      return;
    }
    this._signature = signature;

    const model = buildCardViewModel({
      entityIds,
      states: this._hass.states,
    });

    const unit = model.unit
      ? `<span class="unit">${escapeHtml(model.unit)}</span>`
      : "";
    const attribute = model.attribute
      ? `<div class="attribute">${escapeHtml(model.attribute)}</div>`
      : "";
    const alert = model.problem
      ? `<div class="alert"><ha-alert alert-type="error">${escapeHtml(model.problem.detail)}</ha-alert></div>`
      : "";
    const forecast = model.timeline.length
      ? `<div class="forecast">${renderTimelineSvg(model.timeline, model.maxRate)}</div>`
      : "";
    const stats = model.stats.length
      ? `<div class="stats">${model.stats
          .map(
            (item) =>
              `<div class="stat"><span class="stat-value">${escapeHtml(item.value)}</span>` +
              `<span class="stat-label">${escapeHtml(item.label)}</span></div>`,
          )
          .join("")}</div>`
      : "";

    root.innerHTML = `
      <ha-card class="rainstart-card status-${escapeHtml(model.status)} tone-${escapeHtml(model.heroTone)}"
        tabindex="0" aria-label="${escapeHtml(model.hero)}">
        <div class="content">
          <div class="icon-image">
            <ha-icon class="weather-icon" icon="${escapeHtml(model.icon)}"></ha-icon>
          </div>
          <div class="info">
            <div class="name-state">
              <div class="name">${escapeHtml(model.locationName)}</div>
              <div class="state">${escapeHtml(model.stateLabel)}</div>
            </div>
            <div class="temp-attribute">
              <div class="temp">${escapeHtml(model.value)}${unit}</div>
              ${attribute}
            </div>
          </div>
        </div>
        ${alert}
        ${forecast}
        ${stats}
      </ha-card>
    `;
  }
}

customElements.define(CARD_TAG, MeteoSwissRainStartCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: CARD_TAG,
  name: "MeteoSwiss Rain-Start",
  description: "Rain countdown and nowcast timeline for one location",
  preview: true,
  documentationURL: DOCUMENTATION_URL,
  getEntitySuggestion: (_hass, entityId) => {
    if (!isNextRainEntity(entityId)) {
      return null;
    }
    return {
      config: { type: `custom:${CARD_TAG}`, entity: entityId },
    };
  },
});
