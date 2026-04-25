"""Extract desk-selection signals from free-form Russian text."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Steps used for disambiguation (e.g. 178 = height vs budget)
ACTIVE_STEP_HEIGHT = "height"
ACTIVE_STEP_BUDGET = "budget"
ACTIVE_STEP_MONITORS = "monitors"
ACTIVE_STEP_SIZE = "size"

_DISMISSAL_RE = re.compile(
    r"(не\s*знаю|без\s*разницы|пока\s*не\s*решил|пропустить|неважно|любой|любая|"
    r"без\s*ограничени|без\s*ограничений)",
    re.I,
)

_STABILITY_RE = re.compile(
    r"(не\s*шатал|шатал|устойчивост|тяжел[ыйая]\s*сетап|кронштейн|монитор\s*на\s*кронштейне)",
    re.I,
)

_SCENARIO_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"для\s+игр|тяжел[ыйогое]\s*сетап|гейминг", re.I), "gaming"),
    (re.compile(r"для\s+офиса|офисн", re.I), "office"),
    (re.compile(r"для\s+уч[её]бы|учеб", re.I), "study"),
    (re.compile(r"дома|домашн|работ[аы]\s+дома|home\s*office", re.I), "home_office"),
]

_NUM_WORD_MONITORS: dict[str, int] = {
    "один": 1,
    "одна": 1,
    "два": 2,
    "две": 2,
    "три": 3,
    "четыре": 4,
}


def _normalize_money_text(text: str) -> str:
    return re.sub(r"\s+", "", text.lower())


def parse_budget_from_text(text: str) -> tuple[int | None, int | None, int | None]:
    """
    Returns (budget_min, budget_max, budget_exact).
    budget_exact set when a single clear anchor amount is parsed.
    """
    lowered = text.lower()
    normalized = _normalize_money_text(text)

    range_patterns = [
        re.compile(
            r"от\s*(\d[\d\s]{2,7})\s*до\s*(\d[\d\s]{2,7})\s*(?:руб|₽|р\.|k|к|тыс|тысяч)?",
            re.I,
        ),
        re.compile(r"от\s*(\d{1,3})\s*к?\s*до\s*(\d{1,3})\s*к", re.I),
    ]
    for rx in range_patterns:
        m = rx.search(lowered)
        if m:
            a = int(re.sub(r"\s+", "", m.group(1)))
            b = int(re.sub(r"\s+", "", m.group(2)))
            if "к" in m.group(0).lower() or max(a, b) <= 999:
                if a < 1000:
                    a *= 1000
                if b < 1000:
                    b *= 1000
            lo, hi = (a, b) if a <= b else (b, a)
            if 5_000 <= hi <= 2_000_000:
                return lo, hi, None

    compact = re.search(r"(\d{1,3})[-–](\d{1,3})\s*к\b", normalized)
    if compact:
        lo = int(compact.group(1)) * 1000
        hi = int(compact.group(2)) * 1000
        return lo, hi, None

    spaced = re.search(
        r"(\d[\d\s]{3,8})\s*[-–]\s*(\d[\d\s]{3,8})\s*(?:руб|₽|р\.|k)?",
        lowered,
    )
    if spaced:
        lo = int(re.sub(r"\s+", "", spaced.group(1)))
        hi = int(re.sub(r"\s+", "", spaced.group(2)))
        if 5_000 <= hi <= 2_000_000:
            return lo, hi, None

    upto = re.search(
        r"(?:до|не\s*более)\s*(\d[\d\s]{2,8})\s*(?:руб|₽|р\.|k|к|тыс|тысяч)?",
        lowered,
    )
    if upto:
        val_raw = re.sub(r"\s+", "", upto.group(1))
        val = int(val_raw)
        fragment = upto.group(0).lower()
        if "к" in fragment or "тыс" in fragment:
            if val < 1000:
                val *= 1000
        if 1_000 <= val <= 2_000_000:
            return None, val, val

    upto_k = re.search(r"до\s*(\d{1,3})\s*к", normalized)
    if upto_k:
        v = int(upto_k.group(1)) * 1000
        return None, v, v

    fromm = re.search(r"от\s*(\d[\d\s]{2,8})\s*(?:руб|₽|р\.|k|к|тыс)?", lowered)
    if fromm:
        tail = lowered[fromm.end() : fromm.end() + 12]
        if "до" not in tail:
            val_raw = re.sub(r"\s+", "", fromm.group(1))
            val = int(val_raw)
            frag = fromm.group(0).lower()
            if "к" in frag or val < 3000:
                if val < 1000:
                    val *= 1000
            if 5_000 <= val <= 2_000_000:
                return val, None, val

    approx = re.search(r"(?:примерно|около)\s*(\d{1,3})\s*к", normalized)
    if approx:
        v = int(approx.group(1)) * 1000
        return None, v, v

    thousands = re.search(
        r"(?:бюджет|budget)?\D{0,6}(\d{1,3})\s*(?:к|тыс(?:яч)?)\b",
        lowered,
    )
    if thousands:
        v = int(thousands.group(1)) * 1000
        if 5_000 <= v <= 2_000_000:
            return None, v, v

    explicit = re.search(
        r"(?:бюджет|budget|у\s*меня)\D{0,10}(\d[\d\s]{4,8})\b",
        lowered,
    )
    if explicit:
        v = int(re.sub(r"\s+", "", explicit.group(1)))
        if 10_000 <= v <= 2_000_000:
            return None, v, v

    rub = re.search(r"\b(\d[\d\s]{4,8})\s*(?:руб|₽)", lowered)
    if rub:
        v = int(re.sub(r"\s+", "", rub.group(1)))
        if 10_000 <= v <= 2_000_000:
            return None, v, v

    loose = re.search(r"\b(\d{5,6})\b", normalized)
    if loose:
        v = int(loose.group(1))
        if 10_000 <= v <= 999_999:
            return None, v, v

    plain_k = re.search(r"\b(\d{2,3})к\b", normalized)
    if plain_k:
        v = int(plain_k.group(1)) * 1000
        return None, v, v

    return None, None, None


def parse_height_cm(text: str, *, active_step: str | None) -> int | None:
    lowered = text.lower()
    m = re.search(r"(?:рост|height)\D{0,12}(\d{2,3})\s*(?:см|cm)?", lowered)
    if m:
        h = int(m.group(1))
        if 120 <= h <= 230:
            return h

    if active_step == ACTIVE_STEP_HEIGHT:
        solo = re.match(r"^\s*(\d{2,3})\s*$", text.strip())
        if solo:
            h = int(solo.group(1))
            if 120 <= h <= 230:
                return h

    three = re.search(r"\b(1[4-9]\d|20\d)\b", text)
    if not three:
        return None
    value = int(three.group(1))
    if not (120 <= value <= 230):
        return None
    if active_step == ACTIVE_STEP_BUDGET:
        return None
    if active_step == ACTIVE_STEP_HEIGHT:
        return value
    if "рост" in lowered or re.search(r"\d{2,3}\s*см", lowered):
        return value
    b_min, b_max, _ = parse_budget_from_text(text)
    if b_min is not None or b_max is not None:
        return None
    return value


def parse_monitors_with_step(text: str, *, active_step: str | None) -> int | None:
    if active_step == ACTIVE_STEP_MONITORS:
        solo = re.match(r"^\s*(\d)\s*$", text.strip())
        if solo:
            return int(solo.group(1))
        low = text.strip().lower()
        for word, n in _NUM_WORD_MONITORS.items():
            if low == word or low == f"{word}.":
                return n
    lowered = text.lower()
    for word, n in _NUM_WORD_MONITORS.items():
        if f"{word} монит" in lowered:
            return n
    m = re.search(r"(\d+)\s*монитор", lowered)
    if m:
        return int(m.group(1))
    return None


def parse_has_pc_on_table(text: str) -> bool | None:
    lowered = text.lower()
    if any(
        t in lowered
        for t in (
            "только ноутбук",
            "только монитор",
            "без системн",
            "нет системн",
            "системник не",
            "блок не",
        )
    ):
        return False
    if any(
        t in lowered
        for t in (
            "системник на стол",
            "системный блок",
            "системник будет",
            "пк на стол",
            "блок на стол",
        )
    ):
        return True
    return None


def parse_desktop_size_cm(text: str) -> tuple[int | None, int | None]:
    lowered = text.lower()
    for pattern in (
        r"(\d{2,3})\s*[xх×]\s*(\d{2,3})",
        r"(\d{2,3})\s+на\s+(\d{2,3})",
    ):
        m = re.search(pattern, lowered)
        if m:
            w = int(m.group(1))
            d = int(m.group(2))
            if 60 <= w <= 300 and 40 <= d <= 120:
                return w, d
    m = re.search(r"стол\s*(\d{2,3})\b", lowered)
    if m:
        w = int(m.group(1))
        if 60 <= w <= 300:
            return w, None
    return None, None


def parse_max_width_hint(text: str) -> int | None:
    lowered = text.lower()
    m = re.search(
        r"(?:места\s*максимум|максимум|не\s*шире|до\s*ширины|ширин\w*)\D{0,8}(\d{2,3})\s*(?:см)?",
        lowered,
    )
    if m:
        v = int(m.group(1))
        if 60 <= v <= 300:
            return v
    m2 = re.search(r"только\s*(\d{2,3})\s*(?:см)?", lowered)
    if m2:
        v = int(m2.group(1))
        if 60 <= v <= 250:
            return v
    return None


def parse_internal_scenario(text: str) -> str | None:
    lowered = text.lower()
    for rx, key in _SCENARIO_PATTERNS:
        if rx.search(lowered):
            return key
    return None


def is_dismissal_reply(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False
    return bool(_DISMISSAL_RE.search(t))


def has_stability_priority(text: str) -> bool:
    return bool(_STABILITY_RE.search(text or ""))


@dataclass
class ParsedSignals:
    height_cm: int | None = None
    budget_min: int | None = None
    budget_max: int | None = None
    budget_exact: int | None = None
    monitors_count: int | None = None
    has_pc_on_table: bool | None = None
    preferred_width_cm: int | None = None
    preferred_depth_cm: int | None = None
    max_width_cm: int | None = None
    max_depth_cm: int | None = None
    no_size_limit: bool = False
    internal_scenario: str | None = None
    heavy_setup: bool = False


def parse_signals(text: str, *, active_step: str | None = None) -> ParsedSignals:
    raw = (text or "").strip()
    signals = ParsedSignals()
    if not raw:
        return signals

    lowered = raw.lower()

    if "без огранич" in lowered or "ограничений нет" in lowered:
        signals.no_size_limit = True

    signals.heavy_setup = has_stability_priority(raw)

    b_min, b_max, b_exact = parse_budget_from_text(raw)
    signals.budget_min = b_min
    signals.budget_max = b_max
    signals.budget_exact = b_exact

    if active_step == ACTIVE_STEP_BUDGET:
        solo = re.match(r"^\s*(\d{4,6})\s*$", raw)
        if solo:
            v = int(solo.group(1))
            if v >= 3_000:
                signals.budget_min = None
                signals.budget_max = v
                signals.budget_exact = v

    h = parse_height_cm(raw, active_step=active_step)
    if h is not None:
        signals.height_cm = h

    signals.monitors_count = parse_monitors_with_step(raw, active_step=active_step)
    signals.has_pc_on_table = parse_has_pc_on_table(raw)

    w, d = parse_desktop_size_cm(raw)
    if w is not None:
        signals.preferred_width_cm = w
    if d is not None:
        signals.preferred_depth_cm = d

    mw = parse_max_width_hint(raw)
    if mw is not None:
        signals.max_width_cm = mw

    sc = parse_internal_scenario(raw)
    if sc is not None:
        signals.internal_scenario = sc

    return signals