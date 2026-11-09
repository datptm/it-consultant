"""Command-line entry point for repeatable demo and direct requests."""

import argparse
import json

from .data import load_sample_data
from .engine import evaluate


def main() -> None:
    """Parse CLI input, evaluate it and print JSON to standard output."""
    parser = argparse.ArgumentParser(description="Synthetic Promise Engine PoC")
    subcommands = parser.add_subparsers(dest="command", required=True)
    demo = subcommands.add_parser("demo", help="Evaluate all bundled scenario requests")
    direct = subcommands.add_parser("evaluate", help="Evaluate a custom request")
    for command in (demo, direct):
        command.add_argument("--mode", choices=("rules", "ml"), default="rules")
    direct.add_argument("--product-id", required=True)
    direct.add_argument("--quantity", required=True, type=int)
    direct.add_argument("--destination-id", required=True)
    direct.add_argument("--date", required=True, help="Desired delivery date, YYYY-MM-DD")
    direct.add_argument("--at", help="Request timestamp in UTC; defaults to sample reference time")
    arguments = parser.parse_args()
    data = load_sample_data()
    try:
        models = None
        if arguments.mode == "ml":
            from .ml import train_models

            models = train_models(data)
        if arguments.command == "demo":
            output = [evaluate(data, request, arguments.mode, models) for request in data["demo_requests"]]
        else:
            request = {
                "request_id": "CLI-001", "product_id": arguments.product_id,
                "quantity": arguments.quantity, "destination_id": arguments.destination_id,
                "delivery_type": "STORE_PICKUP",
                "requested_at": arguments.at or data["reference_time"],
                "requested_delivery_date": arguments.date,
            }
            output = evaluate(data, request, arguments.mode, models)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
