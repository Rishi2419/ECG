import io
import base64
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Set the backend to Agg for server-side rendering
import matplotlib.pyplot as plt
from flask import Flask, render_template, jsonify
from matplotlib.figure import Figure

app = Flask(__name__)

class ECGData:
    """Class to generate and store ECG data"""
    def __init__(self):
        self.data = {f"lead_{i}": np.zeros(500) for i in range(1, 13)}
        self.init_data()
    
    def init_data(self):
        """Initialize data with some patterns"""
        for lead in self.data:
            lead_num = int(lead.split('_')[1])
            freq = 0.4 + (lead_num * 0.05)
            amplitude = 0.5 + (lead_num * 0.1) % 1
            phase = lead_num * np.pi / 6
            
            # Create a sinusoidal pattern with some noise
            x = np.linspace(0, 10*np.pi, 500)
            self.data[lead] = np.sin(x * freq + phase) * amplitude
            
            # Add some QRS complexes
            for i in range(5, 500, 50):
                if i+15 < 500:
                    # P wave
                    self.data[lead][i-10:i] += np.sin(np.linspace(0, np.pi, 10)) * 0.2
                    # QRS complex
                    self.data[lead][i] -= 0.2  # Q wave
                    self.data[lead][i+1:i+3] += np.linspace(0, 2, 2) * (1 + (lead_num % 3) * 0.5)  # R wave
                    self.data[lead][i+3:i+5] -= np.linspace(0.5, 0, 2) * 0.3  # S wave
                    # T wave
                    self.data[lead][i+8:i+15] += np.sin(np.linspace(0, np.pi, 7)) * 0.3
            
            # Add some random noise
            self.data[lead] += np.random.normal(0, 0.03, 500)
    
    def update_data(self):
        """Update ECG data by shifting and generating new points"""
        for lead in self.data:
            # Shift data to the left
            self.data[lead] = np.roll(self.data[lead], -5)
            
            # Generate new points
            lead_num = int(lead.split('_')[1])
            freq = 0.4 + (lead_num * 0.05)
            amplitude = 0.5 + (lead_num * 0.1) % 1
            phase = lead_num * np.pi / 6
            
            # Generate new points with patterns
            x = np.linspace(0, 2*np.pi, 5)
            new_points = np.sin(x * freq + phase) * amplitude
            
            # Add a spike for R wave occasionally
            if np.random.random() < 0.1:
                new_points[2] += 1.5 * (1 + (lead_num % 3) * 0.5)
            
            # Add noise
            new_points += np.random.normal(0, 0.05, 5)
            
            # Update the data
            self.data[lead][-5:] = new_points
        
        return self.data

    def get_plot_base64(self, lead_num):
        """Generate a base64 image for a specific lead"""
        fig = Figure(figsize=(5, 2))
        ax = fig.add_subplot(111)
        
        lead_key = f"lead_{lead_num}"
        ax.plot(np.arange(len(self.data[lead_key])), self.data[lead_key], 'g-', linewidth=0.8)
        
        ax.set_title(f"Lead {lead_num}")
        ax.set_ylim(-2, 2)
        ax.set_yticks([])
        ax.set_xticks([])
        fig.tight_layout()
        
        # Save the figure to a PNG in memory
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        
        # Encode the PNG as base64
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close(fig)
        
        return image_base64


# Initialize ECG data
ecg_data = ECGData()

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/update_ecg')
def update_ecg():
    """API endpoint to update ECG data and return new plots"""
    # Update the ECG data
    ecg_data.update_data()
    
    # Generate plots for all leads
    plots = {}
    for i in range(1, 13):
        plots[f"lead_{i}"] = ecg_data.get_plot_base64(i)
    
    return jsonify(plots)

# Create a simple template for the index page
@app.route('/templates/index.html')
def get_index_template():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>12-Lead ECG Monitor</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
            }
            h1 {
                text-align: center;
                margin-bottom: 20px;
            }
            .ecg-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
            }
            .ecg-lead {
                border: 1px solid #ccc;
                padding: 10px;
                border-radius: 5px;
            }
            .ecg-lead img {
                width: 100%;
            }
        </style>
    </head>
    <body>
        <h1>12-Lead ECG Monitor</h1>
        <div class="ecg-grid">
            <div class="ecg-lead">
                <h3>Lead 1</h3>
                <img id="lead_1" src="/update_ecg" alt="Lead 1">
            </div>
            <div class="ecg-lead">
                <h3>Lead 2</h3>
                <img id="lead_2" src="/update_ecg" alt="Lead 2">
            </div>
            <div class="ecg-lead">
                <h3>Lead 3</h3>
                <img id="lead_3" src="/update_ecg" alt="Lead 3">
            </div>
            <div class="ecg-lead">
                <h3>Lead 4</h3>
                <img id="lead_4" src="/update_ecg" alt="Lead 4">
            </div>
            <div class="ecg-lead">
                <h3>Lead 5</h3>
                <img id="lead_5" src="/update_ecg" alt="Lead 5">
            </div>
            <div class="ecg-lead">
                <h3>Lead 6</h3>
                <img id="lead_6" src="/update_ecg" alt="Lead 6">
            </div>
            <div class="ecg-lead">
                <h3>Lead 7</h3>
                <img id="lead_7" src="/update_ecg" alt="Lead 7">
            </div>
            <div class="ecg-lead">
                <h3>Lead 8</h3>
                <img id="lead_8" src="/update_ecg" alt="Lead 8">
            </div>
            <div class="ecg-lead">
                <h3>Lead 9</h3>
                <img id="lead_9" src="/update_ecg" alt="Lead 9">
            </div>
            <div class="ecg-lead">
                <h3>Lead 10</h3>
                <img id="lead_10" src="/update_ecg" alt="Lead 10">
            </div>
            <div class="ecg-lead">
                <h3>Lead 11</h3>
                <img id="lead_11" src="/update_ecg" alt="Lead 11">
            </div>
            <div class="ecg-lead">
                <h3>Lead 12</h3>
                <img id="lead_12" src="/update_ecg" alt="Lead 12">
            </div>
        </div>

        <script>
            function updateECG() {
                fetch('/update_ecg')
                    .then(response => response.json())
                    .then(data => {
                        for (let i = 1; i <= 12; i++) {
                            const imgElement = document.getElementById(`lead_${i}`);
                            imgElement.src = `data:image/png;base64,${data[`lead_${i}`]}`;
                        }
                    })
                    .catch(error => console.error('Error updating ECG:', error));
            }

            // Update every 500ms
            setInterval(updateECG, 500);
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(debug=True)