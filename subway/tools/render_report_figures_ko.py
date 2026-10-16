"""Render Korean report figures from frozen CSVs; no fitting or inference.

Run from any directory: python subway/tools/render_report_figures_ko.py
Requires Pillow and an installed Korean font. Canonical files are read only.
"""

import csv
import hashlib
import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from PIL.PngImagePlugin import PngInfo


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "subway/results/report_figures"
FONT_CANDIDATES = (
    Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts/malgun.ttf",
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
    Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
    Path("/Library/Fonts/AppleGothic.ttf"),
)
CONFIRMATORY = {
    "source": "subway/results/models/confirmatory_test_family.csv",
    "output": "confirmatory_effects_ko.png",
    "key": "hypothesis",
    "rows": (
        ("h1_hot_senior_differential", "폭염: 연령별 반응 차이"),
        ("h1_cold_senior_differential", "한파: 연령별 반응 차이"),
        ("h2_hot_daytime_amplification", "폭염 × 10~16시: 추가 증폭"),
        ("h2_cold_daytime_amplification", "한파 × 10~16시: 추가 증폭"),
    ),
    "title": "극한기온에서 고령자와 비고령자의 지하철 이용 반응 차이",
    "axis": "고령자-비고령자 상대 이용변화 차이 (%, 95% 신뢰구간)",
    "result": "Holm 보정 후 4개 검정 모두 지지되지 않음",
    "notes": (
        "점: 추정치 · 가로선: 개별 95% 신뢰구간 · 4개 검정에 Holm 보정 적용",
        "지지되지 않음은 효과가 0임을 입증하지 않음 · 상대 이용반응의 연관이며 인과효과가 아님",
    ),
    "limits": (-12, 8),
    "ticks": (-12, -8, -4, 0, 4, 8),
}
SPATIAL = {
    "source": "subway/results/models/spatial_moderation_primary.csv",
    "output": "spatial_moderation_effects_ko.png",
    "key": "term",
    "rows": (
        ("hot_x_z_senior_population_share", "폭염 × 고령인구비중"),
        ("cold_x_z_senior_population_share", "한파 × 고령인구비중"),
        ("hot_x_z_shelters_per_10k", "폭염 × 쉼터 수/1만 명"),
        ("cold_x_z_shelters_per_10k", "한파 × 쉼터 수/1만 명"),
    ),
    "title": "지역 특성에 따른 극한기온 지하철 이용 반응의 차이",
    "axis": "지역 특성 1표준편차 증가당 고령/비고령 상대 승차반응 변화 (95% 신뢰구간)",
    "result": "Holm 보정 후 유의: 한파 × 고령인구비중",
    "notes": (
        "점: 추정치 · 가로선: 개별 95% 신뢰구간 · 4개 검정에 Holm 보정 적용",
        "역별 가중 지역 맥락의 연관이며 인과효과가 아님 · 변화는 승차 로그비율 계수",
    ),
    "limits": (-0.012, 0.012),
    "ticks": (-0.012, -0.008, -0.004, 0, 0.004, 0.008, 0.012),
}


def load_points(config):
    """Select by key, preserving source values and recorded Holm decisions."""
    source = ROOT / config["source"]
    with source.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    indexed = {row[config["key"]]: row for row in rows}
    if len(rows) != 4 or len(indexed) != 4 or set(indexed) != {key for key, _ in config["rows"]}:
        raise ValueError(f"Expected exactly four unique primary targets: {source}")
    points = []
    for key, label in config["rows"]:
        row = indexed[key]
        if config["key"] == "hypothesis":
            # Same display conversion as the approved Stage 3B figure.
            beta = float(row["relative_percent"])
            low = (float(row["irr_ci95_low"]) - 1) * 100
            high = (float(row["irr_ci95_high"]) - 1) * 100
            expected_reject = "False"
            if row["event"] != "boarding" or row["threshold"] != "p90_p10":
                raise ValueError("Expected frozen Stage 3B boarding primary")
        else:
            beta, low, high = (float(row[field]) for field in ("beta", "ci95_low", "ci95_high"))
            expected_reject = "True" if key == "cold_x_z_senior_population_share" else "False"
            if row["threshold"] != "p90/p10" or row["inference_status"] != "ESTIMABLE":
                raise ValueError("Expected estimable frozen Stage 3C primary")
        if row["holm_reject"] != expected_reject:
            raise ValueError("Recorded Holm decision differs from approved figure note")
        if not all(math.isfinite(value) for value in (beta, low, high)) or not low <= beta <= high:
            raise ValueError("Invalid displayed estimate or CI")
        if low < config["limits"][0] or high > config["limits"][1]:
            raise ValueError("Display limits would clip a confidence interval")
        points.append((label, beta, low, high, expected_reject == "True"))
    return source, points


def render(config, font_path):
    source, points = load_points(config)
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    width, height = 2400, 1480
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    ink, blue, muted = "#17212b", "#1b5278", "#606d79"
    fonts = {size: ImageFont.truetype(str(font_path), size) for size in (38, 42, 46, 50, 62)}

    def text(x, y, value, size=46, fill=ink, anchor="mm"):
        box = draw.textbbox((x, y), value, font=fonts[size], anchor=anchor)
        if box[0] < 25 or box[1] < 15 or box[2] > width - 25 or box[3] > height - 15:
            raise ValueError(f"Text exceeds figure bounds: {value}")
        draw.text((x, y), value, font=fonts[size], fill=fill, anchor=anchor)

    text(width / 2, 90, config["title"], 62)
    text(width / 2, 185, config["result"], 50, blue)
    left, right, top, bottom = 890, 2270, 295, 1000
    lo, hi = config["limits"]

    def x(value):
        return left + (value - lo) / (hi - lo) * (right - left)

    for tick in config["ticks"]:
        position = x(tick)
        if tick != 0:
            draw.line((position, top, position, bottom), fill="#e4e8eb", width=2)
        label = f"{tick:g}" if config["key"] == "hypothesis" or tick == 0 else f"{tick:.3f}"
        text(position, bottom + 50, label, 42)
    for y in range(top, bottom, 24):
        draw.line((x(0), y, x(0), min(y + 13, bottom)), fill=ink, width=4)
    draw.line((left, bottom, right, bottom), fill=muted, width=2)
    for index, (label, beta, low, high, significant) in enumerate(points):
        y = 385 + index * 165
        color = blue if significant or config["key"] == "hypothesis" else muted
        text(left - 55, y, label, 46, ink, "rm")
        draw.line((x(low), y, x(high), y), fill=color, width=6)
        for endpoint in (low, high):
            draw.line((x(endpoint), y - 17, x(endpoint), y + 17), fill=color, width=4)
        draw.ellipse((x(beta) - 12, y - 12, x(beta) + 12, y + 12), fill=color)
    text(width / 2, 1130, config["axis"], 42)
    for index, note in enumerate(config["notes"]):
        text(width / 2, 1240 + index * 65, note, 38, muted)
    text(width / 2, 1400, "자료: " + source.name + " · 2024년 서울 · 승차 · p90/p10", 38, muted)
    metadata = PngInfo()
    metadata.add_text("Source", config["source"])
    metadata.add_text("SourceSHA256", source_hash)
    metadata.add_text("KoreanFont", font_path.name)
    metadata.add_text("Description", config["title"] + " / " + config["axis"] + " / " + config["result"])
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / config["output"]
    image.save(target, dpi=(360, 360), pnginfo=metadata)
    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("Canonical source changed during rendering")
    print(f"Rendered {target.relative_to(ROOT)}; source SHA256={source_hash}; font={font_path.name}")


def main():
    font_path = next((path for path in FONT_CANDIDATES if path.is_file()), None)
    if font_path is None:
        raise RuntimeError("No installed Korean font: install Malgun Gothic, Noto Sans CJK KR or AppleGothic")
    render(CONFIRMATORY, font_path)
    render(SPATIAL, font_path)


if __name__ == "__main__":
    main()
