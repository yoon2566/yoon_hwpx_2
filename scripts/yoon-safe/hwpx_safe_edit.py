from __future__ import annotations

import argparse
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo


REQUIRED_ENTRIES = [
    "mimetype",
    "Contents/content.hpf",
    "Contents/header.xml",
    "Contents/section0.xml",
]

TEXT_NODE_RE = re.compile(r"(<hp:t(?:\s[^>]*)?>)(.*?)(</hp:t>)", re.S)
LINESEG_PAIR_RE = re.compile(r"<hp:linesegarray\b[^>]*>.*?</hp:linesegarray>", re.S)
LINESEG_SELF_RE = re.compile(r"<hp:linesegarray\b[^>]*/>", re.S)


def path_arg(value: str) -> Path:
    return Path(value).expanduser().resolve()


def write_json(data: Any, output: Path | None) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
    else:
        sys.stdout.write(text + "\n")


def decode_xml(data: bytes) -> str:
    return data.decode("utf-8-sig")


def section_names(names: list[str]) -> list[str]:
    return [name for name in names if name.startswith("Contents/section") and name.endswith(".xml")]


def read_text_entry(hwpx_path: Path, entry_name: str) -> str:
    with ZipFile(hwpx_path, "r") as zf:
        return decode_xml(zf.read(entry_name))


def xml_is_well_formed(text: str) -> tuple[bool, str | None]:
    try:
        ET.fromstring(text)
        return True, None
    except ET.ParseError as exc:
        return False, str(exc)


def analyze_section(section_xml: str) -> dict[str, Any]:
    nodes = TEXT_NODE_RE.findall(section_xml)
    well_formed, xml_error = xml_is_well_formed(section_xml)
    return {
        "xmlWellFormed": well_formed,
        "xmlError": xml_error,
        "textNodeCount": len(nodes),
        "nonEmptyTextNodeCount": sum(1 for _start, text, _end in nodes if html.unescape(text).strip()),
        "tableCount": len(re.findall(r"<hp:tbl\b", section_xml)),
        "linesegarrayCount": len(re.findall(r"<hp:linesegarray\b", section_xml)),
        "linesegCount": len(re.findall(r"<hp:lineseg\b", section_xml)),
    }


def analyze_hwpx(hwpx_path: Path) -> dict[str, Any]:
    with ZipFile(hwpx_path, "r") as zf:
        infos = zf.infolist()
        names = [info.filename for info in infos]
        required_missing = [name for name in REQUIRED_ENTRIES if name not in names]
        sections = section_names(names)
        section_stats = {}
        xml_entries = [
            name
            for name in names
            if name.endswith((".xml", ".hpf", ".rdf")) and not name.endswith("/")
        ]
        xml_stats = {}
        for name in xml_entries:
            try:
                text = decode_xml(zf.read(name))
                ok, error = xml_is_well_formed(text)
            except Exception as exc:  # noqa: BLE001 - report validation detail
                ok, error = False, str(exc)
            xml_stats[name] = {"wellFormed": ok, "error": error}
        for name in sections:
            section_stats[name] = analyze_section(decode_xml(zf.read(name)))
    return {
        "path": str(hwpx_path),
        "firstEntry": infos[0].filename if infos else None,
        "entryCount": len(infos),
        "requiredMissing": required_missing,
        "requiredPresent": [name for name in REQUIRED_ENTRIES if name in names],
        "sections": sections,
        "sectionStats": section_stats,
        "xmlStats": xml_stats,
        "entries": [
            {
                "name": info.filename,
                "compressType": info.compress_type,
                "fileSize": info.file_size,
                "compressSize": info.compress_size,
                "flagBits": info.flag_bits,
                "createSystem": info.create_system,
                "externalAttr": info.external_attr,
            }
            for info in infos
        ],
    }


def extract_text_map(hwpx_path: Path, sections: list[str] | None = None) -> dict[str, Any]:
    analysis = analyze_hwpx(hwpx_path)
    section_list = sections or analysis["sections"]
    nodes_out = []
    with ZipFile(hwpx_path, "r") as zf:
        for section in section_list:
            xml = decode_xml(zf.read(section))
            for index, match in enumerate(TEXT_NODE_RE.finditer(xml)):
                text = html.unescape(match.group(2))
                nodes_out.append(
                    {
                        "section": section,
                        "index": index,
                        "text": text,
                        "empty": not bool(text.strip()),
                    }
                )
    return {
        "source": str(hwpx_path),
        "nodes": nodes_out,
        "replacements": [],
        "notes": "Copy selected nodes into replacements and set text. Do not edit table structure.",
    }


def load_replacement_map(map_path: Path) -> dict[str, dict[int, str]]:
    data = json.loads(map_path.read_text(encoding="utf-8"))
    result: dict[str, dict[int, str]] = {}

    if isinstance(data, dict) and isinstance(data.get("replacements"), list):
        for item in data["replacements"]:
            section = str(item.get("section") or "Contents/section0.xml")
            index = int(item["index"])
            text = str(item.get("text", ""))
            result.setdefault(section, {})[index] = text
        return result

    if isinstance(data, dict) and isinstance(data.get("sections"), dict):
        for section, replacements in data["sections"].items():
            if not isinstance(replacements, dict):
                raise ValueError(f"section replacements must be object: {section}")
            for index, text in replacements.items():
                result.setdefault(str(section), {})[int(index)] = str(text)
        return result

    if isinstance(data, dict):
        for index, text in data.items():
            if str(index).isdigit():
                result.setdefault("Contents/section0.xml", {})[int(index)] = str(text)
        if result:
            return result

    raise ValueError("Unsupported text map format. Use a replacements list or sections object.")


def replace_text_nodes(section_xml: str, replacements: dict[int, str]) -> tuple[str, int]:
    matches = list(TEXT_NODE_RE.finditer(section_xml))
    out: list[str] = []
    cursor = 0
    applied = 0
    for index, match in enumerate(matches):
        out.append(section_xml[cursor : match.start()])
        if index in replacements:
            out.append(match.group(1))
            out.append(html.escape(replacements[index], quote=False))
            out.append(match.group(3))
            applied += 1
        else:
            out.append(match.group(0))
        cursor = match.end()
    out.append(section_xml[cursor:])
    return "".join(out), applied


def remove_linesegarray_from_xml(section_xml: str) -> tuple[str, int]:
    cleaned, self_count = LINESEG_SELF_RE.subn("", section_xml)
    cleaned, pair_count = LINESEG_PAIR_RE.subn("", cleaned)
    return cleaned, self_count + pair_count


def clone_zipinfo(info: ZipInfo) -> ZipInfo:
    new_info = ZipInfo(info.filename, info.date_time)
    new_info.compress_type = info.compress_type
    new_info.comment = info.comment
    new_info.extra = info.extra
    new_info.internal_attr = info.internal_attr
    new_info.external_attr = info.external_attr
    new_info.create_system = info.create_system
    return new_info


def write_hwpx_with_replacements(source: Path, output: Path, entry_data: dict[str, bytes]) -> None:
    if source.resolve() == output.resolve():
        raise ValueError("Refusing to overwrite the source HWPX in place.")
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(source, "r") as zin, ZipFile(output, "w") as zout:
        for info in zin.infolist():
            data = entry_data.get(info.filename)
            if data is None:
                data = zin.read(info.filename)
            new_info = clone_zipinfo(info)
            if info.filename == "mimetype" and info.compress_type != ZIP_STORED:
                new_info.compress_type = ZIP_STORED
            elif info.compress_type not in (ZIP_STORED, ZIP_DEFLATED):
                new_info.compress_type = ZIP_DEFLATED
            zout.writestr(new_info, data)


def apply_text_map(
    source: Path,
    map_path: Path,
    output: Path,
    remove_linesegarray: bool = True,
) -> dict[str, Any]:
    replacements = load_replacement_map(map_path)
    changed_entries: dict[str, bytes] = {}
    applied_total = 0
    removed_total = 0

    with ZipFile(source, "r") as zf:
        names = set(zf.namelist())
        for section, section_replacements in replacements.items():
            if section not in names:
                raise ValueError(f"Section not found in source HWPX: {section}")
            xml = decode_xml(zf.read(section))
            xml, applied = replace_text_nodes(xml, section_replacements)
            applied_total += applied
            if remove_linesegarray:
                xml, removed = remove_linesegarray_from_xml(xml)
                removed_total += removed
            changed_entries[section] = xml.encode("utf-8")

    write_hwpx_with_replacements(source, output, changed_entries)
    return {
        "source": str(source),
        "output": str(output),
        "map": str(map_path),
        "changedSections": sorted(changed_entries),
        "appliedReplacements": applied_total,
        "removedLinesegarray": removed_total,
    }


def remove_linesegarray_from_hwpx(source: Path, output: Path) -> dict[str, Any]:
    changed_entries: dict[str, bytes] = {}
    removed_total = 0
    with ZipFile(source, "r") as zf:
        for section in section_names(zf.namelist()):
            xml = decode_xml(zf.read(section))
            cleaned, removed = remove_linesegarray_from_xml(xml)
            if removed:
                changed_entries[section] = cleaned.encode("utf-8")
                removed_total += removed
    write_hwpx_with_replacements(source, output, changed_entries)
    return {
        "source": str(source),
        "output": str(output),
        "changedSections": sorted(changed_entries),
        "removedLinesegarray": removed_total,
    }


def validate_hwpx(
    hwpx_path: Path,
    must_contain: list[str] | None = None,
    must_not_contain: list[str] | None = None,
    expect_no_linesegarray: bool = False,
) -> dict[str, Any]:
    must_contain = must_contain or []
    must_not_contain = must_not_contain or []
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})

    try:
        analysis = analyze_hwpx(hwpx_path)
    except Exception as exc:  # noqa: BLE001 - validation report
        return {"path": str(hwpx_path), "ok": False, "checks": [{"name": "open-zip", "ok": False, "detail": str(exc)}]}

    add("first-entry-mimetype", analysis["firstEntry"] == "mimetype", str(analysis["firstEntry"]))
    add("required-entries", not analysis["requiredMissing"], ", ".join(analysis["requiredMissing"]))

    xml_bad = [name for name, item in analysis["xmlStats"].items() if not item["wellFormed"]]
    add("xml-well-formed", not xml_bad, ", ".join(xml_bad))

    combined_xml = ""
    with ZipFile(hwpx_path, "r") as zf:
        for section in analysis["sections"]:
            combined_xml += decode_xml(zf.read(section))
    combined_text = html.unescape(combined_xml)

    for text in must_contain:
        add(f"must-contain:{text}", text in combined_text)
    for text in must_not_contain:
        add(f"must-not-contain:{text}", text not in combined_text)

    if expect_no_linesegarray:
        total_linesegarray = sum(item["linesegarrayCount"] for item in analysis["sectionStats"].values())
        add("no-linesegarray", total_linesegarray == 0, str(total_linesegarray))

    return {
        "path": str(hwpx_path),
        "ok": all(item["ok"] for item in checks),
        "checks": checks,
        "analysis": analysis,
    }


def add_common_json_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", type=path_arg, default=None, help="Write JSON output to this path instead of stdout.")
