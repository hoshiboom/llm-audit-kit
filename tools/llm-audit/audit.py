#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm-audit: LLM 应用安全查漏工具 v0.1

用法:
    python audit.py                           # 交互式自查
    python audit.py --non-interactive         # 仅打印清单
    python audit.py --answers answers.json    # 从 JSON 读取答案，生成报告
    python audit.py --layer L3                # 只看某一层
    python audit.py --output report.md        # 导出 Markdown 报告

设计原则:
- 零第三方依赖（仅 Python 3.8+ 标准库）
- checklist.yaml 是知识库，本脚本是驱动器
- 输出 人类可读报告 + JSON（便于 CI 集成）
"""

import argparse
import io
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Windows 控制台默认 GBK，强制切 UTF-8，避免 emoji / 生僻字符崩溃
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def _safe(s: str) -> str:
    """控制台输出安全化：无法编码的字符替换掉，避免 crash。"""
    enc = getattr(sys.stdout, "encoding", "utf-8") or "utf-8"
    try:
        s.encode(enc)
        return s
    except UnicodeEncodeError:
        return s.encode(enc, errors="replace").decode(enc, errors="replace")

# ============================================================
# 极简 YAML 解析器（只支持本 checklist 需要的子集）
# 支持: 嵌套映射、列表、标量（字符串/整数）、多行字符串用单行即可
# ============================================================

def _parse_scalar(s: str) -> Any:
    s = s.strip()
    if s == "":
        return ""
    # 去引号
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    # 整数
    if s.lstrip("-").isdigit():
        try:
            return int(s)
        except ValueError:
            pass
    # 布尔
    low = s.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "~"):
        return None
    return s


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def parse_yaml(text: str) -> Any:
    """极简 YAML parser，够本项目用。"""
    # 预处理：去掉注释（# 之后），保留 # 在引号内的情况（本 checklist 不会出现）
    raw_lines: List[str] = []
    for ln in text.splitlines():
        # 处理行内注释
        stripped = ln
        # 跳过纯注释行
        if stripped.strip().startswith("#"):
            continue
        # 简单去除行尾注释（不处理引号内的 #，checklist 无此情况）
        if " #" in stripped:
            # 只在 # 前有空格时认为是注释
            idx = stripped.find(" #")
            stripped = stripped[:idx]
        if stripped.strip() == "":
            continue
        raw_lines.append(stripped.rstrip())

    # 递归下降
    pos = [0]

    def parse_block(indent: int) -> Any:
        # 判断是列表还是映射
        if pos[0] >= len(raw_lines):
            return None
        first = raw_lines[pos[0]]
        if _indent_of(first) < indent:
            return None
        if first.lstrip().startswith("- "):
            return parse_list(indent)
        else:
            return parse_map(indent)

    def parse_map(indent: int) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        while pos[0] < len(raw_lines):
            line = raw_lines[pos[0]]
            cur_indent = _indent_of(line)
            if cur_indent < indent:
                break
            if cur_indent != indent:
                # 不应进入此分支（上层会处理子节点）
                break
            content = line.strip()
            if content.startswith("- "):
                break
            if ":" not in content:
                raise ValueError(f"Invalid line (expect 'key: value'): {line!r}")
            key, _, val = content.partition(":")
            key = key.strip()
            val = val.strip()
            pos[0] += 1
            if val == "":
                # 子块
                child = parse_block(indent + 2) if pos[0] < len(raw_lines) else None
                d[key] = child if child is not None else {}
            else:
                d[key] = _parse_scalar(val)
        return d

    def parse_list(indent: int) -> List[Any]:
        lst: List[Any] = []
        while pos[0] < len(raw_lines):
            line = raw_lines[pos[0]]
            cur_indent = _indent_of(line)
            if cur_indent < indent:
                break
            if cur_indent != indent:
                break
            content = line.strip()
            if not content.startswith("- "):
                break
            rest = content[2:]
            pos[0] += 1
            if ":" in rest and not (rest.startswith('"') or rest.startswith("'")):
                # 列表项是一个 map，rest 是 map 的第一行
                first_key, _, first_val = rest.partition(":")
                item: Dict[str, Any] = {}
                first_key = first_key.strip()
                first_val = first_val.strip()
                if first_val == "":
                    child = parse_block(indent + 2) if pos[0] < len(raw_lines) else {}
                    if isinstance(child, dict):
                        item[first_key] = child.get(first_key, child)
                        # 上一行子块本身就是整个 map 的其余字段
                        item = {first_key: None, **child} if False else child
                        # 修正：更稳妥处理 —— 回退到显式用临时行解析
                        # 为简化：重新走一趟 map 合并
                        item = {first_key: None}
                        item.update(child if isinstance(child, dict) else {})
                    else:
                        item[first_key] = child
                else:
                    item[first_key] = _parse_scalar(first_val)
                    # 继续读取属于该 item 的后续字段
                    while pos[0] < len(raw_lines):
                        nxt = raw_lines[pos[0]]
                        nxt_indent = _indent_of(nxt)
                        if nxt_indent <= indent:
                            break
                        if nxt.strip().startswith("- "):
                            break
                        # 该行属于当前 item（缩进 > indent）
                        sub = parse_map(nxt_indent)
                        if isinstance(sub, dict):
                            item.update(sub)
                        break
                lst.append(item)
            else:
                lst.append(_parse_scalar(rest))
        return lst

    # 顶层视作 map
    result = parse_map(0)
    return result


# ============================================================
# 主逻辑
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
CHECKLIST_PATH = SCRIPT_DIR / "checklist.yaml"


def load_checklist() -> Dict[str, Any]:
    if not CHECKLIST_PATH.exists():
        sys.exit(f"[错误] 找不到清单文件: {CHECKLIST_PATH}")
    text = CHECKLIST_PATH.read_text(encoding="utf-8")
    data = parse_yaml(text)
    if not isinstance(data, dict) or "layers" not in data:
        sys.exit("[错误] 清单格式不正确，缺少 layers 顶层字段")
    return data


def iter_items(data: Dict[str, Any], layer_filter: Optional[str] = None):
    for layer in data.get("layers", []):
        if not isinstance(layer, dict):
            continue
        lid = layer.get("id")
        if layer_filter and lid != layer_filter:
            continue
        for item in layer.get("items", []) or []:
            yield layer, item


# ---------- 交互式问答 ----------

def ask(question: str) -> str:
    while True:
        try:
            ans = input(question).strip().lower()
        except EOFError:
            return "skip"
        if ans in ("y", "yes", "是"):
            return "yes"
        if ans in ("n", "no", "否"):
            return "no"
        if ans in ("", "s", "skip", "?"):
            return "skip"
        if ans in ("na", "n/a", "不适用"):
            return "na"
        if ans in ("q", "quit", "exit"):
            return "quit"
        print("  请输入 y(yes) / n(no) / na(不适用) / s(跳过) / q(退出)")


def interactive_audit(data: Dict[str, Any], layer_filter: Optional[str]) -> Dict[str, str]:
    answers: Dict[str, str] = {}
    items = list(iter_items(data, layer_filter))
    total = len(items)
    print("=" * 72)
    print(" LLM 应用安全查漏工具  v0.1  (llm-audit)")
    print("=" * 72)
    print(f" 共 {total} 项检查。每项回答: y=yes / n=no / na=不适用 / s=跳过 / q=退出\n")

    for idx, (layer, item) in enumerate(items, 1):
        lid = layer.get("id")
        lname = layer.get("name")
        iid = item.get("id")
        title = item.get("title")
        question = item.get("question")
        weight = item.get("weight", 1)
        rationale = item.get("rationale", "")
        print("-" * 72)
        print(_safe(f"[{idx}/{total}] {lid} {lname}"))
        print(_safe(f"  [{iid}] {title}  (weight={weight})"))
        print(_safe(f"  根因: {rationale}"))
        ans = ask(_safe(f"  ? {question}  [y/n/na/s]: "))
        if ans == "quit":
            print("\n(已退出，保留当前答案)")
            break
        answers[iid] = ans
    return answers


# ---------- 报告生成 ----------

def compute_scores(data: Dict[str, Any], answers: Dict[str, str]) -> Dict[str, Any]:
    layer_stats: Dict[str, Dict[str, Any]] = {}
    gaps: List[Dict[str, Any]] = []
    total_w = 0
    total_got = 0

    for layer in data.get("layers", []):
        lid = layer["id"]
        lname = layer["name"]
        l_w = 0
        l_got = 0
        l_items = 0
        l_missed = 0
        for item in layer.get("items", []) or []:
            iid = item["id"]
            w = int(item.get("weight", 1))
            ans = answers.get(iid, "skip")
            if ans == "na":
                continue
            l_items += 1
            l_w += w
            if ans == "yes":
                l_got += w
            else:
                l_missed += 1
                if ans in ("no", "skip"):
                    gaps.append({
                        "layer": lid,
                        "layer_name": lname,
                        "id": iid,
                        "title": item.get("title"),
                        "weight": w,
                        "answer": ans,
                        "mitigation": item.get("mitigation", ""),
                        "rationale": item.get("rationale", ""),
                    })
        pct = (l_got / l_w * 100) if l_w > 0 else None
        layer_stats[lid] = {
            "name": lname,
            "items": l_items,
            "missed": l_missed,
            "weight_total": l_w,
            "weight_got": l_got,
            "percent": pct,
        }
        total_w += l_w
        total_got += l_got

    overall = (total_got / total_w * 100) if total_w > 0 else None
    # 按权重倒序
    gaps.sort(key=lambda x: (-x["weight"], x["id"]))
    return {
        "overall_percent": overall,
        "layers": layer_stats,
        "gaps": gaps,
    }


def grade(pct: Optional[float]) -> str:
    if pct is None:
        return "-"
    if pct >= 90:
        return "A (优秀)"
    if pct >= 75:
        return "B (良好)"
    if pct >= 60:
        return "C (及格)"
    if pct >= 40:
        return "D (薄弱)"
    return "F (危险)"


def print_report(report: Dict[str, Any]) -> None:
    print("\n" + "=" * 72)
    print(" 审计报告")
    print("=" * 72)
    pct = report["overall_percent"]
    pct_str = f"{pct:.1f}%" if pct is not None else "N/A"
    print(_safe(f" 总体得分: {pct_str}   等级: {grade(pct)}"))
    print()
    print(_safe(f" {'层':<6} {'名称':<40} {'得分':>8} {'等级':>10}"))
    print(" " + "-" * 70)
    for lid, s in report["layers"].items():
        p = s["percent"]
        pstr = f"{p:.1f}%" if p is not None else "N/A"
        print(_safe(f" {lid:<6} {s['name']:<40} {pstr:>8} {grade(p):>10}"))

    gaps = report["gaps"]
    if gaps:
        print()
        print(f" 发现 {len(gaps)} 项缺口（按权重倒序）：")
        print()
        for g in gaps:
            tag = "!!!" if g["weight"] >= 3 else ("!!" if g["weight"] == 2 else "!")
            print(_safe(f"  {tag} [{g['id']}] {g['title']}  (layer={g['layer']}, w={g['weight']}, ans={g['answer']})"))
            print(_safe(f"      建议: {g['mitigation']}"))
        print()
    else:
        print("\n  未发现缺口。")


def render_markdown(report: Dict[str, Any], data: Dict[str, Any], answers: Dict[str, str]) -> str:
    lines: List[str] = []
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pct = report["overall_percent"]
    pct_str = f"{pct:.1f}%" if pct is not None else "N/A"
    lines.append(f"# LLM 应用安全审计报告")
    lines.append("")
    lines.append(f"- 生成时间: `{ts}`")
    lines.append(f"- 总体得分: **{pct_str}**  等级: **{grade(pct)}**")
    lines.append("")
    lines.append("## 分层得分")
    lines.append("")
    lines.append("| 层 | 名称 | 检查项 | 未达标 | 得分 | 等级 |")
    lines.append("|----|------|-------:|-------:|-----:|-----:|")
    for lid, s in report["layers"].items():
        p = s["percent"]
        pstr = f"{p:.1f}%" if p is not None else "N/A"
        lines.append(f"| {lid} | {s['name']} | {s['items']} | {s['missed']} | {pstr} | {grade(p)} |")
    lines.append("")

    gaps = report["gaps"]
    lines.append(f"## 缺口清单（共 {len(gaps)} 项）")
    lines.append("")
    if not gaps:
        lines.append("> 未发现缺口。")
    else:
        lines.append("> 按权重倒序（`!!!` = 关键, `!!` = 重要, `!` = 一般）")
        lines.append("")
        for g in gaps:
            tag = "!!!" if g["weight"] >= 3 else ("!!" if g["weight"] == 2 else "!")
            lines.append(f"### {tag} [{g['id']}] {g['title']}")
            lines.append("")
            lines.append(f"- **层**: {g['layer']} — {g['layer_name']}")
            lines.append(f"- **权重**: {g['weight']}")
            lines.append(f"- **回答**: `{g['answer']}`")
            lines.append(f"- **根因**: {g['rationale']}")
            lines.append(f"- **建议**: {g['mitigation']}")
            lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 答案快照")
    lines.append("")
    lines.append("<details><summary>展开查看所有答案</summary>")
    lines.append("")
    lines.append("| ID | 回答 |")
    lines.append("|----|------|")
    for layer, item in iter_items(data):
        iid = item.get("id")
        ans = answers.get(iid, "skip")
        lines.append(f"| {iid} | {ans} |")
    lines.append("")
    lines.append("</details>")
    return "\n".join(lines)


# ---------- 入口 ----------

def main() -> int:
    ap = argparse.ArgumentParser(description="LLM 应用安全查漏工具")
    ap.add_argument("--non-interactive", action="store_true", help="仅打印清单，不问答")
    ap.add_argument("--answers", type=str, default=None, help="从 JSON 读取答案（id -> yes/no/na/skip）")
    ap.add_argument("--layer", type=str, default=None, help="只检查某一层，如 L3")
    ap.add_argument("--output", type=str, default=None, help="Markdown 报告输出路径")
    ap.add_argument("--json-output", type=str, default=None, help="JSON 报告输出路径")
    args = ap.parse_args()

    data = load_checklist()

    # 非交互：只打印清单
    if args.non_interactive and not args.answers:
        for layer, item in iter_items(data, args.layer):
            print(f"[{layer['id']}] [{item['id']}] (w={item.get('weight',1)}) {item['title']}")
            print(f"     ? {item.get('question')}")
        return 0

    # 读答案 or 交互问答
    if args.answers:
        with open(args.answers, "r", encoding="utf-8") as f:
            answers = json.load(f)
    else:
        answers = interactive_audit(data, args.layer)

    report = compute_scores(data, answers)
    print_report(report)

    if args.output:
        md = render_markdown(report, data, answers)
        Path(args.output).write_text(md, encoding="utf-8")
        print(f"\n[+] Markdown 报告已写入: {args.output}")

    if args.json_output:
        Path(args.json_output).write_text(
            json.dumps({"answers": answers, "report": report}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[+] JSON 报告已写入: {args.json_output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
