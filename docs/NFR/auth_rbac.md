# Non-Functional Requirements (NFR): Auth, RBAC, Profiles & Vendors

## 1. Security & Auditability
- **Password Hashing**: Passwords must never be stored in plain text (`bcrypt`).
- **Stateless Authentication**: JWTs with Redis blocklisting for logouts.
- **Audit Trails**: The `vendor_applications` table must strictly enforce data integrity for audits. When an application changes status, the system must definitively record exactly *which* admin (`reviewed_by`) made the decision, and exactly *when* (`reviewed_at`).

## 2. Performance
- **Response Time**: Authentication endpoints (login, register) should respond in under 200ms.
- **Database Access**: Async SQLAlchemy with an async driver (`aiomysql`) must be used.
- **Seeder Efficiency**: The startup seeder script must quickly execute `select` queries to check existence before attempting `inserts` to avoid slowing down the application boot time or throwing integrity errors.

- **Authorization Isolation**: Access control logic must be encapsulated in reusable FastAPI dependencies (`RequireRole`, `require_self_or_admin`) rather than hardcoded into individual endpoint functions.

## 4. Architecture & Maintainability
- **Domain-Driven Design (DDD)**: Strict modularization (`auth`, `users`, `roles`, `permissions`, `vendors`).
- **Data Isolation**: User profiles must be separated into a `user_profiles` table to ensure the primary `users` table remains extremely lightweight, maximizing authentication performance.
- **Separation of Concerns**: Each module must strictly separate models, schemas, crud, services, and routers. Cross-module database updates (e.g. Vendors module assigning a Role) must happen via the Service layer importing the target module's CRUD, not by writing raw foreign SQL statements.

## 4. Scalability
- The architecture allows separating out the Auth module into its own microservice in the future if required.
