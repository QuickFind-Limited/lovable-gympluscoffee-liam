# ARCHITECTURE.md

<!--
IMPORTANT: THOSE ARE RULES FOR AI, DO NOT USE THOSE INTO FILLED TEMPLATE.

- FOCUS: Technology choices, patterns, architectural decisions, include config path
- EXCLUDE: Detailed configurations, deployment specifics, code organization
- EXAMPLES: Next.js for frontend, PostgreSQL database, REST API design, Authentication flow
- NEVER INCLUDE: Why choices were made, deployment details, naming conventions
-->

## Frontend

- **Framework**: [Framework] → @frontend/package.json
- **State Management**: [Solution] - [Brief description]
- **Build Tool**: [Tool] - [Brief description]

## Backend

- **Language/Framework**: [Language/Framework] → @backend/package.json or @composer.json
- **API Style**: [REST/GraphQL/tRPC] - [Brief description]
- **File Structure**: [Monolith/Microservices/Modules] - [Brief description]

## Mobile (if applicable)

- **Framework**: [React Native/Flutter/Native] → @mobile/package.json
- **State Management**: [Solution] - [Brief description]
- **Platform**: [iOS/Android/Both] - [Brief description]

## Database

- **Type**: [PostgreSQL/MySQL/MongoDB/etc]
- **Schema**: @prisma/schema.prisma or @migrations/ or [schema location]
- **Key Entities**: [Entity1, Entity2, Entity3] - [Brief relationships]

## Authentication & Authorization

- **Authentication**: [JWT/OAuth/Session] - [Implementation approach]
- **Authorization**: [RBAC/ACL/etc] - [Implementation approach]
- **Session Management**: [Approach] - [Brief description]

## API & Communication

- **API Endpoints**: @docs/swagger.yml or @routes/ or [API docs location]
- **Real-time**: [WebSockets/SSE/Polling] if applicable
- **External APIs**: [Service1, Service2] - [Brief usage]

## Core Patterns

- [Domain Pattern]: [Where used] - [Technical implementation]
- [Data Pattern]: [Where used] - [Technical implementation]
- [Error Pattern]: [Where used] - [Technical implementation]

## Performance & Monitoring

- **Caching**: [Strategy] - [What is cached and why]
- **Performance Patterns**: [Architectural approaches to performance]
