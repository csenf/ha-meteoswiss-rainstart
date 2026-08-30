import {
  buildCardViewModel,
  relatedEntityIds,
  renderTimelineSvg,
} from "./rainstart-card-model.mjs";

const CARD_TAG = "meteoswiss-rainstart-card";
const CARD_STYLE_ID = "meteoswiss-rainstart-card-style";

function ensureCardStyles() {
  if (document.getElementById(CARD_STYLE_ID)) {
    return;
  }
  const style = document.createElement("style");
  style.id = CARD_STYLE_ID;
  style.textContent = `
    meteoswiss-rainstart-card ha-card.rainstart-card {
      overflow: hidden;
    }
    meteoswiss-rainstart-card .content {
      padding: 16px;
    }
    meteoswiss-rainstart-card .location {
      color: var(--secondary-text-color);
      font-size: 0.9rem;
    }
    meteoswiss-rainstart-card .hero {
      font-size: 1.6rem;
      font-weight: 600;
      line-height: 1.2;
      margin-top: 4px;
    }
    meteoswiss-rainstart-card .tone-soon .hero { color: var(--warning-color, #f59e0b); }
    meteoswiss-rainstart-card .tone-wet .hero { color: var(--info-color, #0284c7); }
    meteoswiss-rainstart-card .tone-dry .hero { color: var(--primary-text-color); }
    meteoswiss-rainstart-card .tone-muted .hero { color: var(--secondary-text-color); }
    meteoswiss-rainstart-card .tone-error .hero { color: var(--error-color, #dc2626); }
    meteoswiss-rainstart-card .subtitle {
      color: var(--secondary-text-color);
      margin-top: 6px;
    }
    meteoswiss-rainstart-card .banner.problem {
      background: rgba(220, 38, 38, 0.12);
      border-radius: 8px;
      color: var(--error-color, #dc2626);
      margin-top: 12px;
      padding: 10px 12px;
    }
    meteoswiss-rainstart-card .timeline-wrap {
      margin-top: 14px;
    }
    meteoswiss-rainstart-card svg.timeline {
      display: block;
      height: 72px;
      width: 100%;
    }
    meteoswiss-rainstart-card .timeline-label,
    meteoswiss-rainstart-card .timeline-empty {
      fill: var(--secondary-text-color);
      font-size: 10px;
    }
    meteoswiss-rainstart-card .footer {
      color: var(--secondary-text-color);
      display: flex;
      flex-wrap: wrap;
      font-size: 0.85rem;
      gap: 8px 12px;
      margin-top: 12px;
    }
    meteoswiss-rainstart-card .error {
      color: var(--error-color, #dc2626);
    }
  `;
  document.head.appendChild(style);
}

class MeteoSwissRainStartCard extends HTMLElement {
  static getStubConfig() {
    return { entity: "sensor.meteoswiss_rainstart_example_next_rain_minutes" };
  }

  static getConfigElement() {
    return document.createElement(`${CARD_TAG}-editor`);
  }

  setConfig(config) {
    if (!config?.entity) {
      throw new Error("Set the next rain minutes entity");
    }
    this._config = config;
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 3;
  }

  _render() {
    if (!this._config?.entity || !this._hass) {
      return;
    }
    ensureCardStyles();

    let entityIds;
    try {
      entityIds = relatedEntityIds(this._config.entity);
    } catch (error) {
      this.innerHTML = `<ha-card class="rainstart-card"><div class="content error">${error.message}</div></ha-card>`;
      return;
    }

    const model = buildCardViewModel({
      entityIds,
      states: this._hass.states,
    });

    const footerParts = [
      model.footer.precipitation ? `Now ${model.footer.precipitation}` : null,
      model.footer.rainEnd,
      model.footer.dataAge,
    ].filter(Boolean);

    this.innerHTML = `
      <ha-card class="rainstart-card">
        <div class="content status-${model.status} tone-${model.heroTone}">
          <div class="header">
            <div class="location">${model.locationName}</div>
            <div class="hero">${model.hero}</div>
            ${model.subtitle ? `<div class="subtitle">${model.subtitle}</div>` : ""}
          </div>
          ${
            model.status === "problem"
              ? `<div class="banner problem">${model.problem.detail}</div>`
              : ""
          }
          ${
            model.timeline.length
              ? `<div class="timeline-wrap">${renderTimelineSvg(model.timeline, model.maxRate)}</div>`
              : ""
          }
          ${
            footerParts.length
              ? `<div class="footer">${footerParts.map((part) => `<span>${part}</span>`).join("")}</div>`
              : ""
          }
        </div>
      </ha-card>
    `;
  }
}

class MeteoSwissRainStartCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = { ...config };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this._hass) {
      return;
    }
    if (!this._config) {
      this._config = MeteoSwissRainStartCard.getStubConfig();
    }
    this.innerHTML = `
      <div class="editor">
        <ha-entity-picker label="Next rain minutes entity"></ha-entity-picker>
      </div>
    `;
    const picker = this.querySelector("ha-entity-picker");
    if (!picker) {
      return;
    }
    picker.hass = this._hass;
    picker.value = this._config.entity ?? "";
    picker.includeDomains = ["sensor"];
    picker.allowCustomEntity = true;
    picker.addEventListener("value-changed", (event) => {
      this._config = { ...this._config, entity: event.detail.value };
      this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config } }));
    });
  }
}

customElements.define(CARD_TAG, MeteoSwissRainStartCard);
customElements.define(`${CARD_TAG}-editor`, MeteoSwissRainStartCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: CARD_TAG,
  name: "MeteoSwiss Rain-Start",
  description: "Rain countdown and nowcast timeline for one location",
  preview: true,
});
