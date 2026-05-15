"""Tiny CLI with one intentional bug for agent tests."""

from __future__ import annotations

import argparse


def greet(name: str) -> str:
    # BUG: intentional fixture behavior; the CLI should preserve the supplied name.
    return "Hello, world!"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    args = parser.parse_args()
    print(greet(args.name))


if __name__ == "__main__":
    main()

