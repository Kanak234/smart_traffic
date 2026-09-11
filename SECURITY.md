# Security Policy

## Supported Versions

Only the latest release branch of Smart Traffic Simulator receives security updates and vulnerability patches.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Threat Model

Smart Traffic Simulator is an autonomous multi-intersection traffic signal simulation engine. Its architectural boundary and operational threat model assume:
- **Local / Sandbox Execution:** The simulator runs either locally as an interactive Pygame client or headlessly inside containerized CI/CD pipelines (`SDL_VIDEODRIVER=dummy`).
- **No Remote Code Execution:** The simulation engine performs no dynamic `eval`, code compilation at runtime, or untrusted object deserialization (e.g., no `pickle`).
- **Unprivileged Container Boundary:** Official container images run as non-root user `appuser` (UID 10001) with read-only root filesystems and minimal base packages.
- **Resource Constraints:** Simulation time-steps and headless execution are bounded by strict logic tick limits and autoquit flags to prevent denial-of-service in automated testing.

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly:
1. **Do NOT open a public issue.**
2. Report vulnerabilities via GitHub Private Vulnerability Reporting under the **Security** tab of the repository.
3. Include detailed steps to reproduce the vulnerability, along with an impact assessment and proposed remediation if available.

### Response Timelines
- **Initial Acknowledgement:** Within 48 hours of receipt.
- **Severity Assessment & Triaging:** Within 5 business days.
- **Fix & Patch Advisory:** Deployed to supported versions within 14 days of confirmed reproduction.
