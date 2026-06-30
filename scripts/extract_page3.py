from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

from lxml import etree


NS = {
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
    "hs": "http://www.hancom.co.kr/hwpml/2011/section",
    "opf": "http://www.idpf.org/2007/opf/",
}


def parse_xml(data: bytes) -> etree._Element:
    return etree.fromstring(data)


def serialize(root: etree._Element) -> bytes:
    return etree.tostring(
        root,
        encoding="UTF-8",
        xml_declaration=True,
        standalone=True,
    )


def element_text(el: etree._Element) -> str:
    return "".join(el.xpath(".//hp:t//text()", namespaces=NS))


def direct_children(root: etree._Element) -> list[etree._Element]:
    return [child for child in root if isinstance(child.tag, str)]


def remove_linesegarray(root: etree._Element) -> int:
    removed = 0
    for node in list(root.xpath(".//hp:linesegarray", namespaces=NS)):
        parent = node.getparent()
        if parent is not None:
            parent.remove(node)
            removed += 1
    return removed


def first_paragraph_with_secpr(children: list[etree._Element]) -> etree._Element | None:
    for child in children:
        if child.xpath(".//hp:secPr", namespaces=NS):
            return child
    return None


def ensure_first_child_has_secpr(
    selected_children: list[etree._Element],
    source_children: list[etree._Element],
) -> bool:
    if not selected_children:
        return False
    first = selected_children[0]
    if first.xpath(".//hp:secPr", namespaces=NS):
        return False

    source = first_paragraph_with_secpr(source_children)
    if source is None:
        return False

    source_run = source.find(".//hp:run", namespaces=NS)
    target_run = first.find(".//hp:run", namespaces=NS)
    if source_run is None or target_run is None:
        return False

    for child in reversed(list(source_run)):
        qname = etree.QName(child).localname
        if qname in {"secPr", "ctrl"}:
            target_run.insert(0, copy.deepcopy(child))
    return True


def make_blank_section(section_root: etree._Element, source_children: list[etree._Element]) -> etree._Element:
    blank_root = copy.deepcopy(section_root)
    for child in list(blank_root):
        blank_root.remove(child)

    source = first_paragraph_with_secpr(source_children)
    if source is None:
        return blank_root

    blank_p = copy.deepcopy(source)
    for tbl in list(blank_p.xpath(".//hp:tbl", namespaces=NS)):
        parent = tbl.getparent()
        if parent is not None:
            parent.remove(tbl)
    for t_node in blank_p.xpath(".//hp:t", namespaces=NS):
        t_node.text = ""
        for nested in list(t_node):
            t_node.remove(nested)
    remove_linesegarray(blank_p)
    blank_root.append(blank_p)
    return blank_root


def write_zip_like_source(source: Path, output: Path, replacements: dict[str, bytes], drop: set[str] | None = None) -> None:
    drop = drop or set()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source, "r") as src, zipfile.ZipFile(output, "w") as dst:
        for info in src.infolist():
            if info.filename in drop:
                continue
            data = replacements.get(info.filename)
            if data is None:
                data = src.read(info.filename)

            new_info = zipfile.ZipInfo(info.filename, info.date_time)
            new_info.compress_type = info.compress_type
            new_info.comment = info.comment
            new_info.extra = info.extra
            new_info.internal_attr = info.internal_attr
            new_info.external_attr = info.external_attr
            new_info.create_system = info.create_system
            new_info.extract_version = info.extract_version
            new_info.create_version = info.create_version
            new_info.flag_bits = info.flag_bits
            dst.writestr(new_info, data)


def remove_section1_from_content_hpf(data: bytes) -> bytes:
    root = parse_xml(data)
    manifest = root.find(".//opf:manifest", namespaces=NS)
    spine = root.find(".//opf:spine", namespaces=NS)
    if manifest is not None:
        for item in list(manifest.findall("opf:item", namespaces=NS)):
            if item.get("id") == "section1" or item.get("href") == "Contents/section1.xml":
                manifest.remove(item)
    if spine is not None:
        for itemref in list(spine.findall("opf:itemref", namespaces=NS)):
            if itemref.get("idref") == "section1":
                spine.remove(itemref)
    return serialize(root)


def update_preview_text(source_text: bytes, page_text: str) -> bytes:
    try:
        decoded = source_text.decode("utf-8")
    except UnicodeDecodeError:
        decoded = source_text.decode("utf-8", errors="ignore")
    if not decoded.strip():
        return page_text.encode("utf-8")
    # Keep the source preview format simple and truthful for the extracted page.
    lines = [line.strip() for line in page_text.splitlines() if line.strip()]
    return ("\r\n".join(lines) + "\r\n").encode("utf-8")


def parse_indexes(raw: str) -> list[int]:
    indexes: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_raw, end_raw = part.split("-", 1)
            start = int(start_raw)
            end = int(end_raw)
            if end < start:
                raise ValueError(f"Invalid descending range: {part}")
            indexes.extend(range(start, end + 1))
        else:
            indexes.append(int(part))
    if not indexes:
        raise ValueError("No child indexes were provided")
    return indexes


def extract_page3(
    source: Path,
    output: Path,
    report: Path,
    mode: str,
    source_section: str,
    selected_indexes: list[int],
) -> dict:
    with zipfile.ZipFile(source, "r") as zf:
        section0_data = zf.read("Contents/section0.xml")
        section1_data = zf.read(source_section)
        content_hpf = zf.read("Contents/content.hpf")
        preview_text = zf.read("Preview/PrvText.txt") if "Preview/PrvText.txt" in zf.namelist() else b""

    section1_root = parse_xml(section1_data)
    source_children = direct_children(section1_root)
    missing_indexes = [i for i in selected_indexes if i < 0 or i >= len(source_children)]
    if missing_indexes:
        raise ValueError(f"Selected child indexes out of range: {missing_indexes}; available 0..{len(source_children)-1}")
    selected = [copy.deepcopy(source_children[i]) for i in selected_indexes]

    new_section0 = copy.deepcopy(section1_root)
    for child in list(new_section0):
        new_section0.remove(child)
    for child in selected:
        new_section0.append(child)

    secpr_inserted = ensure_first_child_has_secpr(direct_children(new_section0), source_children)
    removed_lower = remove_linesegarray(new_section0)
    page_text = "\n".join(element_text(child) for child in direct_children(new_section0))

    replacements = {
        "Contents/section0.xml": serialize(new_section0),
        "Preview/PrvText.txt": update_preview_text(preview_text, page_text),
    }
    drop: set[str] = set()

    if mode == "preserve-sections":
        blank_section1 = make_blank_section(section1_root, source_children)
        removed_blank = remove_linesegarray(blank_section1)
        replacements["Contents/section1.xml"] = serialize(blank_section1)
    else:
        removed_blank = None
        replacements["Contents/content.hpf"] = remove_section1_from_content_hpf(content_hpf)
        drop.add("Contents/section1.xml")

    write_zip_like_source(source, output, replacements, drop=drop)

    summary = {
        "source": str(source),
        "output": str(output),
        "mode": mode,
        "selectedOriginalSection": source_section,
        "selectedTopLevelChildren": selected_indexes,
        "selectedChildSummary": [
            {
                "index": i,
                "pageBreak": source_children[i].get("pageBreak"),
                "hasSecPr": bool(source_children[i].xpath(".//hp:secPr", namespaces=NS)),
                "tableCount": len(source_children[i].xpath(".//hp:tbl", namespaces=NS)),
                "text": re.sub(r"\s+", " ", element_text(source_children[i])).strip()[:160],
            }
            for i in selected_indexes
        ],
        "secPrInsertedIntoFirstSelectedChild": secpr_inserted,
        "removedLinesegarrayFromPage3Section": removed_lower,
        "removedLinesegarrayFromBlankSection1": removed_blank,
        "outputSize": output.stat().st_size,
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def inspect(source: Path) -> dict:
    with zipfile.ZipFile(source, "r") as zf:
        section_names = [name for name in zf.namelist() if re.match(r"Contents/section\d+\.xml$", name)]
        sections = {}
        for name in section_names:
            root = parse_xml(zf.read(name))
            children = direct_children(root)
            sections[name] = [
                {
                    "index": i,
                    "pageBreak": child.get("pageBreak"),
                    "hasSecPr": bool(child.xpath(".//hp:secPr", namespaces=NS)),
                    "tableCount": len(child.xpath(".//hp:tbl", namespaces=NS)),
                    "text": re.sub(r"\s+", " ", element_text(child)).strip()[:160],
                }
                for i, child in enumerate(children)
            ]
    return {"source": str(source), "sections": sections}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--mode", choices=["preserve-sections", "single-section"], default="preserve-sections")
    parser.add_argument("--source-section", default="Contents/section1.xml")
    parser.add_argument(
        "--children",
        default="12-23",
        help="Top-level child indexes to keep, e.g. 12-23 or 0,2,4-6. Defaults to the third page range in the original culture-center file.",
    )
    parser.add_argument("--inspect", action="store_true")
    args = parser.parse_args()

    if args.inspect:
        print(json.dumps(inspect(args.source), ensure_ascii=False, indent=2))
        return

    if args.output is None or args.report is None:
        raise SystemExit("--output and --report are required unless --inspect is used")
    summary = extract_page3(
        args.source,
        args.output,
        args.report,
        args.mode,
        args.source_section,
        parse_indexes(args.children),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
