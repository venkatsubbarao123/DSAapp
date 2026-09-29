# DSAapp — Administration & Governance Manual

This document details the architectural principles, access control policies, user administration workflows, problem authoring capabilities, system health monitoring, and security audit log invariants implemented in **Phase 9**.

---

## 1. Administrative RBAC Architecture & Security Gates

DSAapp enforces strict role-based access control (RBAC) at both the HTTP router boundary and database service layer. The platform defines four hierarchical roles:
- **`STUDENT`**: Default learner tier with access to curriculum, problem solving, practice drills, contests, and visualizers.
- **`CONTENT_EDITOR`**: Editorial privilege allowing creation and modification of problems, topics, and lessons.
- **`MODERATOR`**: Community stewardship privilege with access to user discussion and contest leaderboard monitoring.
- **`ADMIN`**: Superuser authority with full platform control, user privilege modification, hidden test case management, diagnostics, and broadcasts.

### Defense-in-Depth Layering
1. **JWT Verification**: Validates cryptographic signature and non-expired token claims.
2. **Database User Active Check**: Ensures the requesting user account is currently marked `is_active = True`. Suspended accounts are immediately locked out.
3. **Role Enforcement Dependency (`require_admin`)**: Fast-fails any non-admin caller with `403 Forbidden` (`{"success": false, "error": {"code": "INSUFFICIENT_PERMISSIONS", "message": "Admin privileges required"}}`).
4. **Self-Demotion & Self-Suspension Prevention Guardrail**:
   - An administrator cannot demote their own account from `ADMIN` to any lower role (`STUDENT`, `CONTENT_EDITOR`, `MODERATOR`).
   - An administrator cannot deactivate or suspend their own account (`is_active = False`).
   - Any attempt triggers an immediate `400 Bad Request` preventing platform administrative lockout.

---

## 2. User Directory & Management Workflows

The user administration console provides pagination, email/name search, role filtering, account status toggling, and deep learner inspection.

### User Mutation Safeguards
- **Mandatory Audit Reasons**: All privilege modifications (role changes, account suspensions) require a non-empty audit rationale supplied by the initiating administrator.
- **Audit Log Emission**: Role modifications generate an immutable `AuditLog` entry detailing:
  - `actor_id`: ID of the administrator executing the mutation.
  - `action`: `UPDATE_ROLE` or `UPDATE_STATUS`.
  - `target_type`: `USER`.
  - `target_id`: ID of the target account.
  - `metadata_json`: Previous role/status, new role/status, and the supplied justification.
  - `ip_address`: Source IP address of the administrative client.

---

## 3. Problem Studio & Hidden Test Case Management

Administrative content management allows configuring algorithmic problem metadata and authoring both public sample cases and hidden verification test cases.

### Hidden Test Case Invariants
- **Public Samples**: Sample test cases (`is_sample = True`, `is_hidden = False`) are exposed to students on the problem detail screen to assist in local debugging and example explanations.
- **Hidden Verification Cases**: Verification test cases (`is_hidden = True`) are **never** transmitted to client endpoints via the student curriculum API (`/api/v1/problems/{id}`).
- **Judge Execution**: During online judge runs, the secure worker mounts both public and hidden test cases in the Docker sandbox, verifying that edge cases and boundary conditions are satisfied without exposing test data to the student.
- **Admin Management API**:
  - `GET /api/v1/admin/problems`: Paginated list of catalog problems with total and hidden test case counts.
  - `GET /api/v1/admin/problems/{id}/test-cases`: Full test case suite including inputs and expected outputs.
  - `POST /api/v1/admin/problems/{id}/test-cases`: Add a new sample or hidden test case.
  - `DELETE /api/v1/admin/problems/{id}/test-cases/{case_id}`: Remove an obsolete test case.

---

## 4. System Diagnostics & Zero Secret Leakage

The administrative diagnostics endpoint (`GET /api/v1/admin/system/diagnostics`) reports operational health metrics across all underlying platform infrastructure components.

### Subsystem Health Probes
| Subsystem | Probe Mechanism | Metrics Reported |
| :--- | :--- | :--- |
| **Database** | Synchronous/asynchronous `SELECT 1` ping | Status (`healthy`/`unhealthy`), round-trip latency (ms) |
| **Redis Cache** | `PING` command execution | Status (`healthy`/`degraded`), latency (ms), fallback mode |
| **Docker Sandbox** | `docker info` / client daemon ping | Engine version (29.8.1), active execution containers |
| **Judge Work Queue** | SQL queue depth & heartbeat check | Unprocessed jobs in queue, active leasing workers |
| **AI Tutoring Engine** | Provider initialization probe | Provider identifier (`google-genai`), model availability |

### Zero Secret Leakage Guarantees
Under no circumstances do diagnostic responses or system health cards include:
- `SECRET_KEY` or JWT signing secrets
- Database connection URLs containing passwords
- Redis authentication credentials
- Cloud API keys (Gemini, AWS, etc.)
- SMTP / email credentials
All diagnostics schemas are explicitly typed and validated with Pydantic to ensure no configuration dictionaries or connection strings escape the security boundary.

---

## 5. Security & Operational Audit Log Architecture

DSAapp maintains an append-only audit trail in the `audit_logs` database table.

### Audit Log Schema
```sql
CREATE TABLE audit_logs (
    id VARCHAR(36) PRIMARY KEY,
    actor_id VARCHAR(36),
    action VARCHAR(64) NOT NULL,
    target_type VARCHAR(64),
    target_id VARCHAR(36),
    ip_address VARCHAR(45),
    request_id VARCHAR(64),
    metadata_json TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_audit_logs_actor_id ON audit_logs(actor_id);
CREATE INDEX ix_audit_logs_action ON audit_logs(action);
CREATE INDEX ix_audit_logs_created_at ON audit_logs(created_at);
```

### Log Querying & Filtering
The audit log endpoint (`GET /api/v1/admin/system/audit`) enables administrators to filter events by action type, target type, actor ID, and pagination offsets, with complete JSON inspection of metadata payloads.
