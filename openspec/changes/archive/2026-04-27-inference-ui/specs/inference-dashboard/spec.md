## ADDED Requirements

### Requirement: Dashboard layout and navigation
The system SHALL provide a single-page web application served locally with a sidebar or tab navigation for switching between "Run", "History", and "Trace Viewer" views.

#### Scenario: User opens the dashboard
- **WHEN** the user navigates to `http://localhost:8501` in a browser
- **THEN** the dashboard loads with the "Run" view active by default

#### Scenario: User navigates between views
- **WHEN** the user clicks a navigation item (Run, History, Trace Viewer)
- **THEN** the corresponding view is displayed without a full page reload

### Requirement: Local dev server
The system SHALL provide a CLI command to start the UI backend that serves both the API and the frontend static assets.

#### Scenario: Starting the UI server
- **WHEN** the user runs the UI start command
- **THEN** a local server starts on port 8501 (configurable via `UI_PORT` env var) serving the dashboard

#### Scenario: Custom port
- **WHEN** the user sets `UI_PORT=9000` and starts the UI server
- **THEN** the server listens on port 9000
