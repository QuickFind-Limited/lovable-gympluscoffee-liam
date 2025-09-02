# INFRASTRUCTURE.md

<!--
IMPORTANT: THOSE ARE RULES FOR AI, DO NOT USE THOSE INTO FILLED TEMPLATE.

- FOCUS: Deployment, environments, operational concerns, tools, major versions only
- EXCLUDE: Code organization, architectural decisions, framework choices
- EXAMPLES: Docker setup, CI/CD pipeline, Environment variables, Third-party APIs
- NEVER INCLUDE: Code structure, business vision, UI guidelines
-->

## Environments

- **Development**:

  - URL: [Development URL]
  - Database: [Development database details]
  - Special configurations: [Any dev-specific configs]

- **Staging**:

  - URL: [Staging URL]
  - Database: [Staging database details]
  - Purpose: [What staging is used for]

- **Production**:
  - URL: [Production URL]
  - Database: [Production database details]
  - SLA: [Service level agreements]

## CI/CD Pipeline

- **Build Steps**:

  1. [Step 1]: [Description]
  2. [Step 2]: [Description]
  3. [Step 3]: [Description]

- **Test Automation**:

  - Unit tests: [When and how they run]
  - Integration tests: [When and how they run]
  - E2E tests: [When and how they run]

- **Deployment Triggers**:
  - Manual deployments: [Process]
  - Automated deployments: [Triggers and conditions]

## Monitoring & Logging

- **Monitoring Tools**: [Tools used for monitoring]

  - Application monitoring: [Tool and configuration]
  - Infrastructure monitoring: [Tool and configuration]
  - Performance monitoring: [Tool and configuration]

- **Logging**:

  - Log aggregation: [Tool and configuration]
  - Log levels: [How log levels are used]
  - Log retention: [How long logs are kept]

- **Alert Configuration**:
  - Critical alerts: [What triggers critical alerts]
  - Warning alerts: [What triggers warning alerts]
  - Alert channels: [How alerts are sent]

## Deployment Process

- **Deployment Steps**:

- **Rollback Procedure**:

  1. [Step 1]: [How to identify need for rollback]
  2. [Step 2]: [How to perform rollback]
  3. [Step 3]: [How to verify rollback success]

- **Database Migrations**:
  - Migration strategy: [How database changes are handled]
  - Rollback strategy: [How to rollback database changes]

## External Services

- **Service A**: [Purpose and integration details]

  - Authentication: [How authentication is handled]
  - Rate limits: [Any rate limiting considerations]
  - Fallback strategy: [What happens if service is down]

- **Service B**: [Purpose and integration details]
  - Authentication: [How authentication is handled]
  - Rate limits: [Any rate limiting considerations]
  - Fallback strategy: [What happens if service is down]
