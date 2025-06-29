"""Environment detection for appropriate progress display."""

import os
import sys
from enum import Enum


class EnvironmentType(Enum):
    """Types of execution environments."""

    INTERACTIVE = "interactive"
    CI_CD = "ci_cd"
    TEST = "test"


def detect_environment() -> EnvironmentType:
    """Detect the current execution environment."""
    # Check for test environment
    if "pytest" in sys.modules or "unittest" in sys.modules:
        return EnvironmentType.TEST

    # Check for CI/CD environments
    ci_indicators = [
        "CI",
        "CONTINUOUS_INTEGRATION",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "JENKINS_URL",
        "TRAVIS",
        "CIRCLECI",
        "BUILDKITE",
        "TEAMCITY_VERSION",
    ]

    for indicator in ci_indicators:
        if os.getenv(indicator):
            return EnvironmentType.CI_CD

    # Check if stdout is connected to a terminal
    if not sys.stdout.isatty():
        return EnvironmentType.CI_CD

    return EnvironmentType.INTERACTIVE


def is_interactive() -> bool:
    """Check if we're in an interactive environment."""
    return detect_environment() == EnvironmentType.INTERACTIVE


def is_ci_cd() -> bool:
    """Check if we're in a CI/CD environment."""
    return detect_environment() == EnvironmentType.CI_CD


def is_test() -> bool:
    """Check if we're in a test environment."""
    return detect_environment() == EnvironmentType.TEST
