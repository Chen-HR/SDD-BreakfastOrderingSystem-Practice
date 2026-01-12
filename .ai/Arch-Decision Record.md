# Architectural Decision Records (ADR) for Breakfast Ordering System

## 1. ADR-001: API Documentation with Flask-RESTx

**Date**: 2026-01-13

**Title**: Integration of Flask-RESTx for OpenAPI (Swagger) API Documentation

**Status**: Accepted

**Context**:
The project requires comprehensive API documentation following the OpenAPI 3.0 specification, accessible via `/api/docs`. The backend is built with Flask. Initial API endpoints were defined using standard Flask Blueprints.

**Decision**:
To meet the requirement for OpenAPI documentation and provide a structured way to build RESTful APIs in Flask, `Flask-RESTx` was chosen and integrated into the project.

**Consequences**:
*   **Positive**:
    *   Automatic generation of interactive OpenAPI (Swagger UI) documentation, making API usage clear for frontend developers and external integrators.
    *   Enforces a structured approach to API development with `Namespaces`, `Resources`, and `fields` for request/response serialization/deserialization.
    *   Simplified input validation through `api.expect()` and output formatting through `api.marshal_with()`.
    *   Improved API discoverability and testability directly from the documentation UI.
    *   Adherence to `Regulations.md` regarding API documentation.
*   **Negative**:
    *   Required refactoring of existing Flask Blueprint-based routes (`admin_bp`, `customer_bp`, `auth_bp`) into `flask-restx.Namespace` and `Resource` classes. This was a significant code change.
    *   Increased dependency on a specific Flask extension for API definition.
*   **Alternatives Considered**:
    *   **Flasgger**: While simpler to integrate with existing Flask blueprints, it relies heavily on docstrings for OpenAPI specification, which can be less structured and error-prone compared to `Flask-RESTx`'s explicit model definitions. It also has less robust features for API building itself.
    *   **Manual OpenAPI Specification**: Writing a `swagger.json` or `swagger.yaml` file manually would provide full control but is time-consuming, difficult to maintain, and prone to desynchronization with the actual code.
    *   **Other Flask REST extensions**: `Flask-RESTful` (predecessor to Flask-RESTx) was considered but `Flask-RESTx` offers better OpenAPI 3.0 support and continued development.

**References**:
*   `plan.md` - Mentions API documentation as a requirement.
*   `regulations.md` - Specifies OpenAPI 3.0 and `/api/docs` path.
*   `src/app.py` - Flask app initialization with `Api` instance.
*   `src/api/routes.py` - Refactored `admin_ns`, `customer_ns`.
*   `src/api/auth_routes.py` - Refactored `auth_ns`.
