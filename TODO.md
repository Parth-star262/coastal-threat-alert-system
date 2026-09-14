# Coastal Threat Alert System TODO

This checklist tracks the work required to support every Coastal Threat Alert System claim in the resume.

## 1. Secure Configuration

- [x] Move all API keys, database passwords, email credentials, and Twilio credentials to environment variables.
- [x] Remove hardcoded secrets from `app.py` and `weather_api_test.py`.
- [ ] Rotate any credentials that have already been committed or shared.
- [x] Add `.env.example` with placeholder values only.
- [x] Document the required environment variables.

## 2. Real-Time Environmental Data

- [ ] Run weather collection as a reliable background service instead of a manually started infinite-loop script.
- [x] Add request timeouts, retries, rate-limit handling, and structured logging.
- [x] Store latitude and longitude with every location record.
- [x] Apply `migrations/001_add_weather_coordinates.sql` to the PostgreSQL database.
- [x] Add real coastal datasets for tide level and sea-level anomaly.
- [x] Add wave-height collection.
- [x] Add rainfall and visibility where available.
- [x] Add a storm and cyclone data source.
- [x] Validate weather timestamps, units, missing values, and stale readings.
- [x] Validate coastal timestamps, units, missing values, and stale readings.
- [x] Add database tables and indexes for weather and coastal observations.

## 3. Machine-Learning Models

- [ ] Replace synthetic training data with verified historical weather and coastal-disaster data.
- [x] Document the current data source, collection period, features, labels, and limitations.
- [x] Train the alert-level classifier using a reproducible script.
- [x] Evaluate the classifier using accuracy, precision, recall, F1-score, and confusion matrix.
- [ ] Add a storm-surge prediction model.
- [ ] Add a cyclone-risk classification or forecasting model.
- [x] Add abnormal-tide detection or forecasting.
- [x] Save the scaler, feature names, and evaluation metrics together.
- [x] Save an explicit model version manifest with the training data source.
- [x] Connect all production predictions to the `/predict` API.
- [x] Add input validation for predictions.
- [ ] Add calibrated confidence thresholds for predictions.

## 4. Geospatial Risk Analysis

- [x] Add GeoJSON boundaries for coastal regions or risk zones.
- [ ] Add coastal distance, elevation, population, and infrastructure features where available.
- [x] Calculate a location-level coastal threat score.
- [x] Classify locations as LOW, MEDIUM, HIGH, or CRITICAL risk.
- [x] Generate geographic risk zones from current observations and predictions.
- [x] Expose risk-zone data through a backend API.
- [x] Display colored risk polygons on the dashboard map.
- [x] Support location-based filtering and lookup.

## 5. Alert Generation

- [ ] Create one centralized alert service for weather, tide, surge, cyclone, and model alerts.
- [x] Combine weather observations with validated safety thresholds.
- [x] Include severity, confidence, location, timestamp, trigger, and recommended action in each alert.
- [x] Store alerts in the database.
- [x] Prevent duplicate alerts for the same location and event.
- [x] Add alert lifecycle states such as active, acknowledged, resolved, and expired.
- [x] Add alert history and filtering endpoints.

## 6. Emergency Notifications

- [x] Connect email notifications to the centralized alert service.
- [x] Connect Twilio SMS notifications to the centralized alert service.
- [ ] Add configured recipients by location and severity level.
- [x] Add delivery status and failure logging.
- [x] Add bounded notification retry handling.
- [x] Add a notification test mode that cannot contact real recipients accidentally.
- [ ] Verify email and SMS delivery with test credentials.

## 7. Interactive Dashboard

- [x] Connect the dashboard to live API data instead of mock coastal data.
- [x] Display current threat level and model confidence.
- [ ] Display storm-surge and cyclone predictions.
- [x] Display abnormal-tide detection status.
- [x] Display real coastal sensor readings and their last-update times.
- [x] Display calculated high-risk zones on the map.
- [x] Add location-based alert filtering.
- [x] Add active alerts and alert history.
- [x] Expand historical trend charts beyond the current short sample.
- [x] Add loading, empty, error, stale-data, and retry states.
- [x] Replace mock values in `index.html` and the React dashboard.
- [ ] Confirm the dashboard works on desktop and mobile layouts.

## 8. Backend API and Database

- [x] Add endpoints for latest observations, historical observations, predictions, risk zones, alerts, and notifications.
- [x] Validate weather record request payloads.
- [x] Validate all remaining incoming request payloads.
- [x] Return consistent JSON error responses.
- [ ] Use connection-safe database handling and close resources reliably.
- [ ] Add authentication or authorization if notification management is exposed.
- [x] Add indexes for location, severity, and timestamp queries.
- [x] Add API documentation with example requests and responses.
- [x] Add a deployment health endpoint.

## 9. Testing and Validation

- [x] Add unit tests for data parsing and validation.
- [x] Add unit tests for alert severity and risk scoring.
- [ ] Add tests for duplicate-alert prevention.
- [x] Add tests for ML prediction inputs and safe fallback outputs.
- [ ] Add API tests for every backend endpoint.
- [x] Add frontend dashboard rendering tests with Leaflet mocks.
- [ ] Test notification success and failure paths.
- [ ] Test stale, missing, malformed, and unavailable data.
- [ ] Run an end-to-end test from incoming data to dashboard alert and notification.
- [x] Record model metrics and test results in the documentation.

## 10. Deployment and Documentation

- [x] Add a reproducible setup using documented local services.
- [x] Add a production configuration separate from development settings.
- [x] Document how to start the collector, backend, frontend, and notification services.
- [x] Document all data sources and API limitations.
- [x] Document model training, metrics, and known limitations.
- [x] Add architecture and data-flow diagrams.
- [ ] Add screenshots or a short demo showing live data, predictions, map zones, alerts, and notifications.

## Resume Verification Gate

Before claiming the full resume wording, verify that all items below are true in a fresh setup:

- [ ] Real-time environmental data is collected and stored automatically.
- [ ] Storm surges are actually predicted or detected by implemented logic.
- [ ] Cyclone risk is actually predicted or classified.
- [x] Abnormal tidal activity is detected or forecast.
- [ ] Machine-learning results are evaluated on verified data.
- [x] Geospatial analysis produces location-level risk zones.
- [x] High-risk coastal zones appear on the live map.
- [x] Early-warning weather alerts are generated from live observations.
- [x] Location-based alerts work for multiple regions.
- [x] Historical trends use stored real observations.
- [ ] Emergency email/SMS notifications are connected and tested.
- [ ] The complete workflow is documented and reproducible.

Until every relevant gate is checked, describe the project as a weather-based coastal threat alert prototype rather than a complete storm-surge, cyclone, and abnormal-tide prediction system.
