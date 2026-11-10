"""Rule-based advertisement filter."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

LB = r"(?:^|[^฀-๿a-z0-9])"

MONEY = r"[\d๐-๙][\d๐-๙,.]*\s*(?:บาท|฿|บ\.|\.-)"

PRICE_PATTERNS: list[tuple[str, str]] = [
    ("price_number_baht", r"[\d๐-๙][\d๐-๙,.]*\s*(?:บาท|บ\.)"),
    ("price_baht_symbol", r"฿\s*[\d๐-๙]"),
    ("price_word_number", r"ราคา\s*(?:เพียง|แค่|พิเศษ|ส่ง|ปลีก)?\s*[\d๐-๙]"),
    ("price_number_dash", r"[\d๐-๙][\d๐-๙,]*\s*(?:\.-|฿)"),
    ("price_baht_word", r"บาท"),
]

CONTACT_PATTERNS: list[tuple[str, str]] = [
    ("contact_line_id", r"(?:line|ไลน์)\s*(?:id|ไอดี|@|:)|ไอดีไลน์|แอด\s*(?:line|ไลน์)|add\s*line"),
    ("contact_line_at", r"line\.me/|line\s*@\s*[a-z0-9._-]{3,}|@[a-z0-9._-]{3,}\s*\(\s*(?:มี|ใส่)\s*@"),
    ("contact_phone", r"(?<![\d])0[689][\d\-. ]{7,12}(?![\d])|(?<![\d])0\d{1,2}[-. ]\d{3}[-. ]\d{4}(?![\d])"),
    ("contact_phone_word", r"โทร\.?\s*[\d๐-๙]|เบอร์โทร|ติดต่อ\s*โทร"),
    ("contact_inbox", r"inbox|\bdm\b|กล่องข้อความ|ไดเรก|direct\s*message"),
    ("contact_tak", r"ทักแชท|ทักมา|ทักได้|ทักเลย|ทักไลน์|ทักอิน|ทัก\s*line|ทัก\s*ib|\bทัก\b"),
    ("contact_order_channel", r"สั่งซื้อได้ที่|สั่งได้ที่|สอบถามได้ที่|ช่องทางการสั่งซื้อ|ช่องทางติดต่อ"),
]

CTA_PATTERNS: list[tuple[str, str]] = [
    ("cta_ask_interest", r"สนใจ(?=\s*(?:สอบถาม|ทัก|สั่ง|ติดต่อ|inbox|dm))|สอบถามเพิ่มเติม"),
    ("cta_free_shipping", r"จัดส่งฟรี|ส่งฟรี|ฟรีค่าจัดส่ง|ฟรีค่าส่ง|ส่งฟรีทั่วประเทศ"),
    ("cta_promotion", r"โปรโมชั่น|โปรโมชัน|โปรโมท|โปรพิเศษ|ราคาโปร|โปรแรง"),
    ("cta_preorder", r"พรีออเดอร์|พรีออร์เดอร์|พรี\s*order|pre-?order|จองล่วงหน้า"),
    ("cta_cod", r"เก็บเงินปลายทาง|เก็บปลายทาง|\bcod\b|ปลายทางได้"),
    ("cta_buy_now", r"กดสั่งซื้อ|กดสั่ง|กดซื้อ|สั่งซื้อเลย|โทรสั่งเลย|รีบสั่ง|รีบซื้อ"
                    r"|ด่วน\s*ๆ?\s*จำนวนจำกัด" + f"|{LB}" + r"(?:ซื้อเลย|สั่งเลย|ช้อปเลย|สั่งด่วน)"),
    ("cta_chat", r"ทักแชท|แชทเลย" + f"|{LB}" + r"แชทมา"),
    ("cta_reseller", r"รับตัวแทน|หาตัวแทน|ตัวแทนจำหน่าย|รับสมัครตัวแทน|สมัครตัวแทน|แม่ทีม"),
    ("cta_wholesale", r"ราคาส่ง|ราคาปลีก|ขายส่ง|ขายปลีก|ปลีก-?ส่ง|ราคาโรงงาน"),
    ("cta_stock", r"ของแท้\s*100|สินค้าพร้อมส่ง|พร้อมส่ง|มีของพร้อมส่ง|ของหมดเร็ว"),
    ("cta_discount", f"เหลือ[ง]?เพียง\\s*{MONEY}|ลดเหลือ\\s*{MONEY}|จากปกติ\\s*{MONEY}"
                     f"|จากราคาปกติ|ราคาปกติ\\s*{MONEY}|ปกติราคา\\s*{MONEY}"
                     r"|ลดทันที|คูปองส่วนลด|รับส่วนลด|ส่วนลดพิเศษ|ส่วนลด\s*[\d๐-๙]"
                     r"|ซื้อ\s*1\s*แถม\s*1|ลด\s*[\d๐-๙]+\s*%"),
    ("cta_campaign", r"ร่วมสนุก|ร่วมกิจกรรม|ลุ้นรับ|ลุ้นโชค|ชิงโชค|แจกโชค|แจกรางวัล|ผู้โชคดี|กติกา"),
    ("cta_test_drive", r"(?:เชิญ|ชวน|สนใจ|มา|ร่วม)\s*(?:สัมผัสและ)?ทดลอง(?:ขับ|สินค้า)"
                       r"|ทดลอง(?:ขับ|สินค้า)ได้ที่(?!ไหน|ใด)|นัด(?:หมาย)?ทดลองขับ"
                       r"|จองทดลองขับ|เชิญทดลอง"),
]

RULE_GROUPS: dict[str, list[tuple[str, str]]] = {
    "price": PRICE_PATTERNS,
    "contact": CONTACT_PATTERNS,
    "cta": CTA_PATTERNS,
}

GROUP_PRIORITY = ["cta", "contact", "price"]

_MECHANIC = r"(?:กด\s*)?(?:แชร์|share|ไลค์|like|แท็ก|tag|คอมเมนต์|เม้นท์|เม้นต์|โพสต์รูป)"
_PRIZE = r"(?:ลุ้นรับ|ลุ้นรางวัล|ชิงโชค|รับรางวัล|ของรางวัล|แจกฟรี|แจกบัตร|ร่วมสนุก|รับฟรี)"

STRONG_PATTERNS: list[tuple[str, str]] = [
    ("strong_discount", f"เหลือ[ง]?เพียง\\s*{MONEY}|ลดเหลือ\\s*{MONEY}"
                        f"|จากราคาปกติ\\s*{MONEY}|ราคาปกติ\\s*{MONEY}|จากปกติ\\s*{MONEY}"),
    ("strong_test_drive", r"(?:เชิญ|ชวน|สนใจ|ร่วมสัมผัสและ)\s*ทดลองขับ|ทดลองขับได้ที่(?!ไหน|ใด)"),
    ("strong_campaign_result",
     r"ประกาศ(?:ราย)?(?:ชื่อ|ผล)[^\n]{0,25}ผู้(?:โชคดี|ชนะ|ได้รับ)|รายชื่อผู้โชคดี|ผู้โชคดีที่ได้รับ"),
    ("strong_campaign_rules",
     f"กติกา(?:การร่วมสนุก|ร่วมสนุก|ง่ายๆ|สนุกๆ|การเข้าร่วม|กิจกรรม)|กติกา[^\\n]{{0,60}}{_MECHANIC}"),
    ("strong_campaign_mechanic",
     f"{_PRIZE}[^\\n]{{0,120}}{_MECHANIC}|{_MECHANIC}[^\\n]{{0,80}}{_PRIZE}"),
]

EXCLUDE_PATTERNS: list[tuple[str, str]] = [
    ("veto_buyer_request", r"ขอรายละเอียด|ขอราคา|รบกวนขอ|ใครมีรายละเอียด|ขอข้อมูลเพิ่ม"
                           r"|ขออนุญาต[ิ]?สอบถาม|ขอสอบถาม|รบกวนสอบถาม"
                           r"|สงสัยว่า|อยากทราบว่า|ไม่ทราบว่า"),
    ("veto_scam_warning", r"โดนโกง|คนโกง|โกงเงิน|มิจฉาชีพ|หลอกลวง|เตือนภัย"),
]

MIN_GROUPS = 2

INPUTS = [ROOT / "data" / f"{split}.csv" for split in ("train", "validation", "test")]
OUTDIR = ROOT / "data" / "filtered"
TEXT_COL = "texts"
ENCODING = "utf-8-sig"

COMPILED: dict[str, list[tuple[str, re.Pattern]]] = {
    group: [(name, re.compile(pat, re.IGNORECASE)) for name, pat in patterns]
    for group, patterns in RULE_GROUPS.items()
}
COMPILED_EXCLUDE = [(name, re.compile(pat, re.IGNORECASE)) for name, pat in EXCLUDE_PATTERNS]
COMPILED_STRONG = [(name, re.compile(pat, re.IGNORECASE)) for name, pat in STRONG_PATTERNS]
_PRIORITY = {g: i for i, g in enumerate(GROUP_PRIORITY)}


def match_rules(text: str) -> tuple[list[str], list[str]]:
    if not isinstance(text, str) or not text.strip():
        return [], []
    spans = [
        (m.start(), m.end(), _PRIORITY[group], group, name)
        for group, rules in COMPILED.items()
        for name, rx in rules
        for m in rx.finditer(text)
    ]
    spans.sort(key=lambda s: (s[0], s[2], -(s[1] - s[0])))
    accepted: list[tuple] = []
    for s in spans:
        if any(s[0] < a[1] and a[0] < s[1] and a[3] != s[3] for a in accepted):
            continue
        accepted.append(s)
    hit_groups = [g for g in RULE_GROUPS if any(a[3] == g for a in accepted)]
    hit_rules = list(dict.fromkeys(a[4] for a in accepted))
    return hit_rules, hit_groups


def _match_list(text: str, compiled: list[tuple[str, re.Pattern]]) -> list[str]:
    if not isinstance(text, str) or not text.strip():
        return []
    return [name for name, rx in compiled if rx.search(text)]


def annotate_frame(df: pd.DataFrame, text_col: str = TEXT_COL,
                   min_groups: int = MIN_GROUPS) -> pd.DataFrame:
    """Add the rule columns and is_ads to a copy of df."""
    results = [match_rules(t) for t in df[text_col]]
    out = df.copy()
    out["matched_rules"] = ["; ".join(r) for r, _ in results]
    out["matched_groups"] = ["|".join(g) for _, g in results]
    out["n_groups"] = [len(g) for _, g in results]
    out["strong_rules"] = ["; ".join(_match_list(t, COMPILED_STRONG)) for t in df[text_col]]
    out["excluded_by"] = ["; ".join(_match_list(t, COMPILED_EXCLUDE)) for t in df[text_col]]
    out["is_ads"] = (((out["n_groups"] >= min_groups) | (out["strong_rules"] != ""))
                     & (out["excluded_by"] == ""))
    return out


def process_file(path: Path, outdir: Path) -> tuple[int, int]:
    df = pd.read_csv(path, encoding=ENCODING)
    if TEXT_COL not in df.columns:
        sys.exit(f"{path}: no column '{TEXT_COL}'")
    tagged = annotate_frame(df)
    cols = list(df.columns)
    ads = tagged.loc[tagged["is_ads"], cols + ["matched_rules", "matched_groups", "n_groups",
                                               "strong_rules"]]
    ads = ads.reset_index().rename(columns={"index": "row_index"})
    tagged.loc[~tagged["is_ads"], cols].to_csv(outdir / f"{path.stem}_clean.csv", index=False,
                                               encoding=ENCODING)
    ads.to_csv(outdir / f"{path.stem}_ads.csv", index=False, encoding=ENCODING)
    return len(tagged), len(ads)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", nargs="+", type=Path, default=INPUTS)
    ap.add_argument("--outdir", type=Path, default=OUTDIR)
    args = ap.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    for path in args.input:
        process_file(path, args.outdir)


if __name__ == "__main__":
    main()
