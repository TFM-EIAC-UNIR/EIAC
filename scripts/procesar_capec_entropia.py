#!/usr/bin/env python3
"""Procesa datasets CAPEC y calcula entropía de columnas.

Entradas esperadas:
  CSV en datasets/CAPEC/, datasets/sintetico/ o datasets/SR-BH/
  También admite URL pública (p. ej. Google Sheets) mediante --input

Salidas generadas:
  datos/processed/capec_dataset.csv
  datos/results/entropia_columnas.csv
  datos/results/eiac_columnas.csv
  datos/results/eiac_tabla_latex.tex
  datos/results/eiac_reporte.pdf
  datos/results/eiac_comparacion_hn_eiac.pdf
  datos/results/eiac_comparacion_hn_eiac.tex
"""

from __future__ import annotations

import argparse
import math
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd


MISSING_TOKEN = "__MISSING__"
TOP_DISTRIBUTION_VALUES = 4
DEFAULT_INPUT = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vSgxiQy2LjIoK-6s7iUUuvoh6Xf0MgCNB-QKNA_i6m9DEydcIThAOzPDJRsEGaPf0ZZWwsIZMttasus/"
    "pub?output=csv"
)

MANDATORY_ANALYSIS_COLUMNS = [
    "ID",
    "Name",
    "Description",
    "Abstraction",
    "Status",
    "Likelihood Of Attack",
    "Typical Severity",
]


def count_wrapped_items(value: object) -> int:
    """Cuenta elementos codificados como ::item::item:: en CAPEC."""
    if pd.isna(value):
        return 0
    text = str(value).strip()
    if not text:
        return 0
    parts = [part.strip() for part in text.split("::") if part.strip()]
    return len(parts)


def count_pattern(value: object, pattern: str) -> int:
    if pd.isna(value):
        return 0
    return len(re.findall(pattern, str(value)))


def text_length(value: object) -> int:
    if pd.isna(value):
        return 0
    return len(str(value).strip())


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def add_timestamp_to_path(path: Path, timestamp: str) -> Path:
    return path.with_name(f"{path.stem}_{timestamp}{path.suffix}")


def prepare_values(values: pd.Series, include_missing: bool = True) -> pd.Series:
    prepared = values.fillna("").astype(str).str.strip()
    if include_missing:
        return prepared.mask(prepared == "", MISSING_TOKEN)
    return prepared[prepared != ""]


def shannon_entropy(values: pd.Series, include_missing: bool = False) -> tuple[float, int, int, str, int]:
    prepared = prepare_values(values, include_missing=include_missing)
    counts = prepared.value_counts(dropna=False)
    total = int(counts.sum())
    entropy = 0.0
    for count in counts:
        probability = count / total
        entropy -= probability * math.log2(probability)
    most_common_value = str(counts.index[0]) if len(counts) else ""
    most_common_frequency = int(counts.iloc[0]) if len(counts) else 0
    return entropy, int(len(counts)), total, most_common_value, most_common_frequency


def format_distribution(values: pd.Series, max_values: int = TOP_DISTRIBUTION_VALUES) -> str:
    counts = prepare_values(values, include_missing=False).value_counts(dropna=False)
    if counts.empty:
        return "Sin datos"

    parts = [f"{value} = {count}" for value, count in counts.head(max_values).items()]
    remaining = len(counts) - max_values
    if remaining > 0:
        parts.append(f"... + {remaining} valores")
    return "; ".join(parts)


def classify_relevance(eiac: float) -> str:
    if eiac >= 0.66:
        return "alta_relevancia"
    if eiac >= 0.33:
        return "relevancia_media"
    return "baja_relevancia"


def classify_column(column: str, unique_values: int, total_rows: int, normalized_entropy: float) -> str:
    unique_ratio = unique_values / total_rows if total_rows else 0
    if column.lower() == "id" or unique_ratio >= 0.98:
        return "identificador_o_texto_unico"
    if normalized_entropy >= 0.70:
        return "alta_variabilidad"
    if normalized_entropy >= 0.30:
        return "variabilidad_media"
    return "baja_variabilidad"


def classify_functional_column(
    column: str,
    unique_ratio: float,
    missing_ratio: float,
    normalized_entropy: float,
) -> str:
    column_lower = column.lower().strip()

    traceability_columns = {"id", "name"}
    descriptive_columns = {"description", "notes", "alternate terms"}
    analytic_columns = {
        "abstraction",
        "status",
        "likelihood of attack",
        "typical severity",
    }

    if column_lower in traceability_columns:
        return "trazabilidad"
    if column_lower in descriptive_columns:
        return "descriptiva_contextual"
    if column_lower in analytic_columns:
        return "analitica"
    if missing_ratio >= 0.50:
        return "bajo_aporte_por_datos_faltantes"
    if unique_ratio >= 0.98:
        return "posible_identificador_o_texto_unico"
    if normalized_entropy >= 0.70 and unique_ratio >= 0.50:
        return "candidata_a_limpieza_o_revision"
    if normalized_entropy < 0.30:
        return "bajo_aporte_por_baja_variabilidad"
    return "analitica_complementaria"


def format_relevance_label(relevance: str) -> str:
    return {
        "alta_relevancia": "Alta relevancia",
        "relevancia_media": "Relevancia media",
        "baja_relevancia": "Baja relevancia",
    }[relevance]


def format_functional_label(functional_classification: str) -> str:
    return {
        "analitica": "Analítica",
        "trazabilidad": "Trazabilidad",
        "descriptiva_contextual": "Descriptiva contextual",
        "bajo_aporte_por_datos_faltantes": "Bajo aporte por datos faltantes",
        "posible_identificador_o_texto_unico": "Posible identificador o texto único",
        "candidata_a_limpieza_o_revision": "Candidata a limpieza o revisión",
        "bajo_aporte_por_baja_variabilidad": "Bajo aporte por baja variabilidad",
        "analitica_complementaria": "Analítica complementaria",
    }[functional_classification]


def build_analysis_text(relevance: str, functional_classification: str) -> str:
    relevance_text = {
        "alta_relevancia": "Alta relevancia informativa",
        "relevancia_media": "Relevancia informativa media",
        "baja_relevancia": "Baja relevancia informativa",
    }[relevance]

    functional_text = {
        "analitica": "columna analítica para comparar registros",
        "trazabilidad": "columna de trazabilidad",
        "descriptiva_contextual": "columna descriptiva o contextual",
        "bajo_aporte_por_datos_faltantes": "requiere revisión por datos faltantes",
        "posible_identificador_o_texto_unico": "posible identificador o texto único",
        "candidata_a_limpieza_o_revision": "candidata a limpieza o revisión",
        "bajo_aporte_por_baja_variabilidad": "bajo aporte por baja variabilidad",
        "analitica_complementaria": "columna analítica complementaria",
    }[functional_classification]

    return f"{relevance_text}; {functional_text}."


def build_processed_dataset(source: str) -> pd.DataFrame:
    df = pd.read_csv(source, dtype=str, keep_default_na=False, index_col=False)
    df.columns = [column.strip().lstrip("'") for column in df.columns]

    processed = df.copy()

    if "Description" in processed.columns:
        processed["description_length_chars"] = processed["Description"].map(text_length)
    if "Notes" in processed.columns:
        processed["notes_length_chars"] = processed["Notes"].map(text_length)

    if "Alternate Terms" in processed.columns:
        processed["alternate_terms_count"] = processed["Alternate Terms"].map(count_wrapped_items)
    if "Related Attack Patterns" in processed.columns:
        processed["related_attack_patterns_count"] = processed["Related Attack Patterns"].map(
            lambda value: count_pattern(value, r"CAPEC ID:")
        )
    if "Execution Flow" in processed.columns:
        processed["execution_flow_steps_count"] = processed["Execution Flow"].map(
            lambda value: count_pattern(value, r"::STEP:")
        )
        processed["execution_flow_techniques_count"] = processed["Execution Flow"].map(
            lambda value: count_pattern(value, r":TECHNIQUE:")
        )
    if "Prerequisites" in processed.columns:
        processed["prerequisites_count"] = processed["Prerequisites"].map(count_wrapped_items)
    if "Skills Required" in processed.columns:
        processed["skills_required_count"] = processed["Skills Required"].map(
            lambda value: count_pattern(value, r"::SKILL:")
        )
    if "Resources Required" in processed.columns:
        processed["resources_required_count"] = processed["Resources Required"].map(count_wrapped_items)
    if "Indicators" in processed.columns:
        processed["indicators_count"] = processed["Indicators"].map(count_wrapped_items)
    if "Consequences" in processed.columns:
        processed["consequences_scope_count"] = processed["Consequences"].map(
            lambda value: count_pattern(value, r":SCOPE:")
        )
        processed["consequences_impact_count"] = processed["Consequences"].map(
            lambda value: count_pattern(value, r":TECHNICAL IMPACT:")
        )
    if "Mitigations" in processed.columns:
        processed["mitigations_count"] = processed["Mitigations"].map(count_wrapped_items)
    if "Example Instances" in processed.columns:
        processed["example_instances_count"] = processed["Example Instances"].map(count_wrapped_items)
    if "Related Weaknesses" in processed.columns:
        processed["related_weaknesses_count"] = processed["Related Weaknesses"].map(count_wrapped_items)
    if "Taxonomy Mappings" in processed.columns:
        processed["taxonomy_mappings_count"] = processed["Taxonomy Mappings"].map(
            lambda value: count_pattern(value, r"TAXONOMY NAME:")
        )

    return processed


def build_entropy_report(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    total_rows = len(df)
    derived_columns = {
        column
        for column in df.columns
        if column.endswith("_count") or column.endswith("_chars")
    }

    for column in df.columns:
        entropy, unique_values, total, most_common_value, most_common_frequency = shannon_entropy(df[column])
        max_entropy = math.log2(unique_values) if unique_values > 1 else 0.0
        normalized_entropy = entropy / max_entropy if max_entropy else 0.0
        missing_values = int((df[column].fillna("").astype(str).str.strip() == "").sum())
        unique_ratio = unique_values / total if total else 0.0

        rows.append(
            {
                "column": column,
                "column_type": "derived" if column in derived_columns else "original",
                "rows": total,
                "missing_or_empty_values": missing_values,
                "unique_values": unique_values,
                "unique_ratio": round(unique_ratio, 6),
                "entropy_shannon_bits": round(entropy, 6),
                "max_entropy_bits": round(max_entropy, 6),
                "normalized_entropy": round(normalized_entropy, 6),
                "most_common_value": most_common_value[:200],
                "most_common_frequency": most_common_frequency,
                "classification": classify_column(column, unique_values, total_rows, normalized_entropy),
            }
        )

    return pd.DataFrame(rows).sort_values(
        by=["classification", "normalized_entropy", "entropy_shannon_bits"],
        ascending=[True, False, False],
    )


def build_eiac_report(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    total_rows = len(df)

    for column in df.columns:
        entropy, unique_values, observed_total, most_common_value, most_common_frequency = shannon_entropy(
            df[column],
            include_missing=False,
        )
        max_entropy = math.log2(unique_values) if unique_values > 1 else 0.0
        normalized_entropy = entropy / max_entropy if max_entropy else 0.0
        missing_values = int((df[column].fillna("").astype(str).str.strip() == "").sum())
        completeness = (total_rows - missing_values) / total_rows if total_rows else 0.0
        unique_ratio = unique_values / total_rows if total_rows else 0.0
        uniqueness_penalty = 1 - unique_ratio
        eiac = normalized_entropy * completeness * uniqueness_penalty
        relevance = classify_relevance(eiac)
        functional_classification = classify_functional_column(
            column,
            unique_ratio,
            1 - completeness,
            normalized_entropy,
        )

        rows.append(
            {
                "Columna": column,
                "Distribución": format_distribution(df[column]),
                "k": unique_values,
                "H(X)": round(entropy, 6),
                "Hn(X)": round(normalized_entropy, 6),
                "C(X)": round(completeness, 6),
                "U(X)": round(unique_ratio, 6),
                "1-U(X)": round(uniqueness_penalty, 6),
                "EIAC": round(eiac, 6),
                "Relevancia": format_relevance_label(relevance),
                "Clasificación funcional": format_functional_label(functional_classification),
                "Análisis": build_analysis_text(relevance, functional_classification),
                "Datos faltantes": missing_values,
                "Valor más frecuente": most_common_value[:200],
                "Frecuencia valor más frecuente": most_common_frequency,
                "Total observado": observed_total,
            }
        )

    return pd.DataFrame(rows).sort_values(
        by=["EIAC", "Hn(X)", "Columna"],
        ascending=[False, False, True],
    )


def latex_escape(value: object) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def truncate_text(value: object, max_length: int) -> str:
    text = str(value)
    if len(text) <= max_length:
        return text
    return text[: max_length - 3].rstrip() + "..."


def build_latex_table(report: pd.DataFrame, max_rows: int | None = None, label_suffix: str = "") -> str:
    label = "tab:calculo-eiac-columnas"
    if label_suffix:
        label = f"{label}-{label_suffix}"

    selected = report if max_rows is None else report.head(max_rows)
    lines = [
        r"\begin{table}[h]",
        r"\centering",
        r"\caption{Cálculo de EIAC y clasificación funcional de columnas}",
        rf"\label{{{label}}}",
        r"\scriptsize",
        r"\begin{tabular}{|p{2.1cm}|p{3.0cm}|c|c|c|c|c|c|p{2.5cm}|p{2.8cm}|}",
        r"\hline",
        r"\textbf{Columna} & \textbf{Distribución} & \textbf{\(k\)} & \textbf{\(H(X)\)} & \textbf{\(H_n(X)\)} & \textbf{\(C(X)\)} & \textbf{\(U(X)\)} & \textbf{EIAC} & \textbf{Análisis} & \textbf{Clasificación funcional} \\",
        r"\hline",
    ]

    for _, row in selected.iterrows():
        lines.append(
            " & ".join(
                [
                    latex_escape(row["Columna"]),
                    latex_escape(row["Distribución"]),
                    str(row["k"]),
                    f"{row['H(X)']:.3f}",
                    f"{row['Hn(X)']:.3f}",
                    f"{row['C(X)']:.3f}",
                    f"{row['U(X)']:.3f}",
                    f"{row['EIAC']:.3f}",
                    latex_escape(row["Relevancia"]),
                    latex_escape(row["Clasificación funcional"]),
                ]
            )
            + r" \\"
        )
        lines.append(r"\hline")

    lines.extend([r"\end{tabular}", r"\end{table}"])
    return "\n".join(lines) + "\n"


def build_pdf_report(report: pd.DataFrame, output_path: Path, max_rows: int | None = None) -> None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as exc:
        raise SystemExit(
            "Falta la librería reportlab. Instálela con: python3 -m pip install reportlab"
        ) from exc

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#1F2937"),
        spaceAfter=8,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=14,
    )
    section_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#1F4E79"),
        spaceBefore=10,
        spaceAfter=6,
    )
    note_style = ParagraphStyle(
        "SectionNote",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=8,
    )
    header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=8,
        textColor=colors.white,
    )
    cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.5,
        leading=8,
        textColor=colors.HexColor("#111827"),
    )
    number_style = ParagraphStyle(
        "NumberCell",
        parent=cell_style,
        alignment=TA_CENTER,
    )

    headers = [
        "Columna",
        "Distribución",
        "k",
        "H(X)",
        "Hn(X)",
        "C(X)",
        "U(X)",
        "EIAC",
        "Análisis",
        "Clasificación funcional",
    ]

    def make_table(dataframe: pd.DataFrame) -> Table:
        selected_rows = dataframe if max_rows is None else dataframe.head(max_rows)
        table_data = [[Paragraph(header, header_style) for header in headers]]

        for _, row in selected_rows.iterrows():
            table_data.append(
                [
                    Paragraph(truncate_text(row["Columna"], 45), cell_style),
                    Paragraph(truncate_text(row["Distribución"], 150), cell_style),
                    Paragraph(str(row["k"]), number_style),
                    Paragraph(f"{row['H(X)']:.3f}", number_style),
                    Paragraph(f"{row['Hn(X)']:.3f}", number_style),
                    Paragraph(f"{row['C(X)']:.3f}", number_style),
                    Paragraph(f"{row['U(X)']:.3f}", number_style),
                    Paragraph(f"{row['EIAC']:.3f}", number_style),
                    Paragraph(truncate_text(row["Análisis"], 130), cell_style),
                    Paragraph(truncate_text(row["Clasificación funcional"], 55), cell_style),
                ]
            )

        table = Table(
            table_data,
            repeatRows=1,
            colWidths=[
                2.3 * cm,
                5.1 * cm,
                0.8 * cm,
                1.0 * cm,
                1.0 * cm,
                1.0 * cm,
                1.0 * cm,
                1.0 * cm,
                4.6 * cm,
                3.6 * cm,
            ],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        return table

    mandatory_report = report[report["Columna"].isin(MANDATORY_ANALYSIS_COLUMNS)].copy()
    mandatory_report["orden_obligatorio"] = mandatory_report["Columna"].map(
        {column: index for index, column in enumerate(MANDATORY_ANALYSIS_COLUMNS)}
    )
    mandatory_report = mandatory_report.sort_values("orden_obligatorio").drop(columns=["orden_obligatorio"])
    complementary_report = report[~report["Columna"].isin(MANDATORY_ANALYSIS_COLUMNS)].copy()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        rightMargin=0.8 * cm,
        leftMargin=0.8 * cm,
        topMargin=0.9 * cm,
        bottomMargin=0.9 * cm,
    )

    story = [
        Paragraph("Reporte EIAC de columnas CAPEC", title_style),
        Paragraph(
            f"Tabla generada automáticamente con {len(report)} columnas del ranking EIAC.",
            subtitle_style,
        ),
        Paragraph("Tabla 1. Campos de análisis obligatorio", section_style),
        Paragraph(
            "Incluye las columnas definidas en el documento como dataset modelo: identificación, contexto y atributos categóricos comparables.",
            note_style,
        ),
        make_table(mandatory_report),
        Spacer(1, 0.35 * cm),
        Paragraph("Tabla 2. Columnas complementarias", section_style),
        Paragraph(
            "Incluye las demás columnas disponibles o derivadas del catálogo CAPEC. Estas apoyan la exploración, pero no forman parte del subconjunto principal definido para el análisis obligatorio.",
            note_style,
        ),
        make_table(complementary_report),
    ]
    document.build(story)


def build_hn_eiac_comparison_pdf(report: pd.DataFrame, output_path: Path) -> None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as exc:
        raise SystemExit(
            "Falta la librería reportlab. Instálela con: python3 -m pip install reportlab"
        ) from exc

    comparison = report.copy()
    comparison["Diferencia Hn-EIAC"] = comparison["Hn(X)"] - comparison["EIAC"]
    comparison["Lectura comparativa"] = comparison.apply(
        lambda row: explain_hn_eiac_difference(row["Hn(X)"], row["EIAC"], row["C(X)"], row["U(X)"]),
        axis=1,
    )

    mandatory_comparison = comparison[comparison["Columna"].isin(MANDATORY_ANALYSIS_COLUMNS)].copy()
    mandatory_comparison["orden_obligatorio"] = mandatory_comparison["Columna"].map(
        {column: index for index, column in enumerate(MANDATORY_ANALYSIS_COLUMNS)}
    )
    mandatory_comparison = mandatory_comparison.sort_values("orden_obligatorio").drop(columns=["orden_obligatorio"])
    full_comparison = comparison.sort_values(
        by=["Diferencia Hn-EIAC", "Hn(X)"],
        ascending=[False, False],
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ComparisonTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#1F2937"),
        spaceAfter=8,
    )
    subtitle_style = ParagraphStyle(
        "ComparisonSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=12,
    )
    section_style = ParagraphStyle(
        "ComparisonSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#1F4E79"),
        spaceBefore=10,
        spaceAfter=6,
    )
    note_style = ParagraphStyle(
        "ComparisonNote",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=8,
    )
    header_style = ParagraphStyle(
        "ComparisonHeader",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=8,
        textColor=colors.white,
    )
    cell_style = ParagraphStyle(
        "ComparisonCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.5,
        leading=8,
        textColor=colors.HexColor("#111827"),
    )
    number_style = ParagraphStyle(
        "ComparisonNumber",
        parent=cell_style,
        alignment=TA_CENTER,
    )

    def make_comparison_table(dataframe: pd.DataFrame) -> Table:
        headers = [
            "Columna",
            "Hn(X)",
            "C(X)",
            "U(X)",
            "1-U(X)",
            "EIAC",
            "Diferencia",
            "Lectura comparativa",
        ]
        table_data = [[Paragraph(header, header_style) for header in headers]]

        for _, row in dataframe.iterrows():
            table_data.append(
                [
                    Paragraph(truncate_text(row["Columna"], 45), cell_style),
                    Paragraph(f"{row['Hn(X)']:.3f}", number_style),
                    Paragraph(f"{row['C(X)']:.3f}", number_style),
                    Paragraph(f"{row['U(X)']:.3f}", number_style),
                    Paragraph(f"{row['1-U(X)']:.3f}", number_style),
                    Paragraph(f"{row['EIAC']:.3f}", number_style),
                    Paragraph(f"{row['Diferencia Hn-EIAC']:.3f}", number_style),
                    Paragraph(truncate_text(row["Lectura comparativa"], 170), cell_style),
                ]
            )

        table = Table(
            table_data,
            repeatRows=1,
            colWidths=[3.0 * cm, 1.2 * cm, 1.2 * cm, 1.2 * cm, 1.2 * cm, 1.2 * cm, 1.5 * cm, 9.1 * cm],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7A3E00")),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FFF7ED")]),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        return table

    output_path.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        rightMargin=0.8 * cm,
        leftMargin=0.8 * cm,
        topMargin=0.9 * cm,
        bottomMargin=0.9 * cm,
    )
    story = [
        Paragraph("Comparación entre Hn(X) y EIAC", title_style),
        Paragraph(
            "Hn(X) representa la entropía de Shannon normalizada. EIAC ajusta ese valor con completitud y unicidad para evitar sobrevalorar columnas con muchos faltantes o valores únicos.",
            subtitle_style,
        ),
        Paragraph("Tabla 1. Comparación en campos de análisis obligatorio", section_style),
        Paragraph(
            "Esta tabla muestra cómo cambia la interpretación en las columnas principales del dataset modelo.",
            note_style,
        ),
        make_comparison_table(mandatory_comparison),
        Spacer(1, 0.35 * cm),
        Paragraph("Tabla 2. Comparación en todas las columnas", section_style),
        Paragraph(
            "La diferencia Hn-EIAC permite identificar columnas donde Shannon normalizado puede parecer alto, pero EIAC reduce el valor por unicidad o falta de completitud.",
            note_style,
        ),
        make_comparison_table(full_comparison),
    ]
    document.build(story)


def build_hn_eiac_comparison_latex(report: pd.DataFrame, label_suffix: str = "") -> str:
    label = "tab:comparacion-hn-eiac"
    if label_suffix:
        label = f"{label}-{label_suffix}"

    comparison = report.copy()
    comparison["Diferencia Hn-EIAC"] = comparison["Hn(X)"] - comparison["EIAC"]
    comparison["Lectura comparativa"] = comparison.apply(
        lambda row: explain_hn_eiac_difference(row["Hn(X)"], row["EIAC"], row["C(X)"], row["U(X)"]),
        axis=1,
    )
    comparison = comparison.sort_values(
        by=["Diferencia Hn-EIAC", "Hn(X)"],
        ascending=[False, False],
    )

    lines = [
        r"\begin{table}[h]",
        r"\centering",
        r"\caption{Comparación entre entropía normalizada y EIAC}",
        rf"\label{{{label}}}",
        r"\scriptsize",
        r"\begin{tabular}{|p{3cm}|c|c|c|c|c|c|p{5cm}|}",
        r"\hline",
        r"\textbf{Columna} & \textbf{\(H_n(X)\)} & \textbf{\(C(X)\)} & \textbf{\(U(X)\)} & \textbf{\(1-U(X)\)} & \textbf{EIAC} & \textbf{Diferencia} & \textbf{Lectura comparativa} \\",
        r"\hline",
    ]

    for _, row in comparison.iterrows():
        lines.append(
            " & ".join(
                [
                    latex_escape(row["Columna"]),
                    f"{row['Hn(X)']:.3f}",
                    f"{row['C(X)']:.3f}",
                    f"{row['U(X)']:.3f}",
                    f"{row['1-U(X)']:.3f}",
                    f"{row['EIAC']:.3f}",
                    f"{row['Diferencia Hn-EIAC']:.3f}",
                    latex_escape(row["Lectura comparativa"]),
                ]
            )
            + r" \\"
        )
        lines.append(r"\hline")

    lines.extend([r"\end{tabular}", r"\end{table}"])
    return "\n".join(lines) + "\n"


def explain_hn_eiac_difference(hn_value: float, eiac: float, completeness: float, unique_ratio: float) -> str:
    difference = hn_value - eiac
    if unique_ratio >= 0.95:
        return "Hn(X) es alto, pero EIAC baja el valor porque la columna se comporta como identificador o texto casi único."
    if completeness < 0.50:
        return "EIAC reduce el valor porque la columna tiene muchos datos faltantes."
    if difference >= 0.40:
        return "EIAC ajusta fuertemente el valor de Shannon al considerar completitud y unicidad."
    if difference >= 0.15:
        return "EIAC realiza un ajuste moderado frente a Shannon normalizado."
    return "Hn(X) y EIAC son cercanos; la columna conserva buena parte de su relevancia informativa."


def print_console_table(report: pd.DataFrame, max_rows: int | None) -> None:
    display_columns = [
        "Columna",
        "Distribución",
        "k",
        "H(X)",
        "Hn(X)",
        "C(X)",
        "U(X)",
        "EIAC",
        "Análisis",
        "Clasificación funcional",
    ]
    selected = report if max_rows is None else report.head(max_rows)
    console_report = selected[display_columns].copy()
    console_report["Distribución"] = console_report["Distribución"].map(lambda value: truncate_text(value, 80))
    console_report["Análisis"] = console_report["Análisis"].map(lambda value: truncate_text(value, 85))
    with pd.option_context(
        "display.max_colwidth",
        90,
        "display.width",
        220,
    ):
        print("Tabla de resultados EIAC")
        print("=" * 80)
        print(console_report.to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Procesa CAPEC y calcula entropía por columna.")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="CSV local o URL publicada como CSV")
    parser.add_argument("--processed", default="datos/processed/capec_dataset.csv", help="CSV procesado")
    parser.add_argument("--entropy", default="datos/results/entropia_columnas.csv", help="Ranking de entropía")
    parser.add_argument("--eiac", default="datos/results/eiac_columnas.csv", help="Ranking EIAC")
    parser.add_argument("--eiac-latex", default="datos/results/eiac_tabla_latex.tex", help="Tabla EIAC en LaTeX")
    parser.add_argument("--eiac-pdf", default="datos/results/eiac_reporte.pdf", help="Reporte EIAC en PDF")
    parser.add_argument(
        "--comparison-pdf",
        default="datos/results/eiac_comparacion_hn_eiac.pdf",
        help="Reporte PDF comparativo entre Hn(X) y EIAC",
    )
    parser.add_argument(
        "--comparison-latex",
        default="datos/results/eiac_comparacion_hn_eiac.tex",
        help="Tabla LaTeX comparativa entre Hn(X) y EIAC",
    )
    parser.add_argument("--pdf-rows", type=int, default=None, help="Filas EIAC para incluir en el PDF")
    parser.add_argument("--print-rows", type=int, default=None, help="Filas EIAC para imprimir en consola")
    args = parser.parse_args()

    source = args.input if is_url(args.input) else str(Path(args.input))
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    processed_csv = add_timestamp_to_path(Path(args.processed), run_timestamp)
    entropy_csv = add_timestamp_to_path(Path(args.entropy), run_timestamp)
    eiac_csv = add_timestamp_to_path(Path(args.eiac), run_timestamp)
    eiac_latex = add_timestamp_to_path(Path(args.eiac_latex), run_timestamp)
    eiac_pdf = add_timestamp_to_path(Path(args.eiac_pdf), run_timestamp)
    comparison_pdf = add_timestamp_to_path(Path(args.comparison_pdf), run_timestamp)
    comparison_latex = add_timestamp_to_path(Path(args.comparison_latex), run_timestamp)

    processed_csv.parent.mkdir(parents=True, exist_ok=True)
    entropy_csv.parent.mkdir(parents=True, exist_ok=True)
    eiac_csv.parent.mkdir(parents=True, exist_ok=True)
    eiac_latex.parent.mkdir(parents=True, exist_ok=True)
    eiac_pdf.parent.mkdir(parents=True, exist_ok=True)
    comparison_pdf.parent.mkdir(parents=True, exist_ok=True)
    comparison_latex.parent.mkdir(parents=True, exist_ok=True)

    processed = build_processed_dataset(source)
    entropy_report = build_entropy_report(processed)
    eiac_report = build_eiac_report(processed)

    processed.to_csv(processed_csv, index=False)
    entropy_report.to_csv(entropy_csv, index=False)
    eiac_report.to_csv(eiac_csv, index=False)
    eiac_latex.write_text(build_latex_table(eiac_report, label_suffix=run_timestamp), encoding="utf-8")
    build_pdf_report(eiac_report, eiac_pdf, args.pdf_rows)
    build_hn_eiac_comparison_pdf(eiac_report, comparison_pdf)
    comparison_latex.write_text(
        build_hn_eiac_comparison_latex(eiac_report, label_suffix=run_timestamp),
        encoding="utf-8",
    )

    print(f"Registros procesados: {len(processed)}")
    print(f"Columnas procesadas: {len(processed.columns)}")
    print(f"Fuente de datos: {source}")
    print(f"Fecha y hora de ejecución: {run_timestamp}")
    print(f"Dataset procesado: {processed_csv}")
    print(f"Ranking de entropía: {entropy_csv}")
    print(f"Ranking EIAC: {eiac_csv}")
    print(f"Tabla EIAC LaTeX: {eiac_latex}")
    print(f"Reporte EIAC PDF: {eiac_pdf}")
    print(f"Comparación Hn(X) vs EIAC PDF: {comparison_pdf}")
    print(f"Comparación Hn(X) vs EIAC LaTeX: {comparison_latex}")
    print()
    print_console_table(eiac_report, args.print_rows)


if __name__ == "__main__":
    main()
