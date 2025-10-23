# Multimeter Streamlit Dashboard

Real-time monitoring dashboard for Energy Meter using Streamlit.

## 🌟 Live Demo

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-name.streamlit.app)

**Try the demo!** The dashboard automatically runs in demo mode when deployed to the cloud, showing realistic simulated data.

## Features

- 📊 Real-time parameter monitoring (Voltage, Current, Power)
- 📈 Live graphs and visualizations with Plotly
- 💾 Historical data tracking (last 50 readings)
- 🔌 RS485/Modbus RTU communication (hardware mode)
- 🎮 Demo mode with simulated data (cloud mode)
- ⚡ Support for 3-phase voltage and current measurements
- 📉 Frequency and Power Factor monitoring
- 🔄 Auto-refresh with configurable intervals

## Demo Mode

When running on Streamlit Cloud (or any environment without serial ports), the dashboard automatically switches to **Demo Mode**, displaying realistic simulated data:

- Voltage: 230V ±5V with realistic fluctuations
- Current: 10A ±2A with load variations  
- Frequency: 50Hz ±0.1Hz
- Power Factor: 0.85 ±0.05
- Active and Reactive Power calculations

Perfect for demonstrations, training, or portfolio showcases!

## Installation

### Local Setup

1. Clone this repository:
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the dashboard:
```bash
streamlit run app.py
```

## Hardware Requirements

- SECURE ELITE 440 Energy Meter
- USB to RS485 converter
- Serial connection (COM port)

## Configuration

Configure the connection settings in the Streamlit sidebar:
- **COM Port**: Select your RS485 adapter port
- **Baudrate**: Default 9600
- **Parity**: Default Even (E)
- **Unit ID**: Default 1

## Usage

1. Connect your RS485 adapter to the meter
2. Launch the dashboard
3. Configure connection settings
4. Click "Connect" to start monitoring

## Register Map

The dashboard reads the following parameters:
- Voltage (L1-N, L2-N, L3-N)
- Current (L1, L2, L3)
- Power (Active, Reactive, Apparent)
- Frequency
- Power Factor
- Energy (kWh)

## Deployment

This dashboard can be deployed on Streamlit Cloud for remote access.

## License

MIT License

## Author

Your Name

## Support

For issues and questions, please open an issue on GitHub.