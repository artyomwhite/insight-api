"""Application-wide constants."""

EVENT_NAME_PATTERN = r"^[a-z][a-z0-9_]{1,99}$"

DEMO_EVENT_TYPES = [
    "user_registered",
    "login",
    "task_created",
    "task_completed",
    "subscription_started",
    "payment_completed",
    "logout",
]

GRANULARITY_OPTIONS = ("hour", "day", "week", "month")
