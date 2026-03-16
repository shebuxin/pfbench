from __future__ import annotations

import contextlib
import io
import warnings
from typing import Any

from pfbench.powerflow.case_data import available_builtin_cases, load_builtin_case
from pfbench.utils import canonical_json, stable_hex

_PANDAPOWER_CASES = (
    "case39",
    "case57",
    "case118",
    "case145",
    "case300",
    "case89pegase",
    "case_illinois200",
)


def _load_pandapower_case(case_name: str) -> dict[str, Any]:
    try:
        import pandapower.networks as pn
        from pandapower.converter import to_mpc
    except Exception as exc:  # pragma: no cover - exercised in environments without pandapower
        raise KeyError(
            f"Case {case_name} requires pandapower. Install the environment from environment.yml first."
        ) from exc

    try:
        loader = getattr(pn, case_name)
    except AttributeError as exc:
        raise KeyError(f"Unsupported pandapower-backed case: {case_name}") from exc

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            net = loader()
            mpc = to_mpc(net, init="flat")["mpc"]

    bus = mpc["bus"][:, :13].tolist()
    gen = mpc["gen"][:, :10].tolist()
    branch = mpc["branch"][:, :13].tolist()
    bus_name = [str(value) if value is not None else None for value in net.bus["name"].tolist()]

    return {
        "case_name": case_name,
        "source_library": "pandapower",
        "source_url": f"pandapower.networks.{case_name}()",
        "matpower_case_format_version": str(mpc.get("version", "2")),
        "baseMVA": float(mpc["baseMVA"]),
        "bus": bus,
        "gen": gen,
        "branch": branch,
        "bus_name": bus_name,
    }


def available_cases() -> list[str]:
    names = set(available_builtin_cases())
    try:
        import pandapower.networks as pn

        names.update(name for name in _PANDAPOWER_CASES if hasattr(pn, name))
    except Exception:
        pass
    return sorted(names)


def load_case(case_name: str) -> dict[str, Any]:
    if case_name in available_builtin_cases():
        case = load_builtin_case(case_name)
    elif case_name in _PANDAPOWER_CASES:
        case = _load_pandapower_case(case_name)
    else:
        raise KeyError(f"Unsupported case: {case_name}. Supported cases: {', '.join(available_cases())}")
    case["data_digest"] = stable_hex(case["case_name"], canonical_json({
        "baseMVA": case["baseMVA"],
        "bus": case["bus"],
        "gen": case["gen"],
        "branch": case["branch"],
    }), length=16)
    return case
