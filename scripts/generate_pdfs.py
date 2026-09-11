from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "policies"
FONT = Path("C:/Windows/Fonts/NotoSansSC-VF.ttf")


def build_pdf(filename: str, title: str, sections: list[tuple[str, str]], table_data: list[list[str]]) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    pdfmetrics.registerFont(TTFont("NotoSansSC", str(FONT)))
    path = OUTPUT / filename
    doc = SimpleDocTemplate(
        str(path), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleCN", parent=styles["Title"], fontName="NotoSansSC", fontSize=18, leading=24, textColor=colors.HexColor("#17324D"), spaceAfter=10)
    heading_style = ParagraphStyle("HeadingCN", parent=styles["Heading2"], fontName="NotoSansSC", fontSize=12, leading=17, textColor=colors.HexColor("#236B8E"), spaceBefore=8, spaceAfter=4)
    body_style = ParagraphStyle("BodyCN", parent=styles["BodyText"], fontName="NotoSansSC", fontSize=9.5, leading=15, spaceAfter=5)
    cell_style = ParagraphStyle("CellCN", parent=body_style, fontSize=8.5, leading=12)
    story = [Paragraph(title, title_style), Paragraph("星河科技有限公司 · 财务制度模拟资料 · 2026 年版", body_style), Spacer(1, 4)]
    for heading, body in sections:
        story.extend([Paragraph(heading, heading_style), Paragraph(body, body_style)])
    table = Table([[Paragraph(str(cell), cell_style) for cell in row] for row in table_data], repeatRows=1, colWidths=[38 * mm, 42 * mm, 42 * mm, 42 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCEAF2")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#17324D")),
        ("FONTNAME", (0, 0), (-1, -1), "NotoSansSC"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9BB7C7")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([Spacer(1, 6), table, Spacer(1, 12), Paragraph("说明：本文件为项目演示用模拟制度，不代表真实企业财务政策。", body_style)])
    doc.build(story)
    print(path)


build_pdf(
    "travel_policy.pdf",
    "差旅费用报销制度",
    [
        ("一、住宿标准", "员工因公出差可按职级和城市等级报销住宿费用。实际住宿金额低于限额时按实际金额报销，超过限额部分原则上由个人承担。"),
        ("二、交通与餐补", "城市间交通应选择经济、合理的交通方式。出差期间可按照制度标准领取餐补，不得重复报销已由接待方承担的餐费。"),
        ("三、审核原则", "报销申请需要关联出差事由、日期和发票。信息缺失时，财务人员可以退回补充材料。"),
    ],
    [["职级", "住宿限额（普通城市）", "住宿限额（一线城市）", "每日餐补"], ["P1", "600 元", "720 元", "150 元"], ["P2", "450 元", "540 元", "120 元"], ["P3", "350 元", "420 元", "100 元"]],
)

build_pdf(
    "reimbursement_rules.pdf",
    "报销额度与审核规则",
    [
        ("一、额度计算", "报销额度取实际发生金额与对应制度限额中的较小值。城市等级为一线城市时，住宿和交通限额按 1.2 倍计算；三线城市按 0.85 倍计算。"),
        ("二、费用分类", "系统将费用分为住宿、交通和餐补。无法匹配分类的费用不会被自动核准，需要人工核对。"),
        ("三、人工审核", "自动计算结果仅供申请人参考，不代表最终审批结论。超过 2,000 元或材料不完整的申请必须进入人工审核。"),
    ],
    [["费用类型", "P1", "P2", "P3"], ["住宿", "600 元/晚", "450 元/晚", "350 元/晚"], ["交通", "300 元/日", "250 元/日", "200 元/日"], ["餐补", "150 元/日", "120 元/日", "100 元/日"]],
)
