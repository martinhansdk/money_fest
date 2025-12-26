"""
Command-line interface for Money Fest administration
"""

import argparse
import getpass
import sys
import os
from app.config import settings
from app.database import get_db, init_db
from app.services.user import create_user
from app.services.category import import_categories_from_file
from app.services.backup import backup_database


def cmd_create_user(args):
    """Create a new user with password from argument, environment, or stdin"""
    username = args.username

    # Get password from argument, environment variable, or stdin
    if args.password:
        password = args.password
        print(f"Warning: Passing passwords via command line is insecure", file=sys.stderr)
    elif os.environ.get('USER_PASSWORD'):
        password = os.environ.get('USER_PASSWORD')
    elif not sys.stdin.isatty():
        # Non-interactive mode (like docker exec without -it)
        print(f"Error: No password provided. Use --password, USER_PASSWORD env var, or stdin", file=sys.stderr)
        print(f"Example: echo 'mypassword' | docker exec -i categorizer python -m app.cli create-user {username}", file=sys.stderr)
        print(f"Or: docker exec categorizer python -m app.cli create-user {username} --password mypassword", file=sys.stderr)
        print(f"Or: docker exec -it categorizer python -m app.cli create-user {username}", file=sys.stderr)
        sys.exit(1)
    else:
        # Interactive mode
        try:
            password = getpass.getpass(f"Enter password for '{username}': ")
            password_confirm = getpass.getpass("Confirm password: ")

            # Check passwords match
            if password != password_confirm:
                print("Error: Passwords do not match", file=sys.stderr)
                sys.exit(1)
        except (EOFError, KeyboardInterrupt):
            print("\nError: Password input failed. Use -it flag with docker exec or --password argument", file=sys.stderr)
            sys.exit(1)

    # Create user
    try:
        # Initialize database if needed
        init_db()

        with get_db() as db:
            user_id = create_user(db, username, password)
        print(f"✓ User '{username}' created successfully (ID: {user_id})")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error creating user: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_import_categories(args):
    """Import categories from a file"""
    filepath = args.filepath

    try:
        # Initialize database if needed
        init_db()

        with get_db() as db:
            count = import_categories_from_file(db, filepath)
        print(f"✓ Imported {count} categories from {filepath}")
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error importing categories: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_backup(args):
    """Create a backup of the database"""
    destination = args.destination

    try:
        backup_path = backup_database(settings.DATABASE_PATH, destination)
        print(f"✓ Database backed up to: {backup_path}")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error creating backup: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Money Fest - Command-line administration tools"
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # create-user command
    create_user_parser = subparsers.add_parser(
        'create-user',
        help='Create a new user'
    )
    create_user_parser.add_argument('username', help='Username for the new user')
    create_user_parser.add_argument(
        '--password',
        help='Password (insecure, visible in process list. Use -it or env var instead)'
    )
    create_user_parser.set_defaults(func=cmd_create_user)

    # import-categories command
    import_cat_parser = subparsers.add_parser(
        'import-categories',
        help='Import categories from a file'
    )
    import_cat_parser.add_argument(
        'filepath',
        nargs='?',
        default='/app/categories.txt',
        help='Path to categories file (default: /app/categories.txt)'
    )
    import_cat_parser.set_defaults(func=cmd_import_categories)

    # backup command
    backup_parser = subparsers.add_parser(
        'backup',
        help='Create a database backup'
    )
    backup_parser.add_argument(
        'destination',
        nargs='?',
        default='/app/data/',
        help='Destination directory for backup (default: /app/data/)'
    )
    backup_parser.set_defaults(func=cmd_backup)

    # Parse arguments
    args = parser.parse_args()

    # Show help if no command specified
    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    args.func(args)


if __name__ == '__main__':
    main()
