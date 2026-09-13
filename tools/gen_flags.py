"""
Dev-only generator for the ComfyUI startup-flags dictionary.

NOT shipped to users. Run it manually when a new ComfyUI release adds/renames
flags, then review the generated `assets/data/flags.json` by hand before commit.

What it does
------------
1. AST-parses a ComfyUI ``comfy/cli_args.py`` (no import, no code execution) and
   extracts every ``add_argument`` with its type, default, choices, help text and
   mutually-exclusive group.
2. Writes ``tools/all_flags.json`` — the full raw dump (reference only).
3. Merges a curated selection (CURATION below) with that raw metadata and writes
   ``assets/data/flags.json`` — the grouped "greatest hits" dictionary the app
   ships and shows in the flags picker.

Usage
-----
    python tools/gen_flags.py [path/to/comfy/cli_args.py]

Default path points at the local test build.
"""

from __future__ import annotations

import ast
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CLI_ARGS = r"C:\Users\Admin\ComfyUI_windows_portable\ComfyUI\comfy\cli_args.py"
ALL_FLAGS_OUT = os.path.join(REPO_ROOT, "tools", "all_flags.json")
FLAGS_JSON_OUT = os.path.join(REPO_ROOT, "assets", "data", "flags.json")


# ── Curated selection ────────────────────────────────────────────────────────
# (group_id, group_title, [ (flag, description) | (flag, description, overrides) ])
# `overrides` may set: type, value_type, default, choices — to override what the
# raw parser inferred (e.g. treat an optional-value flag as a plain toggle, or
# give a value flag a sensible pre-fill default for the picker).
CURATION = [
    (
        "device",
        "Device / Backend",
        [
            ("--cpu", "Run everything on the CPU (slow, but works without a GPU)."),
            (
                "--directml",
                "Use torch-directml (AMD / DirectX 12 GPUs on Windows).",
                {"type": "bool"},
            ),
            (
                "--cuda-device",
                "Select CUDA device id(s), e.g. 0 or 0,1.",
                {"default": "0"},
            ),
        ],
    ),
    (
        "vram",
        "VRAM / Memory",
        [
            ("--gpu-only", "Keep everything on the GPU (fastest, needs lots of VRAM)."),
            ("--highvram", "Keep models in VRAM between runs."),
            ("--lowvram", "Run text encoders on the CPU to save VRAM."),
            ("--novram", "Most aggressive VRAM saving, for very low-VRAM GPUs."),
            (
                "--reserve-vram",
                "Reserve N GB of VRAM for the OS / other apps.",
                {"default": 2},
            ),
            ("--disable-smart-memory", "Aggressively offload models to system RAM."),
        ],
    ),
    (
        "precision",
        "Precision",
        [
            ("--force-fp32", "Force fp32 everywhere (most compatible, slowest)."),
            ("--force-fp16", "Force fp16 everywhere."),
            ("--fp16-vae", "Run the VAE in fp16 (faster, may cause black images)."),
            ("--fp32-vae", "Run the VAE in full-precision fp32 (most compatible)."),
            ("--bf16-vae", "Run the VAE in bf16."),
            ("--fp16-unet", "Run the diffusion model in fp16."),
            ("--bf16-unet", "Run the diffusion model in bf16."),
            (
                "--fp8_e4m3fn-unet",
                "Store diffusion-model weights in fp8 (saves memory).",
            ),
        ],
    ),
    (
        "attention",
        "Attention",
        [
            (
                "--use-split-cross-attention",
                "Split cross-attention (lower memory use).",
            ),
            ("--use-pytorch-cross-attention", "PyTorch 2.0 cross-attention."),
            ("--use-sage-attention", "SageAttention (fast, needs hardware support)."),
            ("--use-flash-attention", "FlashAttention (fast, needs hardware support)."),
            ("--disable-xformers", "Disable xformers."),
        ],
    ),
    (
        "performance",
        "Performance / Cache",
        [
            (
                "--fast",
                "Enable experimental speed optimizations (e.g. fp16_accumulation).",
                {"type": "bool"},
            ),
            ("--cache-classic", "Old aggressive caching."),
            ("--cache-none", "Minimal RAM/VRAM use; re-runs every node each time."),
            (
                "--cache-lru",
                "Cache up to N node results (uses more RAM/VRAM).",
                {"default": 10},
            ),
            ("--deterministic", "Use slower, more reproducible algorithms."),
        ],
    ),
    (
        "network",
        "Network / Server",
        [
            (
                "--listen",
                "Listen on a given IP (bare = all interfaces).",
                {"default": "0.0.0.0"},
            ),
            ("--port", "Server listen port."),
            (
                "--enable-cors-header",
                "Enable CORS; optional origin, default '*'.",
                {"default": "*"},
            ),
        ],
    ),
    (
        "preview",
        "Preview",
        [
            (
                "--preview-method",
                "Latent preview method for sampler nodes.",
                {"default": "auto"},
            ),
            ("--preview-size", "Maximum latent preview size."),
        ],
    ),
    (
        "misc",
        "Custom Nodes / Misc",
        [
            ("--disable-all-custom-nodes", "Load no custom nodes (clean startup)."),
            ("--disable-api-nodes", "Disable API nodes and their internet access."),
            ("--multi-user", "Enable per-user storage."),
        ],
    ),
]

_TYPE_MAP = {"int": "int", "float": "float", "str": "str"}


def _literal(node):
    """Best-effort python value of an AST node; None when not a plain literal."""
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def _help_text(node):
    if node is None:
        return None
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return " ".join(node.value.split())
    # e.g. "... {}".format(...) — keep the template string
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        if node.func.attr == "format" and isinstance(node.func.value, ast.Constant):
            return " ".join(str(node.func.value.value).split())
    return None


def _collect_enums(tree):
    """enum class name -> [member values]."""
    enums = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            is_enum = any(
                (isinstance(b, ast.Attribute) and b.attr == "Enum")
                or (isinstance(b, ast.Name) and b.id == "Enum")
                for b in node.bases
            )
            if not is_enum:
                continue
            values = []
            for stmt in node.body:
                if isinstance(stmt, ast.Assign) and isinstance(
                    stmt.value, ast.Constant
                ):
                    values.append(stmt.value.value)
            enums[node.name] = values
    return enums


def _collect_excl_groups(tree):
    """variable name -> group id, for add_mutually_exclusive_group() results."""
    groups = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            call = node.value
            if (
                isinstance(call.func, ast.Attribute)
                and call.func.attr == "add_mutually_exclusive_group"
                and node.targets
                and isinstance(node.targets[0], ast.Name)
            ):
                groups[node.targets[0].id] = node.targets[0].id
    return groups


def parse_cli_args(path):
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source)
    enums = _collect_enums(tree)
    excl = _collect_excl_groups(tree)

    flags = []
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "add_argument"
        ):
            continue
        if not node.args:
            continue
        option = _literal(node.args[0])
        if not (isinstance(option, str) and option.startswith("--")):
            continue

        recv = node.func.value
        recv_name = recv.id if isinstance(recv, ast.Name) else None

        kw = {k.arg: k.value for k in node.keywords}
        action = _literal(kw.get("action"))
        action_name = None
        if isinstance(kw.get("action"), ast.Name):
            action_name = kw["action"].id
        type_name = kw["type"].id if isinstance(kw.get("type"), ast.Name) else None
        default = _literal(kw.get("default"))
        choices = _literal(kw.get("choices"))
        const = _literal(kw.get("const"))
        nargs = _literal(kw.get("nargs"))
        metavar = _literal(kw.get("metavar"))
        help_text = _help_text(kw.get("help"))

        # classify
        value_type = None
        if action in ("store_true", "store_false"):
            kind = "bool"
        elif choices:
            kind = "choice"
        elif action_name == "EnumAction" or type_name in enums:
            kind = "choice"
            choices = enums.get(type_name, choices)
        elif type_name in _TYPE_MAP:
            kind = "value"
            value_type = _TYPE_MAP[type_name]
        elif type_name is not None:
            kind = "value"  # e.g. is_valid_directory
            value_type = "str"
        else:
            kind = "value"
            value_type = "str"

        flags.append(
            {
                "flag": option,
                "type": kind,
                "value_type": value_type,
                "default": default,
                "choices": choices,
                "const": const,
                "nargs": nargs,
                "metavar": metavar,
                "multi": nargs in ("*", "+"),
                "exclusive_group": excl.get(recv_name),
                "help": help_text,
            }
        )
    return flags


def build_curated(raw_by_flag):
    groups = []
    missing = []
    for group_id, title, entries in CURATION:
        out_flags = []
        for entry in entries:
            flag = entry[0]
            desc = entry[1]
            overrides = entry[2] if len(entry) > 2 else {}
            raw = raw_by_flag.get(flag)
            if raw is None:
                missing.append(flag)
                continue
            kind = overrides.get("type", raw["type"])
            if kind == "bool":
                # a toggle carries no value metadata
                value_type = None
                default = None
                choices = None
            else:
                value_type = overrides.get("value_type", raw["value_type"])
                default = overrides.get("default", raw["default"])
                choices = overrides.get("choices", raw["choices"])
            item = {
                "flag": flag,
                "type": kind,
                "value_type": value_type,
                "default": default,
                "choices": choices,
                "exclusive_group": raw["exclusive_group"],
                "description": desc,
            }
            out_flags.append(item)
        groups.append({"id": group_id, "title": title, "flags": out_flags})
    return {"groups": groups}, missing


def main():
    cli_args_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CLI_ARGS
    if not os.path.exists(cli_args_path):
        sys.exit(f"cli_args.py not found: {cli_args_path}")

    raw = parse_cli_args(cli_args_path)
    os.makedirs(os.path.dirname(ALL_FLAGS_OUT), exist_ok=True)
    with open(ALL_FLAGS_OUT, "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=2, ensure_ascii=False)
    print(f"[all_flags] {len(raw)} flags -> {ALL_FLAGS_OUT}")

    raw_by_flag = {r["flag"]: r for r in raw}
    curated, missing = build_curated(raw_by_flag)
    os.makedirs(os.path.dirname(FLAGS_JSON_OUT), exist_ok=True)
    with open(FLAGS_JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(curated, f, indent=2, ensure_ascii=False)
    n = sum(len(g["flags"]) for g in curated["groups"])
    print(
        f"[flags.json] {n} curated flags in {len(curated['groups'])} groups "
        f"-> {FLAGS_JSON_OUT}"
    )
    if missing:
        print(f"[WARN] curated flags not found in this cli_args.py: {missing}")


if __name__ == "__main__":
    main()
