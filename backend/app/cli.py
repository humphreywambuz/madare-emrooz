"""Command-line tasks: ``flask create-admin 09121234567 --first-name … --last-name …``."""
import click
from flask import Flask

from app.modules.identity.domain.enums import UserRole


def register_commands(app: Flask) -> None:
    @app.cli.command("create-admin")
    @click.argument("mobile")
    @click.option("--first-name", required=True)
    @click.option("--last-name", required=True)
    def create_admin(mobile: str, first_name: str, last_name: str) -> None:
        """Create the first admin, who can then create the other staff accounts in the panel."""
        from app.wiring import staff_service

        staff = staff_service().create_staff(
            None, mobile=mobile, role=UserRole.ADMIN, first_name=first_name,
            last_name=last_name, is_listed=False,
        )
        click.echo(f"Admin created: {staff.mobile} ({staff.user_id}). Sign in with an SMS code.")
