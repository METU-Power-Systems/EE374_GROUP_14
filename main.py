# main.py  –  EE374 Phase‑1  ▸  polished GUI
pip install pandas

import sys, math, pandas as pd
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLineEdit, QDoubleSpinBox, QComboBox, QSpinBox, QRadioButton,
    QPushButton, QTableView, QMessageBox, QLabel, QGroupBox,
    QHeaderView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor

from cable_utils import smart_filter, apparent_power, line_current, required_capacity
from cable_table import DataFrameModel

# ---------- DATA ----------
FILE = Path(__file__).with_name("cable_list.xlsx")
df_full = pd.read_excel(FILE, header=1).dropna(axis=1, how="all")
df_full["Voltage level"] = df_full["Voltage level"].ffill()
VOLTAGE_LEVELS = sorted(df_full["Voltage level"].astype(str).unique())

# ---------- MAIN WINDOW ----------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EE374 – Cable Smart‑Listing  (Phase 1)")
        self.resize(1000, 680)

        # ---------- WIDGETS ----------
        self.p_edit = self.spin(1000)       # kW
        self.q_edit = self.spin(1000)       # kVAr
        self.vll_edit = self.spin(100000, 0)  # V

        self.vlevel_box = QComboBox(); self.vlevel_box.addItems(VOLTAGE_LEVELS)
        self.temp_box   = QComboBox(); self.temp_box.addItems([str(t) for t in (5,10,15,20,25,30,35,40)])
        self.circ_spin  = QSpinBox();  self.circ_spin.setRange(1, 6)

        self.type3 = QRadioButton("3‑core"); self.type1 = QRadioButton("Single‑core"); self.type3.setChecked(True)
        self.place_box = QComboBox(); self.place_box.addItems(["flat", "trefoil"])

        self.filter_btn = QPushButton("Filter"); self.reset_btn = QPushButton("Reset")

        self.table = QTableView(); self.refresh_table(df_full)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)

        # ---------- LAYOUT ----------
        main = QVBoxLayout(self)
        main.addSpacing(18)          # <‑‑ NEW 18‑pixel top margin
        # --- Load box ---
        load_box = QGroupBox("Load & Environment")
        load_form = QFormLayout(load_box)
        load_form.addRow("P (kW):", self.p_edit)
        load_form.addRow("Q (kVAr):", self.q_edit)
        load_form.addRow("Line‑to‑Line Voltage (V):", self.vll_edit)
        load_form.addRow("System Voltage Level:", self.vlevel_box)
        load_form.addRow("Ambient Temp (°C):", self.temp_box)

        # --- Cable box ---
        cable_box = QGroupBox("Cable & Installation")
        cable_form = QFormLayout(cable_box)
        type_row = QHBoxLayout(); type_row.addWidget(self.type3); type_row.addWidget(self.type1)
        cable_form.addRow("Cable type:", type_row)
        cable_form.addRow("Placement (single‑core):", self.place_box)
        cable_form.addRow("Parallel circuits in trench:", self.circ_spin)

        # --- Buttons ---
        btn_row = QHBoxLayout(); btn_row.addStretch(); btn_row.addWidget(self.filter_btn); btn_row.addWidget(self.reset_btn)

        main.addWidget(load_box)
        main.addSpacing(20)
        main.addWidget(cable_box)
        main.addLayout(btn_row)
        main.addWidget(self.table)

        # ---------- SIGNALS ----------
        self.filter_btn.clicked.connect(self.handle_filter)
        self.reset_btn.clicked.connect(lambda: self.refresh_table(df_full))

        # ---------- STYLE ----------
        self.apply_fusion_theme()

    # ---------- helpers ----------
    def spin(self, maximum, decimals=1):
        s = QDoubleSpinBox(decimals=decimals)
        s.setRange(0, maximum)
        return s

    def refresh_table(self, df: pd.DataFrame):
        self.table.setModel(DataFrameModel(df))

    def handle_filter(self):
        try:
            p = float(self.p_edit.text()); q = float(self.q_edit.text()); vll = float(self.vll_edit.text())
        except ValueError:
            QMessageBox.warning(self, "Missing numbers", "Please fill P, Q and V_LL.")
            return

        temp = int(self.temp_box.currentText())
        n_circ = self.circ_spin.value()
        cable_type = "3-core" if self.type3.isChecked() else "single"

        S = apparent_power(p, q)
        I_load = line_current(S, vll)
        cap_needed = required_capacity(I_load, temp, n_circ, cable_type)

        df_filt = smart_filter(
            df_full,
            v_level = self.vlevel_box.currentText(),
            cap_needed = cap_needed,
            cable_type = cable_type,
            placement = self.place_box.currentText()
        )

        if df_filt.empty:
            QMessageBox.information(self, "No match",
                "No cable satisfies the rating for these inputs.\n"
                "Try single‑core, more circuits, or a higher voltage level.")
            return

        self.refresh_table(df_filt)

    # ---------- theme ----------
    # ---------- theme ----------
    def apply_fusion_theme(self):
        QApplication.setStyle("Fusion")
    
        # custom dark‑green palette
        pal = QPalette()
    
        deep_green   = QColor("#113d2b")   # window background
        mid_green    = QColor("#1d5a3f")   # group‑box fill
        alt_row      = QColor("#174b34")   # alternating row colour
        text_colour  = QColor("#e9f7ef")   # nearly‑white text
        highlight    = QColor("#33c18e")   # focus / selection blue‑green
    
        pal.setColor(QPalette.Window,       deep_green)
        pal.setColor(QPalette.Base,         mid_green)
        pal.setColor(QPalette.AlternateBase, alt_row)
        pal.setColor(QPalette.Text,         text_colour)
        pal.setColor(QPalette.WindowText,   text_colour)
        pal.setColor(QPalette.ButtonText,   text_colour)
        pal.setColor(QPalette.Highlight,    highlight)
        pal.setColor(QPalette.HighlightedText, QColor("black"))
    
        self.setPalette(pal)
    
        # widget styling – higher‑contrast groups + nicer table header
        self.setStyleSheet("""
            QWidget { color:#e9f7ef; }

            /* -------- group boxes -------- */
            QGroupBox {
                font-weight:bold;
                border:2px solid #33c18e;
                border-radius:8px;
                margin-top:14px;               /* distance from widgets above */
                background:#0e2d21;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left:18px;                     /* horizontal indent */
                top:-2px;                      /* only 2 px above border (was -10) */
                padding:2px 8px;
                background:#13553c;            /* lighter strip behind the text */
                color:#33c18e;
            }

            /* -------- inputs -------- */
            QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {
                background:#e9f7ef; color:#000;
                border:1px solid #2b7d5a; border-radius:4px; padding:2px 6px;
            }

            /* -------- table -------- */
            QHeaderView::section {
                background:#174b34;
                color:#e9f7ef;
                padding:4px;
                border:none;
            }
            QTableView {
                gridline-color:#2b7d5a;
                selection-background-color:#33c18e;
                alternate-background-color:#24114a;  /* purple rows you liked */
            }
            
            /* -------- combo‑box popup (drop‑down list) -------- */
            QComboBox QAbstractItemView {
                background:#cfe9ff;                 /* light blue */
                selection-background-color:#33c18e; /* keep teal highlight */
                color:#000;                         /* black text for readability */
            }
            /* -------- buttons -------- */
            QPushButton {
                background:#33c18e; color:black; padding:4px 18px;
                border:none; border-radius:4px;
            }
            QPushButton:hover   { background:#45dca2; }
            QPushButton:pressed { background:#28a16f; }
        """)


# ---------- RUN ----------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow(); win.show()
    sys.exit(app.exec())
