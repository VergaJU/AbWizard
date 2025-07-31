import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QListWidget, QTabWidget, QTextEdit, QHeaderView, QAbstractItemView,
    QMessageBox
)
from PySide6.QtGui import QTextCursor 
from PySide6.QtCore import Qt, QObject, Signal

# Import your backend logic
from wizard import Wizard

# ------------------------------------------------------------------- #
# CORRECT IMPLEMENTATION for redirecting print statements
# ------------------------------------------------------------------- #
class Stream(QObject):
    """A QObject that captures text and emits it as a Qt signal."""
    textWritten = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def write(self, text):
        self.textWritten.emit(str(text))

    def flush(self):
        pass

# ------------------------------------------------------------------- #
# MAIN APPLICATION WINDOW
# ------------------------------------------------------------------- #
class MainWindow(QWidget):
    DEFAULT_INSTRUMENT_CONFIG = {
        'lasers': "405, 488, 638",
        'filters': [
            [450, 45, 1], [525, 40, 2], [585, 42, 1], [610, 20, 2],
            [660, 10, 2], [690, 50, 1], [712, 25, 1], [780, 60, 3],
        ]
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Antibody Panel Solver")
        self.setGeometry(100, 100, 800, 600)

        # In-memory data storage for the antibody panel
        self.panel_data = {}

        # --- Setup the GUI ---
        self.init_ui()

        # --- Load default data and connect the logger AFTER UI is built ---
        self.load_default_instrument()
        self.connect_logger()

    def init_ui(self):
        """Creates and arranges all the widgets."""
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.create_instrument_tab()
        self.create_panel_tab()

        self.run_button = QPushButton("Run Analysis")
        self.run_button.setFixedHeight(40)
        self.run_button.clicked.connect(self.run_analysis)
        main_layout.addWidget(self.run_button)
        
        main_layout.addWidget(QLabel("Log:"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        main_layout.addWidget(self.log_output)

    def connect_logger(self):
        """Redirects stdout to the GUI log widget."""
        self.stream = Stream()
        self.stream.textWritten.connect(self.on_log_update)
        sys.stdout = self.stream
        print("GUI Initialized. Default instrument configuration loaded.")

    def on_log_update(self, text):
        """Slot to receive text and append it to the log."""
        self.log_output.moveCursor(QTextCursor.MoveOperation.End)
        self.log_output.insertPlainText(text)

    def load_default_instrument(self):
        self.laser_input.setText(self.DEFAULT_INSTRUMENT_CONFIG['lasers'])
        default_filters = self.DEFAULT_INSTRUMENT_CONFIG['filters']
        self.filter_table.setRowCount(len(default_filters))
        
        for row, filter_data in enumerate(default_filters):
            for col, item in enumerate(filter_data):
                self.filter_table.setItem(row, col, QTableWidgetItem(str(item)))

    def create_instrument_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        layout.addWidget(QLabel("Enter available lasers, separated by commas:"))
        self.laser_input = QLineEdit()
        layout.addWidget(self.laser_input)
        
        layout.addWidget(QLabel("Detector Channels (Filters):"))
        self.filter_table = QTableWidget(0, 3)
        self.filter_table.setHorizontalHeaderLabels(['Center (nm)', 'Width (nm)', 'Count'])
        self.filter_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.filter_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.filter_table)

        input_layout = QHBoxLayout()
        self.f_center_input = QLineEdit()
        self.f_width_input = QLineEdit()
        self.f_count_input = QLineEdit("1")
        add_btn = QPushButton("Add Filter")
        remove_btn = QPushButton("Remove Selected")

        input_layout.addWidget(QLabel("Center:"))
        input_layout.addWidget(self.f_center_input)
        input_layout.addWidget(QLabel("Width:"))
        input_layout.addWidget(self.f_width_input)
        input_layout.addWidget(QLabel("Count:"))
        input_layout.addWidget(self.f_count_input)
        input_layout.addWidget(add_btn)
        input_layout.addWidget(remove_btn)
        layout.addLayout(input_layout)

        add_btn.clicked.connect(self.add_filter)
        remove_btn.clicked.connect(self.remove_filter)
        self.tabs.addTab(tab, "1. Instrument Setup")

    def create_panel_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)

        marker_layout = QVBoxLayout()
        marker_layout.addWidget(QLabel("Markers:"))
        self.marker_list = QListWidget()
        self.marker_list.currentItemChanged.connect(self.update_antibody_table)
        marker_layout.addWidget(self.marker_list)
        
        marker_input_layout = QHBoxLayout()
        self.marker_name_input = QLineEdit()
        add_marker_btn = QPushButton("Add")
        remove_marker_btn = QPushButton("Remove")
        marker_input_layout.addWidget(self.marker_name_input)
        marker_input_layout.addWidget(add_marker_btn)
        marker_input_layout.addWidget(remove_marker_btn)
        marker_layout.addLayout(marker_input_layout)
        layout.addLayout(marker_layout)

        ab_layout = QVBoxLayout()
        self.ab_header_label = QLabel("Antibodies for Selected Marker:")
        ab_layout.addWidget(self.ab_header_label)
        self.antibody_table = QTableWidget(0, 3)
        self.antibody_table.setHorizontalHeaderLabels(['Name', 'Ex (nm)', 'Em (nm)'])
        self.antibody_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.antibody_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        ab_layout.addWidget(self.antibody_table)

        ab_input_layout = QGridLayout()
        self.ab_name_input = QLineEdit()
        self.ab_ex_input = QLineEdit()
        self.ab_em_input = QLineEdit()
        add_ab_btn = QPushButton("Add Antibody")
        remove_ab_btn = QPushButton("Remove Selected")
        ab_input_layout.addWidget(QLabel("Name:"), 0, 0)
        ab_input_layout.addWidget(self.ab_name_input, 0, 1)
        ab_input_layout.addWidget(QLabel("Ex:"), 1, 0)
        ab_input_layout.addWidget(self.ab_ex_input, 1, 1)
        ab_input_layout.addWidget(QLabel("Em:"), 2, 0)
        ab_input_layout.addWidget(self.ab_em_input, 2, 1)
        ab_input_layout.addWidget(add_ab_btn, 0, 2, 2, 1)
        ab_input_layout.addWidget(remove_ab_btn, 2, 2, 1, 1)
        ab_layout.addLayout(ab_input_layout)
        layout.addLayout(ab_layout)

        add_marker_btn.clicked.connect(self.add_marker)
        remove_marker_btn.clicked.connect(self.remove_marker)
        add_ab_btn.clicked.connect(self.add_antibody)
        remove_ab_btn.clicked.connect(self.remove_antibody)
        
        self.tabs.addTab(tab, "2. Antibody Panel")

    def add_filter(self):
        try:
            center = int(self.f_center_input.text())
            width = int(self.f_width_input.text())
            count = int(self.f_count_input.text())
            
            row_pos = self.filter_table.rowCount()
            self.filter_table.insertRow(row_pos)
            self.filter_table.setItem(row_pos, 0, QTableWidgetItem(str(center)))
            self.filter_table.setItem(row_pos, 1, QTableWidgetItem(str(width)))
            self.filter_table.setItem(row_pos, 2, QTableWidgetItem(str(count)))
            
            self.f_center_input.clear()
            self.f_width_input.clear()
            self.f_count_input.setText("1")
        except ValueError:
            QMessageBox.critical(self, "Input Error", "Please enter valid numbers for filter properties.")
            
    def remove_filter(self):
        selected_row = self.filter_table.currentRow()
        if selected_row >= 0:
            self.filter_table.removeRow(selected_row)
        else:
            QMessageBox.warning(self, "Selection Error", "Please select a filter to remove.")

    def add_marker(self):
        name = self.marker_name_input.text().strip()
        if name and name not in self.panel_data:
            self.panel_data[name] = []
            self.marker_list.addItem(name)
            self.marker_name_input.clear()
        else:
            QMessageBox.warning(self, "Input Error", "Marker name cannot be empty or a duplicate.")

    def remove_marker(self):
        current_item = self.marker_list.currentItem()
        if current_item:
            name = current_item.text()
            del self.panel_data[name]
            self.marker_list.takeItem(self.marker_list.row(current_item))
            self.antibody_table.setRowCount(0) # Clear table
        else:
            QMessageBox.warning(self, "Selection Error", "Please select a marker to remove.")

    def update_antibody_table(self, current, previous):
        if not current:
            self.ab_header_label.setText("Antibodies for Selected Marker:")
            self.antibody_table.setRowCount(0)
            return
        
        marker_name = current.text()
        self.ab_header_label.setText(f"Antibodies for: {marker_name}")
        self.antibody_table.setRowCount(0) # Clear
        
        antibodies = self.panel_data.get(marker_name, [])
        for ab in antibodies:
            row_pos = self.antibody_table.rowCount()
            self.antibody_table.insertRow(row_pos)
            self.antibody_table.setItem(row_pos, 0, QTableWidgetItem(ab['name']))
            self.antibody_table.setItem(row_pos, 1, QTableWidgetItem(str(ab['ex'])))
            self.antibody_table.setItem(row_pos, 2, QTableWidgetItem(str(ab['em'])))

    def add_antibody(self):
        current_marker_item = self.marker_list.currentItem()
        if not current_marker_item:
            QMessageBox.warning(self, "Input Error", "Please select a marker first.")
            return
        
        marker_name = current_marker_item.text()
        try:
            name = self.ab_name_input.text().strip()
            ex = int(self.ab_ex_input.text())
            em = int(self.ab_em_input.text())
            if not name: raise ValueError("Name cannot be empty.")
            
            self.panel_data[marker_name].append({'name': name, 'ex': ex, 'em': em})
            self.update_antibody_table(current_marker_item, None)
            
            self.ab_name_input.clear()
            self.ab_ex_input.clear()
            self.ab_em_input.clear()
        except ValueError as e:
            QMessageBox.critical(self, "Input Error", f"Please enter valid antibody data.\n({e})")

    def remove_antibody(self):
        current_marker_item = self.marker_list.currentItem()
        selected_ab_row = self.antibody_table.currentRow()
        
        if not current_marker_item or selected_ab_row < 0:
            QMessageBox.warning(self, "Selection Error", "Please select a marker and an antibody to remove.")
            return
        
        marker_name = current_marker_item.text()
        self.panel_data[marker_name].pop(selected_ab_row)
        self.update_antibody_table(current_marker_item, None)

    # --- All your slot functions like add_filter, add_marker, etc. go here ---
    # These methods were also correct in your previous code.

    def run_analysis(self):
        self.log_output.clear()
        self.run_button.setEnabled(False)
        QApplication.processEvents()

        try:
            # 1. Assemble data from GUI
            lasers_text = self.laser_input.text()
            if not lasers_text: raise ValueError("Lasers cannot be empty.")
            lasers = [int(l.strip()) for l in lasers_text.split(',')]

            instrument_config = {'lasers': lasers, 'filters': {}}
            if self.filter_table.rowCount() == 0:
                raise ValueError("At least one filter must be defined.")
            for row in range(self.filter_table.rowCount()):
                center = int(self.filter_table.item(row, 0).text())
                width = int(self.filter_table.item(row, 1).text())
                count = int(self.filter_table.item(row, 2).text())
                instrument_config['filters'][f"{center}/{width}"] = {'center': center, 'width': width, 'count': count}

            # *** THIS IS THE FIX FOR THE FIRST ERROR ***
            # Ensure the panel data isn't empty AND that at least one marker has antibodies.
            if not self.panel_data or all(not v for v in self.panel_data.values()):
                raise ValueError("Please add at least one marker with one antibody.")

            # 2. Instantiate Wizard and run
            print("Data assembled. Starting analysis...\n")
            wizard = Wizard(self.panel_data, instrument_config)
            wizard.run()

        except Exception as e:
            error_message = f"ERROR: {e}"
            print(error_message) # This now works correctly
            QMessageBox.critical(self, "Analysis Error", str(e))

        finally:
            self.run_button.setEnabled(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())