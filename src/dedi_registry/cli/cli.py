import typer

from dedi_registry.database import get_active_db
import dedi_registry.cli.user as user


def create_cli() -> typer.Typer:
    app = typer.Typer(help='Decentralised Discovery Network Registry CLI')

    app.add_typer(user.app, name='user', help='Administrator user operations')

    return app


def main():
    app = create_cli()

    app()


if __name__ == '__main__':
    main()
