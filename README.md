# Cloud HVAC Operations Lab

![Build Status](https://img.shields.io/github/actions/workflow/status/your-org/cloud-hvac-operations-lab/main.yml?branch=main)
![Code Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)
![License](https://img.shields.io/github/license/your-org/cloud-hvac-operations-lab)

## Strategic Overview

### Problem Statement
Modern cloud environments demand sophisticated, distributed systems capable of autonomous operation and rapid incident response. Recreating the robust monitoring, fault detection, and self-stabilization patterns of a Building Automation System (BAS) within a cloud-native, microservices architecture addresses the critical need to demonstrate advanced cloud operations, Site Reliability Engineering (SRE), and automated incident response capabilities. This project provides a tangible platform to simulate and manage complex operational challenges inherent in distributed systems.

### High-Level Overview
The "Cloud HVAC Operations Lab" is a cloud-based simulation of a Building Automation System (BAS), meticulously engineered using a microservices architecture. Each core function – sensor data generation, monitoring, fault detection, alerting, and automated remediation – is encapsulated within its own distinct microservice. This project aims to replicate the critical functions of a physical BAS in a cloud context, emphasizing operational excellence, incident management, and automated system stabilization for distributed systems. The core analogy maps HVAC concepts (Thermostat, Temperature Sensor, BAS Controller, Alarm Panel, Technician, Control Logic) to cloud microservices and equivalents (Application state/service, Metrics, Monitoring + automation logic, Cloud alerts, Operator/runbook, Auto-remediation script).

### MVP Definition
A simulated thermostat system running in the cloud, built with a **microservices architecture**, that:
*   **Sensor Microservice**: Generates and publishes simulated temperature data.
*   **Monitoring Microservice**: Continuously ingests sensor data and monitors safe ranges.
*   **Detection Microservice**: Identifies fault conditions (e.g., temperature excursions, sensor silence, erratic data, unauthorized config changes).
*   **Logging Microservice**: Records all incidents and operational events.
*   **Alerting Microservice**: Triggers notifications to operators upon fault detection.
*   **Automation Microservice**: Executes automated stabilization and remediation actions.
*   Produces incident documentation (runbooks, post-mortems).
*   Demonstrates normal operation (temperature 68-75°F, "healthy" status) and triggers real ops workflows for intentional fault conditions, showcasing the resilience of the microservices ecosystem.

## Getting Started

### Prerequisites
Ensure you have the following installed:
*   Git
*   Docker & Docker Compose
*   Python 3.9+
*   Node.js 18+ & npm (for E2E tests and root-level scripts)

### Local Setup
1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-org/cloud-hvac-operations-lab.git
    cd cloud-hvac-operations-lab
    ```

2.  **Install root dependencies (for E2E tests, Jest config)**:
    ```bash
    npm install
    ```

3.  **Install Python dependencies for each microservice**:
    ```bash
    pip install -r src/sensor-service/requirements.txt
    pip install -r src/monitoring-service/requirements.txt
    pip install -r src/logging-service/requirements.txt
    pip install -r src/alerting-service/requirements.txt
    pip install -r src/automation-service/requirements.txt
    pip install -r src/shared/requirements.txt
    ```

4.  **Run all services with Docker Compose**:
    ```bash
    docker compose up --build
    ```
    This will start all microservices, including the simulated sensor, monitoring, logging, alerting, and automation services.

### Running Tests

*   **Unit Tests (Python)**:
    Navigate to a service directory (e.g., `src/sensor-service`) and run `pytest`:
    ```bash
    cd src/sensor-service
    pytest
    ```
*   **Unit Tests (Shared Python Models)**:
    ```bash
    cd tests/unit/shared
    pytest
    ```
*   **Integration Tests (Python)**:
    ```bash
    cd tests/integration
    pytest
    ```
*   **E2E Tests (JavaScript/Jest - Placeholder)**:
    ```bash
    npm test # Runs Jest for E2E tests (if implemented)
    ```

## Documentation

*   [Architecture Overview](docs/architecture.md)
*   [Contributing Guidelines](CONTRIBUTING.md)
*   [Runbooks](docs/runbooks/)
*   [Post-Mortem Template](docs/postmortems/template.md)

## Security & Incident Response

This project includes a documented real-world security incident and remediation:

- **Postmortem:** [Accidental Secret Exposure (Slack Webhook)](docs/postmortems/secret-exposure.md)

The incident demonstrates secure secret handling, git history rewriting, and DevSecOps best practices.


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
