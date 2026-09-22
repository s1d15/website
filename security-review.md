# Security Review

## Bandit

Bandit is executed automatically in Jenkins against the application source code.

Result:
- High: 0
- Medium: 0
- Low: 85

Policy:
- Medium and High findings fail the pipeline.
- Low findings are reviewed and documented.

Previous Medium findings related to HTTP requests without timeout values were
remediated by adding explicit request timeouts.

Status: PASS.


## Trivy

Trivy scans the immutable Docker image produced by the Build stage.

The scan identified HIGH and CRITICAL vulnerabilities in both Python
dependencies and operating-system packages.

### Category 1 - Direct application dependencies

Django 4.2.14 contained CRITICAL/HIGH security findings.

Action:
Django was upgraded to 4.2.30 within the existing 4.2 release line.

Validation:
The application was rebuilt and the automated test suite, code-quality checks,
and security scans were rerun.

Status: Remediated.


### Category 2 - Transitive Python dependencies

Examples:
- NLTK
- cryptography
- urllib3

These packages are installed indirectly through existing application
dependencies.

Action:
Findings are documented and monitored. Upgrading them independently could
introduce dependency compatibility issues, so remediation will be performed
through controlled parent-dependency upgrades.

Status: Accepted / monitored technical debt.


### Category 3 - Base image and OS packages

Trivy identified vulnerabilities inherited from the Debian/Python base image
and installed system packages.

Action:
These are documented as base-image technical debt. The mitigation strategy is
to periodically rebuild against updated base images and reduce unnecessary
runtime packages.

Status: Mitigated / scheduled for future remediation.


## Pipeline Security Policy

Bandit:
- Medium/High findings block deployment.

Trivy:
- HIGH/CRITICAL findings are automatically detected and archived.
- Findings are reviewed and classified rather than silently ignored.
- Directly actionable vulnerabilities are remediated.
- Remaining risks are explicitly documented.