import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QListWidget, QTabWidget, QTextEdit, QHeaderView, QAbstractItemView,
    QMessageBox
)
from PySide6.QtGui import QTextCursor 
from PySide6.QtCore import Qt, QObject, Signal

from wizard import Wizard

# ------------------------------------------------------------------- #
# Stream class for redirecting print statements
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
        'lasers': {
            405: {
                '450/45': {'center': 450, 'width': 45},
                '525/40': {'center': 525, 'width': 40},
            },
            488: {
                '525/40': {'center': 525, 'width': 40},
                '585/42': {'center': 585, 'width': 42},
                '660/10': {'center': 660, 'width': 10},
            },
            638: {
                '660/10': {'center': 660, 'width': 10},
                '780/60': {'center': 780, 'width': 60},
            }
        }
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Antibody Panel Solver")
        self.setGeometry(100, 100, 900, 700)

        # In-memory data storage for the antibody panel
        self.panel_data = {}
        self.instrument_data = {}

        self.init_ui()
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
        self.instrument_data = self.DEFAULT_INSTRUMENT_CONFIG.copy()
        
        # Populate the laser list
        self.laser_list_widget.clear()
        for laser in self.instrument_data['lasers'].keys():
            self.laser_list_widget.addItem(str(laser))

        # Select the first laser to trigger the detector table update
        if self.laser_list_widget.count() > 0:
            self.laser_list_widget.setCurrentRow(0)

    def create_instrument_tab(self):
        tab = QWidget()
        # Main horizontal layout: [Lasers Pane | Detectors Pane]
        main_layout = QHBoxLayout(tab)

        # --- Left Pane: Lasers ---
        laser_pane_layout = QVBoxLayout()
        laser_pane_layout.addWidget(QLabel("Lasers"))
        self.laser_list_widget = QListWidget()
        self.laser_list_widget.currentItemChanged.connect(self.update_detector_table)
        laser_pane_layout.addWidget(self.laser_list_widget)

        laser_input_layout = QHBoxLayout()
        self.laser_input = QLineEdit()
        self.laser_input.setPlaceholderText("e.g., 405")
        add_laser_btn = QPushButton("Add")
        remove_laser_btn = QPushButton("Remove")
        laser_input_layout.addWidget(self.laser_input)
        laser_input_layout.addWidget(add_laser_btn)
        laser_input_layout.addWidget(remove_laser_btn)
        laser_pane_layout.addLayout(laser_input_layout)
        
        main_layout.addLayout(laser_pane_layout, 1) # 1/3 of the space

        # --- Right Pane: Detectors ---
        detector_pane_layout = QVBoxLayout()
        self.detector_header_label = QLabel("Detectors for Selected Laser")
        detector_pane_layout.addWidget(self.detector_header_label)
        
        self.detector_table = QTableWidget(0, 3)
        self.detector_table.setHorizontalHeaderLabels(['Name', 'Center (nm)', 'Width (nm)'])
        self.detector_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.detector_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        detector_pane_layout.addWidget(self.detector_table)

        detector_input_layout = QGridLayout()
        self.d_name_input = QLineEdit()
        self.d_center_input = QLineEdit()
        self.d_width_input = QLineEdit()
        self.d_name_input.setPlaceholderText("e.g., 525/40")
        self.d_center_input.setPlaceholderText("e.g., 525")
        self.d_width_input.setPlaceholderText("e.g., 40")
        add_detector_btn = QPushButton("Add Detector")
        remove_detector_btn = QPushButton("Remove Selected")

        detector_input_layout.addWidget(QLabel("Name:"), 0, 0)
        detector_input_layout.addWidget(self.d_name_input, 0, 1)
        detector_input_layout.addWidget(QLabel("Center:"), 1, 0)
        detector_input_layout.addWidget(self.d_center_input, 1, 1)
        detector_input_layout.addWidget(QLabel("Width:"), 2, 0)
        detector_input_layout.addWidget(self.d_width_input, 2, 1)
        detector_input_layout.addWidget(add_detector_btn, 0, 2, 2, 1)
        detector_input_layout.addWidget(remove_detector_btn, 2, 2)
        detector_pane_layout.addLayout(detector_input_layout)

        main_layout.addLayout(detector_pane_layout, 2) # 2/3 of the space

        # Connect signals to slots
        add_laser_btn.clicked.connect(self.add_laser)
        remove_laser_btn.clicked.connect(self.remove_laser)
        add_detector_btn.clicked.connect(self.add_detector)
        remove_detector_btn.clicked.connect(self.remove_detector)

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

    def add_laser(self):
        try:
            laser_val = int(self.laser_input.text().strip())
            if 'lasers' not in self.instrument_data:
                self.instrument_data['lasers'] = {}
                
            if laser_val in self.instrument_data['lasers']:
                QMessageBox.warning(self, "Input Error", "This laser already exists.")
                return

            self.instrument_data['lasers'][laser_val] = {}
            self.laser_list_widget.addItem(str(laser_val))
            self.laser_input.clear()
        except ValueError:
            QMessageBox.critical(self, "Input Error", "Please enter a valid integer for the laser.")
            
    ### NEW: Slot to remove a laser
    def remove_laser(self):
        current_item = self.laser_list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Selection Error", "Please select a laser to remove.")
            return
            
        laser_val = int(current_item.text())
        del self.instrument_data['lasers'][laser_val]
        self.laser_list_widget.takeItem(self.laser_list_widget.row(current_item))
        # The currentItemChanged signal will fire, auto-updating the detector table
        
    ### NEW: Slot that updates the detector table when a new laser is selected
    def update_detector_table(self, current_item, previous_item):
        self.detector_table.setRowCount(0) # Clear the table
        
        if not current_item:
            self.detector_header_label.setText("Detectors for Selected Laser")
            return

        laser_val = int(current_item.text())
        self.detector_header_label.setText(f"Detectors for Laser {laser_val} nm")
        
        detectors = self.instrument_data['lasers'].get(laser_val, {})
        for name, props in detectors.items():
            row_pos = self.detector_table.rowCount()
            self.detector_table.insertRow(row_pos)
            self.detector_table.setItem(row_pos, 0, QTableWidgetItem(name))
            self.detector_table.setItem(row_pos, 1, QTableWidgetItem(str(props['center'])))
            self.detector_table.setItem(row_pos, 2, QTableWidgetItem(str(props['width'])))


    def add_detector(self):
        current_laser_item = self.laser_list_widget.currentItem()
        if not current_laser_item:
            QMessageBox.warning(self, "Input Error", "Please select a laser first.")
            return
        
        laser_val = int(current_laser_item.text())
        
        try:
            name = self.d_name_input.text().strip()
            center = int(self.d_center_input.text())
            width = int(self.d_width_input.text())
            if not name:
                raise ValueError("Detector name cannot be empty.")
            
            self.instrument_data['lasers'][laser_val][name] = {'center': center, 'width': width}
            self.update_detector_table(current_laser_item, None) # Refresh table view
            
            self.d_name_input.clear()
            self.d_center_input.clear()
            self.d_width_input.clear()
        except ValueError as e:
            QMessageBox.critical(self, "Input Error", f"Please enter valid detector data.\n({e})")
            
    def remove_detector(self):
        current_laser_item = self.laser_list_widget.currentItem()
        selected_detector_row = self.detector_table.currentRow()
        
        if not current_laser_item or selected_detector_row < 0:
            QMessageBox.warning(self, "Selection Error", "Please select a laser and a detector to remove.")
            return

        laser_val = int(current_laser_item.text())
        detector_name = self.detector_table.item(selected_detector_row, 0).text()
        
        del self.instrument_data['lasers'][laser_val][detector_name]
        self.update_detector_table(current_laser_item, None) # Refresh table view

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
            # 1. Assemble data from GUI (now much simpler)
            # Basic validation
            if not self.instrument_data.get('lasers'):
                raise ValueError("Please define at least one laser.")
            if not any(self.instrument_data['lasers'].values()):
                raise ValueError("Please add at least one detector to one of the lasers.")
            if not self.panel_data or all(not v for v in self.panel_data.values()):
                raise ValueError("Please add at least one marker with one antibody.")

            # 2. Instantiate Wizard and run
            print("Data assembled. Starting analysis...\n")
            # The instrument data is already in the correct format
            wizard = Wizard(self.panel_data, self.instrument_data)
            wizard.run()

        except Exception as e:
            error_message = f"ERROR: {e}"
            print(error_message)
            QMessageBox.critical(self, "Analysis Error", str(e))

        finally:
            self.run_button.setEnabled(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())