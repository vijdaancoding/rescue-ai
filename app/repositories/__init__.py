"""
Persistence layer.

Every repository exposes a narrow, entity-specific Protocol plus a concrete
SQLAlchemy implementation. Services depend on the Protocol so they stay
database-agnostic and trivially stubbable in tests.
"""
