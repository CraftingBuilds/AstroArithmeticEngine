from pathlib import Path
import json

VAULT_PATH = Path("/mnt/storage/Obsidian/My Obsidian Vault/Astrology-Arith-m-etic")

ENGINE_ROOT = Path("/mnt/storage/AstroArithmeticEngine")

# We want the ENTIRE Building Blocks folder
BUILDING_BLOCKS_DIR = VAULT_PATH / "Building Blocks"

# Output goes to your actual engine folder, not home dir
OUTPUT_DIR = ENGINE_ROOT / "derived"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def safe_read_text(file_path: Path) -> str:
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return file_path.read_text(encoding="utf-8", errors="replace")


def should_skip(file_path: Path) -> bool:
    skip_names = {"INDEX.md", "README.md"}
    return file_path.name in skip_names


def build_entry(file_path: Path, base_dir: Path) -> dict:
    rel_path = file_path.relative_to(base_dir)
    parts = rel_path.parts

    category_path = list(parts[:-1])  # folders only
    name = file_path.stem

    return {
        "name": name,
        "source_file": str(file_path),
        "relative_path": str(rel_path),
        "category_path": category_path,
        "folder": str(file_path.parent),
        "content": safe_read_text(file_path).strip()
    }


def index_building_blocks(building_blocks_dir: Path) -> list:
    entries = []

    if not building_blocks_dir.exists():
        raise FileNotFoundError(f"Building Blocks folder not found: {building_blocks_dir}")

    for file_path in sorted(building_blocks_dir.rglob("*.md")):
        if should_skip(file_path):
            continue
        entries.append(build_entry(file_path, building_blocks_dir))

    return entries


def build_tree(entries: list) -> dict:
    tree = {}

    for entry in entries:
        node = tree
        for part in entry["category_path"]:
            node = node.setdefault(part, {})
        node.setdefault("_files", []).append({
            "name": entry["name"],
            "relative_path": entry["relative_path"],
            "source_file": entry["source_file"]
        })

    return tree


def main():
    print(f"Vault path: {VAULT_PATH}")
    print(f"Building Blocks path: {BUILDING_BLOCKS_DIR}")
    print(f"Engine root: {ENGINE_ROOT}")
    print(f"Output dir: {OUTPUT_DIR}")
    print()

    entries = index_building_blocks(BUILDING_BLOCKS_DIR)

    all_file = OUTPUT_DIR / "building_blocks_master_index.json"
    all_file.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    tree = build_tree(entries)
    tree_file = OUTPUT_DIR / "building_blocks_tree.json"
    tree_file.write_text(
        json.dumps(tree, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"Wrote {len(entries)} Building Blocks entries to:")
    print(f"  {all_file}")
    print()
    print("Wrote Building Blocks tree to:")
    print(f"  {tree_file}")


if __name__ == "__main__":
    main()
