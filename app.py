import sys
import numpy as np
import threading
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QGridLayout, QLabel)
from PyQt6.QtCore import QTimer, pyqtSignal, Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class ECGCanvas(FigureCanvas):
    """Canvas for displaying a single ECG lead"""
    def __init__(self, lead_number, width=3, height=2, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        self.lead_number = lead_number
        
        super(ECGCanvas, self).__init__(self.fig)
        
        # Initialize the data
        self.data = np.zeros(500)
        
        # Configure the plot
        self.axes.set_title(f"Lead {lead_number}")
        self.axes.set_ylim(-2, 2)
        self.axes.set_yticks([])
        self.axes.set_xticks([])
        self.line, = self.axes.plot(np.arange(len(self.data)), self.data, 'g-', linewidth=0.8)
        
        self.fig.tight_layout()
        
    def update_data(self, new_data):
        """Update the plot with new data"""
        self.data = new_data
        self.line.set_ydata(self.data)
        self.draw()


class ECGMonitor(QMainWindow):
    """Main application window for the ECG monitor"""
    data_updated = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("12-Lead ECG Monitor")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create the central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create the main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Add a title label
        title_label = QLabel("12-Lead ECG Monitor")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Create a grid layout for the ECG plots
        grid_layout = QGridLayout()
        main_layout.addLayout(grid_layout)
        
        # Initialize the ECG canvases
        self.ecg_canvases = {}
        for i in range(1, 13):
            row = (i - 1) // 2
            col = (i - 1) % 2
            canvas = ECGCanvas(i)
            grid_layout.addWidget(canvas, row, col)
            self.ecg_canvases[f"lead_{i}"] = canvas
        
        # Initialize the ECG data
        self.ecg_data = {f"lead_{i}": np.zeros(500) for i in range(1, 13)}
        self.data_lock = threading.Lock()
        
        # Connect the data updated signal
        self.data_updated.connect(self.update_plots)
        
        # Start the data generation thread
        self.running = True
        self.data_thread = threading.Thread(target=self.generate_ecg_data, daemon=True)
        self.data_thread.start()
        
        # Set up the timer for updating the UI
        self.timer = QTimer()
        self.timer.timeout.connect(self.request_update)
        self.timer.start(100)  # Update every 100ms
    
    def generate_ecg_data(self):
        """Generate synthetic ECG data for 12 leads"""
        while self.running:
            with self.data_lock:
                for lead in self.ecg_data:
                    # Shift the data to the left
                    self.ecg_data[lead] = np.roll(self.ecg_data[lead], -5)
                    
                    # Generate new data points for the right side
                    # Using different patterns for different leads to simulate real ECG
                    lead_num = int(lead.split('_')[1])
                    freq = 0.4 + (lead_num * 0.05)  # Different frequency for each lead
                    amplitude = 0.5 + (lead_num * 0.1) % 1  # Different amplitude
                    phase = lead_num * np.pi / 6  # Different phase
                    
                    # Generate a QRS complex like pattern with some noise
                    x = np.linspace(0, 2*np.pi, 5)
                    new_points = np.sin(x * freq + phase) * amplitude
                    
                    # Add a spike to simulate R wave (higher for some leads)
                    if lead_num % 3 == 0:
                        new_points[2] += 1.5
                    
                    # Add some random noise
                    new_points += np.random.normal(0, 0.05, 5)
                    
                    # Add the new points
                    self.ecg_data[lead][-5:] = new_points
            
            # Update at a regular interval
            time.sleep(0.1)
    
    def request_update(self):
        """Request an update of the plots"""
        with self.data_lock:
            data_copy = self.ecg_data.copy()
        self.data_updated.emit(data_copy)
    
    def update_plots(self, data):
        """Update all ECG plots with new data"""
        for lead, canvas in self.ecg_canvases.items():
            canvas.update_data(data[lead])
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.running = False
        if self.data_thread.is_alive():
            self.data_thread.join(1.0)  # Wait for the thread to finish
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ECGMonitor()
    window.show()
    sys.exit(app.exec())