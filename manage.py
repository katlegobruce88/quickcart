#!/usr/bin/env python
"""
Usage: manage.py <system> [options] <django-command> ...

Run Django management commands for different Quickcart subsystems.

Supported systems:
- marketplace: Customer-facing marketplace frontend
- sellerportal: Seller dashboard and product management
- gigportal: Gig workers and job postings

Supports environment selection via --settings or defaults.
All other args passed to Django.
"""

import os
import sys
from argparse import ArgumentParser
from django.core.management import execute_from_command_line


def parse_args():
    parser = ArgumentParser(
        description="Quickcart Multi-System Management CLI"
    )

    subparsers = parser.add_subparsers(
        dest="system",
        title="Available systems",
        description="Choose the Quickcart system to manage"
    )

    # Marketplace (buyer facing)
    marketplace = subparsers.add_parser(
        "marketplace",
        help="Customer-facing marketplace frontend",
        usage="manage.py marketplace [options] <django-command>"
    )
    marketplace.add_argument(
        "--settings",
        help="Settings module under quickcart.marketplace.envs (default: 'dev')."
    )
    marketplace.set_defaults(
        settings_base="quickcart.marketplace.envs",
        default_settings="quickcart.marketplace.envs.dev",
        help_string=marketplace.format_help()
    )

    # Seller portal (seller facing)
    sellerportal = subparsers.add_parser(
        "sellerportal",
        help="Seller dashboard and product management",
        usage="manage.py sellerportal [options] <django-command>"
    )
    sellerportal.add_argument(
        "--settings",
        help="Settings module under quickcart.sellerportal.envs (default: 'dev')."
    )
    sellerportal.set_defaults(
        settings_base="quickcart.sellerportal.envs",
        default_settings="quickcart.sellerportal.envs.dev",
        help_string=sellerportal.format_help()
    )

    # Gig portal (gig workers and jobs)
    gigportal = subparsers.add_parser(
        "gigportal",
        help="Gig workers and job postings management",
        usage="manage.py gigportal [options] <django-command>"
    )
    gigportal.add_argument(
        "--settings",
        help="Settings module under quickcart.gigportal.envs (default: 'dev')."
    )
    gigportal.set_defaults(
        settings_base="quickcart.gigportal.envs",
        default_settings="quickcart.gigportal.envs.dev",
        help_string=gigportal.format_help()
    )

    parsed_args, remaining_args = parser.parse_known_args()

    if (not parsed_args.system or
        "--help" in remaining_args or
        "-h" in remaining_args):
        parser.print_help()
        if hasattr(parsed_args, "help_string"):
            print(f"\nOptions for '{parsed_args.system}':\n")
            print(parsed_args.help_string)
        else:
            print("\n[ERROR] Please specify a valid system: marketplace, sellerportal, or gigportal.")
        sys.exit(0)

    return parsed_args, remaining_args


def main():
    sys.path.insert(0, os.getcwd())

    args, django_args = parse_args()

    settings_module = args.settings or os.environ.get("QUICKCART_SETTINGS")
    if settings_module:
        os.environ["DJANGO_SETTINGS_MODULE"] = f"{args.settings_base}.{settings_module}"
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", args.default_settings)

    os.environ.setdefault("SERVICE_VARIANT", args.system)

    execute_from_command_line([sys.argv[0]] + django_args)


if __name__ == "__main__":
    main()
