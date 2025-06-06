#!/usr/bin/env python
"""
Usage: manage.py <system> [options] <django-command> ...

Run Django management commands for different systcms in the Quickcart platform.

Supported systcms:
- cms: Customer Management System (customer-facing)
- vms: Vendor Management System (merchant-facing)

Supports environment selection via --settings or falls back
to development defaults.
All other arguments are passed through to Django.
"""
# pylint: disable=wrong-import-order, wrong-import-position

# Load environment variables from .env file first, before any other imports

import os
import sys
from argparse import ArgumentParser
from django.core.management import execute_from_command_line


def parse_args():
    """Parse Quickcart-specific CLI arguments
    commands."""
    parser = ArgumentParser(
        description="Quickcart Multi-System Management CLI"
    )

    subparsers = parser.add_subparsers(
        dest="system",
        title="Available systcms",
        description="Choose the system to manage (e.g., cms, pms)"
    )

    # CMS system (customer-facing)
    cms = subparsers.add_parser(
        "cms",
        help="Customer Management System (customer-facing)",
        usage="manage.py cms [options] <django-command>"
    )
    cms.add_argument(
        "--settings",
        help="Settings module under cms.envs (defaults to 'devstack_docker')."
    )
    cms.add_argument(
        "--service-variant",
        choices=["cms", "cms-xml", "cms-preview"],
        default="cms",
        help="Service variant of CMS (used in production)."
    )
    cms.set_defaults(
        settings_base="cms.envs",
        default_settings="cms.envs.devstack_docker",
        help_string=cms.format_help()
    )

    # PMS system (merchant-facing)
    pms = subparsers.add_parser(
        "pms",
        help="Vendor Management System (merchant-facing)",
        usage="manage.py pms [options] <django-command>"
    )
    pms.add_argument(
        "--settings",
        help="Settings module under pms.envs (defaults to 'devstack_docker')."
    )
    pms.set_defaults(
        settings_base="pms.envs",
        default_settings="pms.envs.devstack_docker",
        service_variant="pms",
        help_string=pms.format_help()
    )

    parsed_args, remaining_args = parser.parse_known_args()

    # Display global help if no system is specified or help is requested
    if (not parsed_args.system or
            "--help" in remaining_args or
            "-h" in remaining_args):
        parser.print_help()
        if hasattr(parsed_args, "help_string"):
            print(f"\nOptions for '{parsed_args.system}':\n")
            print(parsed_args.help_string)
        else:
            print("\n[ERROR] Please specify a valid system: cms or pms.")
        sys.exit(0)

    return parsed_args, remaining_args


def main():
    """Main CLI entrypoint for Quickcart manage.py."""
    # Add the project root to Python path
    sys.path.insert(0, os.getcwd())

    args, django_args = parse_args()

    # Determine the Django settings module
    settings_module = args.settings or os.environ.get(
        "QUICKCART_PLATFORM_SETTINGS"
    )
    if settings_module:
        os.environ["DJANGO_SETTINGS_MODULE"] = (
            f"{args.settings_base}.{settings_module}"
        )
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", args.default_settings)

    # Set the service variant environment variable
    os.environ.setdefault(
        "SERVICE_VARIANT",
        getattr(args, "service_variant", args.system)
    )

    # Execute the Django management command
    execute_from_command_line([sys.argv[0]] + django_args)


if __name__ == "__main__":
    main()
