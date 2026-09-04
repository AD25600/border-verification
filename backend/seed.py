"""
Seeds the database with foundational reference data:
  - the three RBAC roles
  - one demo checkpoint
  - one admin, one supervisor, one officer test account

Run this once after migrations, before starting the frontend.
Uses only synthetic/demo data (per architecture Rule 8).
"""

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.checkpoint import Checkpoint
from app.models.role import Role, RoleName
from app.models.user import User


def run() -> None:
    db = SessionLocal()
    try:
        roles = {}
        for name, description in [
            (RoleName.ADMIN, "Full system access"),
            (RoleName.SUPERVISOR, "Verification oversight and analytics access"),
            (RoleName.OFFICER, "Verification workflow access"),
        ]:
            role = db.query(Role).filter(Role.name == name).first()
            if role is None:
                role = Role(name=name, description=description)
                db.add(role)
                db.flush()
            roles[name] = role

        checkpoint = db.query(Checkpoint).filter(Checkpoint.code == "DEMO-CP-01").first()
        if checkpoint is None:
            checkpoint = Checkpoint(
                name="Demo International Checkpoint",
                code="DEMO-CP-01",
                location="Synthetic Demo Location",
                is_active=True,
            )
            db.add(checkpoint)
            db.flush()

        demo_users = [
            ("admin@demo.example", "Demo Admin", "Admin@12345", RoleName.ADMIN, None),
            ("supervisor@demo.example", "Demo Supervisor", "Supervisor@12345", RoleName.SUPERVISOR, checkpoint.id),
            ("officer@demo.example", "Demo Officer", "Officer@12345", RoleName.OFFICER, checkpoint.id),
        ]

        for email, full_name, password, role_name, checkpoint_id in demo_users:
            existing = db.query(User).filter(User.email == email).first()
            if existing is None:
                db.add(
                    User(
                        email=email,
                        full_name=full_name,
                        hashed_password=hash_password(password),
                        role_id=roles[role_name].id,
                        checkpoint_id=checkpoint_id,
                        is_active=True,
                    )
                )

        db.commit()
        print("Seed complete. Test accounts:")
        for email, _, password, role_name, _ in demo_users:
            print(f"  {role_name:<12} {email}  /  {password}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
