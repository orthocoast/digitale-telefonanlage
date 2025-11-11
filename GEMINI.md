# GEMINI.md - Project: Digitale Telefonanlage

## Project Overview

This project is a **digital telephone system** designed to capture and manage incoming call data. Its core functionality is to receive call information via a webhook from a service called Placetel, log this data, and prepare it for display and management in a call dashboard.

The system is built with Python and uses a simple Flask server as the webhook endpoint. Incoming call data is stored in a JSONL file (`placetel_logs.jsonl`), which serves as the raw, append-only source of truth, as detailed in the `call-dashboard-bauplan.md`.

**Key Technologies:**
*   **Backend:** Python, Flask
*   **Data Storage:** An immutable `placetel_logs.jsonl` file for raw logs and a **SQLite** database (`database.db`) for operational data like call status.
*   **Webhook Tunneling:** ngrok is used for exposing the local server to the internet.

## Development Workflow & Personas

This project follows a dual-persona development model, supported by a clear separation between development and production scripts.

*   **The IT-Consultant:** This persona focuses on strategy, risk management, and project planning. The consultant ensures that the project goals are aligned with the business needs and that the implementation follows a realistic and secure path.
*   **The Programmieragent (Programming Agent):** This persona focuses on direct implementation, code quality, and technical execution. The agent writes, tests, and refactors code based on the agreed-upon plan.

### Script Separation

To ensure stability, development is done on a dedicated development script, and changes are only promoted to the production script after they are stable and approved.

*   `webhook_server_dev.py`: **Development Script.** All new features, changes, and tests are implemented here first. This is the script to run for day-to-day development.
*   `webhook_server_prod.py`: **Production Script.** This script represents the current stable, "live" version. It should not be modified directly. Changes are copied over from the `dev` script after they have been validated.

## Building and Running (Development)

### 1. Prerequisites

Install the necessary Python packages.

```bash
pip install flask
```

### 2. Running the Development Server

The development server is used to test new features.

```bash
# Start the development server (it will run on http://localhost:54351)
python3 webhook_server_dev.py
```

### 3. Exposing the Server with Ngrok

To make the local server accessible to the Placetel webhook, you need to use ngrok.

1.  Open a **new terminal window**.
2.  Run the following command to create a public tunnel to your local server:

    ```bash
    ngrok http http://localhost:54351
    ```

3.  Ngrok will provide a public URL (e.g., `https://<unique-id>.ngrok-free.dev`). This URL must be configured as the webhook endpoint in your Placetel account.

### 4. Monitoring Logs

New call data will be appended to `placetel_logs.jsonl`. You can monitor this file in real-time:

```bash
tail -f placetel_logs.jsonl
```

## Production & Deployment

The `webhook_server_prod.py` script represents the stable version of the application. The workflow for updating the production script is as follows:

1.  **Develop & Test:** All changes are made and tested in `webhook_server_dev.py`.
2.  **Review & Approve:** The changes are reviewed for stability and correctness.
3.  **Promote:** Once approved, the contents of `webhook_server_dev.py` are copied to `webhook_server_prod.py` to deploy the new version.

```bash
# Example of promoting dev to prod
cp webhook_server_dev.py webhook_server_prod.py
```

## Development Conventions

*   **Data Ingestion:** The webhook server (`_dev` or `_prod`) acts as the single entry point for incoming data. It requires a `Bearer` token for authorization, which is hardcoded in the script as `"inmeinemgarten"`.
*   **Logging:** Raw, unmodified JSON payloads from the webhook are appended to `placetel_logs.jsonl` with a timestamp. This file serves as an immutable log.
*   **Planning & Design:** The `call-dashboard-bauplan.md` is the central document for architecture, data models, and future development milestones. It should be consulted before making significant changes.