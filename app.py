import io
import base64
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask, jsonify

from matplotlib.figure import Figure

app = Flask(__name__)

class ECGData:
    def __init__(self):
        self.data = {f"lead_{i}": np.zeros(500) for i in range(1, 13)}
        self.init_data()
    
    def init_data(self):
        for lead in self.data:
            lead_num = int(lead.split('_')[1])
            freq = 0.4 + (lead_num * 0.05)
            amplitude = 0.5 + (lead_num * 0.1) % 1
            phase = lead_num * np.pi / 6
            x = np.linspace(0, 10*np.pi, 500)
            self.data[lead] = np.sin(x * freq + phase) * amplitude

            for i in range(15, 500, 50):
                if i >= 10:
                    p_wave = np.sin(np.linspace(0, np.pi, 10)) * 0.2
                    self.data[lead][i-10:i] += p_wave
                if i+3 < 500:
                    self.data[lead][i] -= 0.2  # Q
                    r_wave = np.linspace(0, 2, 2) * (1 + (lead_num % 3) * 0.5)
                    self.data[lead][i+1:i+3] += r_wave
                if i+5 < 500:
                    s_wave = np.linspace(0.5, 0, 2) * 0.3
                    self.data[lead][i+3:i+5] -= s_wave
                if i+15 < 500:
                    t_wave = np.sin(np.linspace(0, np.pi, 7)) * 0.3
                    self.data[lead][i+8:i+15] += t_wave
            self.data[lead] += np.random.normal(0, 0.03, 500)
    
    def update_data(self):
        for lead in self.data:
            self.data[lead] = np.roll(self.data[lead], -2)
            lead_num = int(lead.split('_')[1])
            freq = 0.4 + (lead_num * 0.05)
            amplitude = 0.5 + (lead_num * 0.1) % 1
            phase = lead_num * np.pi / 6
            x = np.linspace(0, 2*np.pi, 2)
            new_points = np.sin(x * freq + phase) * amplitude
            if np.random.random() < 0.2:
                new_points[1] += 1.2 * (1 + (lead_num % 3) * 0.5)
            new_points += np.random.normal(0, 0.05, 2)
            self.data[lead][-2:] = new_points
        return self.data

    def get_plot_base64(self, lead_num):
        fig = Figure(figsize=(6, 2))  # wider graph
        ax = fig.add_subplot(111)
        lead_key = f"lead_{lead_num}"
        ax.plot(np.arange(len(self.data[lead_key])), self.data[lead_key], 'g-', linewidth=0.9)
        ax.set_title(f"Lead {lead_num}", fontsize=10)
        ax.set_ylim(-2, 2)
        ax.set_yticks([])
        ax.set_xticks([])
        fig.tight_layout(pad=1.0)
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=120)
        buf.seek(0)
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close(fig)
        return image_base64


ecg_data = ECGData()

@app.route('/')
def index():
    return get_index_template()

@app.route('/update_ecg')
def update_ecg():
    ecg_data.update_data()
    plots = {}
    for i in range(1, 13):
        plots[f"lead_{i}"] = ecg_data.get_plot_base64(i)
    return jsonify(plots)

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
                gap: 20px;
            }
            .ecg-lead {
                border: 1px solid #ccc;
                padding: 12px;
                border-radius: 8px;
                background: #f9f9f9;
                box-shadow: 0 0 5px rgba(0,0,0,0.1);
            }
            .ecg-lead img {
                width: 100%;
                height: auto;
                display: block;
            }
        </style>
    </head>
    <body>
        <h1>12-Lead ECG Monitor</h1>
        <div class="ecg-grid">
            """ + "\n".join([
                f"""
                <div class="ecg-lead">
                    <h3>Lead {i}</h3>
                    <img id="lead_{i}" src="/update_ecg" alt="Lead {i}">
                </div>
                """ for i in range(1, 13)
            ]) + """
        </div>

        <script>
            function updateECG() {
                fetch('/update_ecg')
                    .then(response => response.json())
                    .then(data => {
                        for (let i = 1; i <= 12; i++) {
                            const img = document.getElementById(`lead_${i}`);
                            img.src = `data:image/png;base64,${data[`lead_${i}`]}`;
                        }
                    })
                    .catch(error => console.error('Update failed:', error));
            }

            // Faster updates (every 100ms)
            setInterval(updateECG, 100);
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(debug=True)
