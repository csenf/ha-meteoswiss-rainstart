"""Constants for MeteoSwiss Rain-Start integration."""

DOMAIN = "meteoswiss_rainstart"

DATA_SOURCE_RADAR = "radar_nowcast"

DEFAULT_THRESHOLD_MM = 0.1
MIN_THRESHOLD_MM = 0.0
MAX_THRESHOLD_MM = 100.0
DEFAULT_POLL_INTERVAL = 300
MIN_POLL_INTERVAL = 60
MAX_POLL_INTERVAL = 3600

CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_THRESHOLD = "threshold_mm"
CONF_POLL_INTERVAL = "poll_interval"

RADAR_HOST = "www.meteoschweiz.admin.ch"
RADAR_BASE_URL = f"https://{RADAR_HOST}"
RADAR_PATH_PREFIX = "/product/output/"
MAX_RADAR_JSON_BYTES = 2_000_000

# Switzerland bounding box (WGS84).
CH_LAT_MIN = 45.82
CH_LAT_MAX = 47.81
CH_LON_MIN = 5.96
CH_LON_MAX = 10.49

TIMEZONE = "Europe/Zurich"
EPSG_WGS84 = "EPSG:4326"
EPSG_LV95 = "EPSG:2056"

SENSOR_KEY = "next_rain_minutes"
SENSOR_PRECIPITATION = "precipitation"
SENSOR_NEAREST_RAIN = "nearest_rain"
SENSOR_RAIN_END = "rain_end_minutes"
SENSOR_DATA_AGE = "data_age_minutes"
SENSOR_NEXT_FETCH = "next_fetch"
BINARY_RAINING = "raining"
BINARY_PARSER_PROBLEM = "parser_problem"
IMAGE_INTENSITY = "intensity_graph"

FETCH_STATUS_OK = "ok"
FETCH_STATUS_DOWNLOAD_ERROR = "download_error"
FETCH_STATUS_PARSE_ERROR = "parse_error"
FETCH_STATUS_OUT_OF_BOUNDS = "out_of_bounds"
FETCH_STATUS_ERROR = "error"

PIPELINE_RADAR: dict[str, str | int] = {
    "pipeline": "radar_nowcast",
    "collection": "meteoswiss.precipitation.animation",
    "parameter": "RZC+INCA-rate",
    "step_minutes": 5,
}

CONF_LOCATION = "location"
CONF_LOCATION_NAME = "location_name"
