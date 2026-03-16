from __future__ import annotations


def test_core_modules_import() -> None:
    import pfbench  # noqa: F401
    import pfbench.cli  # noqa: F401
    import pfbench.evaluation  # noqa: F401
    import pfbench.generation  # noqa: F401
    import pfbench.grading  # noqa: F401
    import pfbench.io  # noqa: F401
    import pfbench.powerflow  # noqa: F401
