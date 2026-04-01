"""Example: Integrating structured logging with quest_commit_bridge.

This example demonstrates:
1. Rate-limited logging for verbose operations
2. JSON output with OpenTelemetry correlation
3. Operation timing with automatic duration tracking
4. Log rotation for long-running processes

To run this example:
    python examples/observability/structured_logging_integration.py
"""

from src.observability.structured_logging import (
    get_application_logger,
    log_operation,
    rate_limited_log,
    setup_logger,
)
from src.observability.tracing import bind_context, init_tracing, start_span


def example_quest_commit_bridge_with_logging():
    """Enhanced quest_commit_bridge with structured logging."""
    # Initialize tracing (optional but recommended)
    init_tracing(service_name="nusyq-quest-bridge", console_fallback=True)

    # Setup JSON logger with rotation
    logger = get_application_logger(
        "nusyq.quest_commit_bridge",
        log_format="json",
        log_file="logs/quest_bridge.jsonl",
    )

    # Simulate processing multiple commits
    commits = [
        {"sha": "abc123", "message": "feat: Add new feature\n\nQuest: 915cf0d2"},
        {"sha": "def456", "message": "fix: Bug fix\n\nQuest: 1ff3ccbd"},
        {"sha": "ghi789", "message": "chore: Update dependencies"},  # No quest
    ]

    with start_span("batch.process_commits", attrs={"commit_count": len(commits)}):
        with log_operation(logger, "commit_batch_processing", commit_count=len(commits)):
            for commit in commits:
                process_commit_with_logging(logger, commit)


def process_commit_with_logging(logger, commit):
    """Process a single commit with structured logging."""
    commit_sha = commit["sha"]
    message = commit["message"]

    # Bind correlation context (propagates to all logs/spans)
    bind_context(commit_sha=commit_sha)

    with start_span("commit.process", attrs={"commit_sha": commit_sha}):
        with log_operation(logger, "commit_processing", commit=commit_sha):
            # Rate-limited debug log (verbose operation)
            rate_limited_log(
                logger,
                logging.DEBUG,
                f"Parsing commit {commit_sha}",
                rate_limit_key=f"parse:{commit_sha}",
                rate_limit_seconds=300,  # Once per 5 minutes
                extra={"commit": commit_sha, "message_length": len(message)},
            )

            # Extract quest references
            quests = extract_quest_references(message)

            if quests:
                logger.info(
                    f"Found {len(quests)} quest reference(s) in commit",
                    extra={
                        "commit": commit_sha,
                        "quest_count": len(quests),
                        "quest_ids": quests,
                    },
                )

                for quest_id in quests:
                    complete_quest_with_logging(logger, quest_id, commit_sha)
            else:
                # Rate-limit "no quests" logs (common case)
                rate_limited_log(
                    logger,
                    logging.DEBUG,
                    "No quest references found",
                    rate_limit_key=f"no_quests:{commit_sha}",
                    rate_limit_seconds=600,  # Once per 10 minutes
                )


def complete_quest_with_logging(logger, quest_id, commit_sha):
    """Complete a quest with structured logging."""
    with start_span("quest.complete", attrs={"quest_id": quest_id}):
        with log_operation(logger, "quest_completion", quest=quest_id, commit=commit_sha):
            try:
                # Simulate quest completion
                xp_earned = calculate_xp(quest_id)
                patterns = extract_patterns(commit_sha)

                logger.info(
                    "Quest completed successfully",
                    extra={
                        "quest_id": quest_id,
                        "commit": commit_sha,
                        "xp_earned": xp_earned,
                        "pattern_count": len(patterns),
                    },
                )

                # Save receipt
                save_receipt_with_logging(logger, quest_id, commit_sha, xp_earned, patterns)

            except Exception as e:
                # Errors are NEVER rate-limited
                logger.error(
                    f"Quest completion failed: {e}",
                    exc_info=True,
                    extra={"quest_id": quest_id, "commit": commit_sha},
                )
                raise


def save_receipt_with_logging(logger, quest_id, commit_sha, xp, patterns):
    """Save quest receipt with logging."""
    with start_span("receipt.save", attrs={"quest_id": quest_id}):
        # Rate-limit receipt save logs (verbose)
        rate_limited_log(
            logger,
            logging.DEBUG,
            f"Saving receipt for quest {quest_id}",
            rate_limit_key=f"receipt:{quest_id}",
            rate_limit_seconds=300,
        )

        # Simulate saving receipt
        receipt_path = f"docs/tracing/RECEIPTS/quest_completion_{quest_id}.json"

        logger.info(
            "Receipt saved",
            extra={
                "quest_id": quest_id,
                "commit": commit_sha,
                "xp": xp,
                "receipt_path": receipt_path,
            },
        )


def example_error_reporter_with_rate_limiting():
    """Enhanced error reporter with rate-limited file scanning."""
    # Setup logger with quieter default level for scanning
    logger = setup_logger(
        "nusyq.error_reporter",
        level="WARNING",  # Quieter for verbose operations
        log_format="json",
        log_file="logs/error_reporter.jsonl",
    )

    with log_operation(logger, "repository_scan", repo="NuSyQ-Hub"):
        # Simulate scanning many files
        files = [f"src/module_{i}.py" for i in range(100)]

        for file_path in files:
            # Rate-limit per-file scan logs
            rate_limited_log(
                logger,
                logging.DEBUG,
                f"Scanning {file_path}",
                rate_limit_key=f"scan:{file_path}",
                rate_limit_seconds=600,  # Once per 10 minutes per file
                extra={"file": file_path},
            )

            # Simulate linting
            errors = simulate_lint(file_path)

            if errors:
                # Always log errors (no rate limiting)
                logger.warning(
                    f"Found {len(errors)} error(s) in {file_path}",
                    extra={"file": file_path, "error_count": len(errors), "errors": errors},
                )


def example_health_check_with_rate_limiting():
    """Enhanced health check with rate-limited logging."""
    from src.observability.structured_logging import get_health_check_logger

    logger = get_health_check_logger(log_format="json")

    # Simulate health checks every 10 seconds
    for _ in range(100):
        with log_operation(logger, "health_check"):
            status = check_system_health()

            # Log only once per minute (not every 10 seconds)
            rate_limited_log(
                logger,
                logging.INFO,
                f"Health check: {status}",
                rate_limit_key="health:system",
                rate_limit_seconds=60,
                extra={"status": status, "uptime": get_uptime()},
            )

        time.sleep(10)


def example_webhook_with_rate_limiting():
    """Enhanced webhook handler with rate-limited success logs."""
    from src.observability.structured_logging import get_webhook_logger

    logger = get_webhook_logger(log_format="json")

    urls = ["https://api.example.com/webhook1", "https://api.example.com/webhook2"]

    for url in urls:
        with log_operation(logger, "webhook_send", url=url):
            try:
                # Simulate sending webhook
                response = send_webhook(url, {"event": "test"})

                # Rate-limit success logs (once per 5 minutes per URL)
                rate_limited_log(
                    logger,
                    logging.INFO,
                    f"Webhook sent successfully to {url}",
                    rate_limit_key=f"webhook:success:{url}",
                    rate_limit_seconds=300,
                    extra={"url": url, "status_code": response.status_code},
                )

            except Exception as e:
                # Always log errors (no rate limiting)
                logger.error(
                    f"Webhook failed: {url}",
                    exc_info=True,
                    extra={"url": url, "error": str(e)},
                )


# ---- Helper functions (simulated) ----


def extract_quest_references(message):
    """Extract quest IDs from commit message."""
    import re

    pattern = r"Quest:\s*([a-f0-9-]+)"
    matches = re.findall(pattern, message, re.IGNORECASE)
    return matches


def calculate_xp(quest_id):
    """Simulate XP calculation."""
    return 30


def extract_patterns(commit_sha):
    """Simulate pattern extraction."""
    return ["FEATURE", "DESIGN_PATTERN"]


def simulate_lint(file_path):
    """Simulate linting."""
    import random

    if random.random() < 0.1:  # 10% chance of errors
        return ["E501 line too long", "F401 unused import"]
    return []


def check_system_health():
    """Simulate health check."""
    return "healthy"


def get_uptime():
    """Simulate uptime."""
    import time

    return time.time()


def send_webhook(url, payload):
    """Simulate webhook send."""
    import random

    class Response:
        status_code = 200 if random.random() < 0.9 else 500

    return Response()


if __name__ == "__main__":
    import logging
    import time

    # Example 1: Quest commit bridge with full observability
    print("=" * 60)
    print("Example 1: Quest Commit Bridge")
    print("=" * 60)
    example_quest_commit_bridge_with_logging()

    # Example 2: Error reporter with rate-limited scanning
    print("\n" + "=" * 60)
    print("Example 2: Error Reporter with Rate Limiting")
    print("=" * 60)
    example_error_reporter_with_rate_limiting()

    # Example 3: Health check with rate limiting
    print("\n" + "=" * 60)
    print("Example 3: Health Check (run for 30 seconds)")
    print("=" * 60)
    # Uncomment to run (takes 30 seconds):
    # example_health_check_with_rate_limiting()

    # Example 4: Webhook with rate limiting
    print("\n" + "=" * 60)
    print("Example 4: Webhook Handler")
    print("=" * 60)
    example_webhook_with_rate_limiting()
