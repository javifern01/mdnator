import argparse
import logging
import os
import sys
import threading
import time
import warnings
from pathlib import Path

# Enable ANSI color support on Windows
os.system("")

# ANSI color constants
_CYAN  = "\033[36m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED   = "\033[31m"
_GREY  = "\033[90m"
_BOLD  = "\033[1m"
_RESET = "\033[0m"

# Silence noisy third-party libraries before importing them
logging.getLogger("pdfminer").setLevel(logging.ERROR)
logging.getLogger("markitdown").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=UserWarning)
# Redirect stderr during import to swallow any startup noise
_devnull = open(os.devnull, "w")

from markitdown import MarkItDown  # noqa: E402
from tqdm import tqdm              # noqa: E402

SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".xlsx", ".pptx",
    ".html", ".htm", ".csv", ".json", ".xml",
    ".zip", ".epub", ".txt",
}


def collect_files(input_path: Path, recursive: bool) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    pattern = "**/*" if recursive else "*"
    return [p for p in input_path.glob(pattern) if p.is_file()]


def resolve_output_path(file: Path, input_path: Path, output_dir: Path) -> Path:
    rel = Path(file.name) if input_path.is_file() else file.relative_to(input_path)
    return output_dir / rel.with_suffix(".md")


def _fmt_duration(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def _truncate(name: str, max_len: int) -> str:
    return name if len(name) <= max_len else name[: max_len - 1] + "…"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert files to Markdown using markitdown."
    )
    parser.add_argument("path", type=Path, help="Input file or directory")
    parser.add_argument("--output-dir", "-o", type=Path, required=True, help="Output directory")
    parser.add_argument("--recursive", "-r", action="store_true", help="Recurse into subdirectories")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed without writing")
    args = parser.parse_args()

    input_path: Path = args.path.resolve()
    output_dir: Path = args.output_dir.resolve()

    if not input_path.exists():
        print(f"{_RED}[ERROR]{_RESET} Path does not exist: {input_path}", file=sys.stderr)
        sys.exit(1)

    files = collect_files(input_path, args.recursive)
    candidates = [f for f in files if f.suffix.lower() in SUPPORTED_EXTENSIONS]

    if not candidates:
        print(f"{_YELLOW}No compatible files found.{_RESET}")
        return

    if args.dry_run:
        for f in candidates:
            print(f"{_GREY}[DRY-RUN]{_RESET} {f} {_GREY}->{_RESET} {resolve_output_path(f, input_path, output_dir)}")
        return

    md = MarkItDown()
    ok = errors = 0
    error_lines: list[str] = []
    t_start = time.monotonic()

    bar_format = (
        f"  {_GREY}[{{bar:20}}]{_RESET}"
        f" {_BOLD}{{percentage:3.0f}}%{_RESET}"
        f" {_GREY}{{n}}/{{total}} {{elapsed}}{_RESET}"
        f" {{postfix}}"
    )

    with tqdm(candidates, unit="file", ncols=120, bar_format=bar_format,
              ascii="░█") as bar:
        for file in bar:
            bar.set_postfix_str(f"{_CYAN}{_truncate(file.name, 40)}{_RESET} {_GREY}procesando…{_RESET}")
            out_path = resolve_output_path(file, input_path, output_dir)
            result_box: list = []
            exc_box:    list = []

            def _convert():
                old_stderr, sys.stderr = sys.stderr, _devnull
                try:
                    result_box.append(md.convert(str(file)))
                except Exception as e:
                    exc_box.append(e)
                finally:
                    sys.stderr = old_stderr

            t = threading.Thread(target=_convert, daemon=True)
            t.start()
            while t.is_alive():
                bar.refresh()
                time.sleep(0.1)
            t.join()

            if exc_box:
                error_lines.append(f"  {_GREY}•{_RESET} {file.name}: {exc_box[0]}")
                errors += 1
                bar.set_postfix_str(f"{_RED}✗{_RESET}")
            else:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(result_box[0].text_content, encoding="utf-8")
                ok += 1
                bar.set_postfix_str(f"{_GREEN}✓{_RESET}")

    elapsed = time.monotonic() - t_start
    total = ok + errors
    speed = total / elapsed if elapsed > 0 else 0.0
    sep = f"{_GREY}{'─' * 44}{_RESET}"

    print(f"\n{sep}")
    ok_str   = f"{_GREEN}✓  {ok} convertidos{_RESET}"
    err_str  = f"{_RED}✗  {errors} errores{_RESET}" if errors else f"{_GREY}✗  0 errores{_RESET}"
    print(f"  {ok_str}    {err_str}")
    print(f"  {_GREY}Tiempo: {_fmt_duration(elapsed)}   Velocidad: {speed:.1f} archivos/s{_RESET}")

    if error_lines:
        print(sep)
        print(f"  {_BOLD}Errores:{_RESET}")
        for line in error_lines:
            print(line)

    print(sep)


if __name__ == "__main__":
    main()
