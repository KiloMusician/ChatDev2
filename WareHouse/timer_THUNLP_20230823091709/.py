"""Error summary placeholder for timer_THUNLP_20230823091709."""

ERROR_SUMMARY = [
    "timer does not yet support milliseconds",
    "timer does not yet run unattended",
    "timer does not yet expose REST controls",
]


def get_error_summary() -> list[str]:
    """Return the placeholder error summary."""
    return ERROR_SUMMARY


def main() -> None:
    for index, note in enumerate(get_error_summary(), start=1):
        print(f"{index}. {note}")


if __name__ == "__main__":
    main()
