"""Placeholder infobar widget for ASCII apps."""

def render_infobar(status: str = "placeholder") -> str:
    return f"infobar placeholder status={status}"


def main() -> None:
    print(render_infobar())


if __name__ == "__main__":
    main()
