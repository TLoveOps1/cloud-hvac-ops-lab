# Post-Mortem Template: [Incident Title]

*   **Incident ID**: [Unique ID from Logging Service]
*   **Date of Incident**: YYYY-MM-DD
*   **Time of Incident (UTC)**: HH:MM
*   **Duration**: [e.g., 30 minutes]
*   **Affected Services/Components**: [e.g., `sensor-service`, `monitoring-service`]
*   **Impact**: [Describe the user/system impact, e.g., "Temperature data loss for 30 minutes, no automated cooling for 15 minutes."]
*   **Severity**: [e.g., Critical, Major, Minor]

## Incident Summary

[Provide a brief, high-level overview of the incident. What happened? What was the immediate impact? How was it detected?]

## Timeline (UTC)

| Time | Event | Description | Owner |
| :--- | :---- | :---------- | :---- |
| HH:MM | Detection | `monitoring-service` triggered `High Temperature` alert for `sensor-1`. | `monitoring-service` |
| HH:MM | Alerting | `alerting-service` sent Slack notification to #sre-oncall. | `alerting-service` |
| HH:MM | Automation Attempt | `automation-service` initiated `cooling_logic` for `sensor-1`. | `automation-service` |
| HH:MM | Operator Acknowledges | On-call SRE acknowledged alert. | SRE |
| HH:MM | Manual Intervention | SRE restarted `thermostat-controller` due to persistent high temp. | SRE |
| HH:MM | Resolution | Temperature returned to normal range. | SRE |
| HH:MM | Incident Closed | Incident status updated to `resolved` in `logging-service`. | SRE |

## Root Cause Analysis

[Detail the underlying reasons for the incident. Use the "5 Whys" or similar techniques. Avoid blame and focus on systemic issues.]

*   **Initial Trigger**: [e.g., A sudden spike in external ambient temperature.]
*   **Contributing Factors**: 
    *   [e.g., `thermostat-controller` service was experiencing a memory leak, causing it to become unresponsive to cooling commands.]
    *   [e.g., The automated cooling logic had a bug that prevented it from correctly interacting with the controller API.]
*   **Root Cause**: [e.g., Insufficient load testing on the `thermostat-controller` under sustained high load conditions, leading to an undetected memory leak.]

## Lessons Learned

### What went well?
*   [e.g., Automated detection was fast and accurate.]
*   [e.g., Alerting successfully notified the on-call team.]
*   [e.g., Runbook provided clear initial steps.]

### What could have gone better?
*   [e.g., Automated remediation failed to resolve the issue.]
*   [e.g., Manual intervention took longer than expected due to lack of direct access to controller logs.]
*   [e.g., The dashboard did not clearly show the state of automated remediation attempts.]

## Action Items

| Action Item | Owner | Due Date | Status |
| :---------- | :---- | :------- | :----- |
| Investigate and fix memory leak in `thermostat-controller`. | @dev-team | YYYY-MM-DD | Open |
| Add more robust error handling and logging to `automation-service`'s cooling logic. | @dev-team | YYYY-MM-DD | Open |
| Implement a dedicated API endpoint for `thermostat-controller` restart. | @devops-team | YYYY-MM-DD | Open |
| Enhance System Health Dashboard to display automated remediation status. | @product-owner | YYYY-MM-DD | Open |
| Conduct load testing on all core microservices to identify performance bottlenecks. | @sre-team | YYYY-MM-DD | Open |

## Follow-up

[Any additional follow-up meetings, reviews, or communications required.]
