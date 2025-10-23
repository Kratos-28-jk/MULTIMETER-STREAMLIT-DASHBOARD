
#!/usr/bin/env python3
"""
Multi-Meter PAC3200 Streamlit Dashboard
Save this file as: multi_pac3200_dashboard.py
Run with: streamlit run multi_pac3200_dashboard.py
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import time
import os
import json
import logging

# Try to import Modbus libraries (optional for demonstration)
from network_helper import display_network_info, show_connection_status

# In your sidebar section:
display_network_info()
try:
    from pymodbus.client import ModbusTcpClient as ModbusClient
    from pymodbus.payload import BinaryPayloadDecoder
    from pymodbus.constants import Endian
    MODBUS_AVAILABLE = True
except ImportError:
    try:
        # Try older pymodbus version
        from pymodbus.client.sync import ModbusTcpClient as ModbusClient
        from pymodbus.payload import BinaryPayloadDecoder
        from pymodbus.constants import Endian
        MODBUS_AVAILABLE = True
    except ImportError:
        MODBUS_AVAILABLE = False
        st.warning("⚠️ PyModbus not installed. Running in demo mode with simulated data.\n\nTo install: `pip install pymodbus`")

# Set page configuration
st.set_page_config(
    page_title="Multi-Meter PAC3200 Monitor",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1f77b4;
    }
    .status-online {
        color: #28a745;
        font-weight: bold;
    }
    .status-offline {
        color: #dc3545;
        font-weight: bold;
    }
    .meter-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #e9ecef;
        margin-bottom: 1rem;
    }
    .meter-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #495057;
        margin-bottom: 0.5rem;
    }
    .big-font {
        font-size: 20px !important;
        font-weight: bold;
    }
    .stAlert {
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

class PAC3200Meter:
    """Single PAC3200 meter instance"""
    def __init__(self, meter_id, name, host='192.168.0.101', port=502, unit_id=1, timeout=3, location="", description=""):
        self.meter_id = meter_id
        self.name = name
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout
        self.location = location
        self.description = description
        self.client = None
        self.connected = False
        self.last_reading = None
        self.last_reading_time = None
        
        # SENTRON PAC3200 Register Map
        self.registers = {
            # Voltage Measurements
            'V1_N_Voltage': 1, 'V2_N_Voltage': 3, 'V3_N_Voltage': 5,
            'V1_V2_Voltage': 7, 'V2_V3_Voltage': 9, 'V3_V1_Voltage': 11,
            'Maximum_Voltage_V1_n': 75, 'Maximum_Voltage_V2_n': 77, 'Maximum_Voltage_V3_n': 79,
            'Maximum_Voltage_V1_2': 81, 'Maximum_Voltage_V2_3': 83, 'Maximum_Voltage_V3_1': 85,
            'Minimum_Voltage_V1_n': 145, 'Minimum_Voltage_V2_n': 147, 'Minimum_Voltage_V3_n': 149,
            'Minimum_Voltage_V1_2': 151, 'Minimum_Voltage_V2_3': 153, 'Minimum_Voltage_V3_1': 155,
            'THD_R_Voltage_1': 43, 'THD_R_Voltage_2': 45, 'THD_R_Voltage_3': 47,
            'Average_Voltage_Vph_n': 57, 'Average_Voltage_Vph_ph': 59,
            'Amplitude_Unbalance_Voltage': 71,
            
            # Current Measurements  
            'L1_Current': 13, 'L2_Current': 15, 'L3_Current': 17,
            'Maximum_Current_1': 87, 'Maximum_Current_2': 89, 'Maximum_Current_3': 91,
            'Minimum_Current_1': 157, 'Maximum_Current_2': 159, 'Minimum_Current_3': 161,
            'Average_Current': 61,
            'THD_R_Current_1': 49, 'THD_R_Current_2': 51, 'THD_R_Current_3': 53,
            'Amplitude_Unbalance_Current': 73,
            
            # Power Measurements
            'L1_Active_Power': 25, 'L2_Active_Power': 27, 'L3_Active_Power': 29,
            'Maximum_Active_Power_1': 99, 'Maximum_Active_Power_2': 101, 'Maximum_Active_Power_3': 103,
            'Minimum_Active_Power_1': 169, 'Minimum_Active_Power_2': 171, 'Minimum_Active_Power_3': 173,
            'Total_Active_Power': 65,
            
            'L1_Reactive_Power': 31, 'L2_Reactive_Power': 33, 'L3_Reactive_Power': 35,
            'Maximum_Reactive_Power_1': 105, 'Maximum_Reactive_Power_2': 107, 'Maximum_Reactive_Power_3': 109,
            'Minimum_Reactive_Power_1': 175, 'Minimum_Reactive_Power_2': 177, 'Minimum_Reactive_Power_3': 179,
            'Total_Reactive_Power': 67,
            
            'L1_Apparent_Power': 19, 'L2_Apparent_Power': 21, 'L3_Apparent_Power': 23,
            'Maximum_Apparent_Power_1': 93, 'Maximum_Apparent_Power_2': 95, 'Maximum_Apparent_Power_3': 97,
            'Minimum_Apparent_Power_1': 163, 'Minimum_Apparent_Power_2': 165, 'Minimum_Apparent_Power_3': 167,
            'Total_Apparent_Power': 63,
            
            # Power Factor
            'L1_Power_Factor': 37, 'L2_Power_Factor': 39, 'L3_Power_Factor': 41,
            'Maximum_Power_Factor_1': 111, 'Maximum_Power_Factor_2': 113, 'Maximum_Power_Factor_3': 115,
            'Minimum_Power_Factor_1': 181, 'Minimum_Power_Factor_2': 183, 'Minimum_Power_Factor_3': 185,
            'Total_Power_Factor': 69,
            
            # Frequency and Energy
            'Frequency': 55,
            'Total_Active_Energy': 801,
            'Total_Reactive_Energy': 805,
        }
    
    def connect(self):
        """Connect to PAC3200"""
        if not MODBUS_AVAILABLE:
            self.connected = True
            return True
            
        try:
            if self.client:
                self.client.close()
            
            self.client = ModbusClient(host=self.host, port=self.port, timeout=self.timeout)
            connected = self.client.connect()
            
            if connected:
                # Test connection by reading a simple register
                test_result = self.client.read_holding_registers(1, 2, unit=self.unit_id)
                if test_result.isError():
                    self.connected = False
                    return False
                self.connected = True
                return True
            else:
                self.connected = False
                return False
                
        except Exception as e:
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from PAC3200"""
        if self.client and MODBUS_AVAILABLE:
            self.client.close()
        self.connected = False
    
    def read_float32_register(self, register_address):
        """Read a 32-bit float from PAC3200"""
        if not MODBUS_AVAILABLE:
            # Return simulated data for demo
            return self._generate_simulated_value(register_address)
            
        try:
            if not self.client or not self.client.is_socket_open():
                return None
                
            rr = self.client.read_holding_registers(register_address, 2, unit=self.unit_id)
            
            if rr.isError():
                return None
                
            decoder = BinaryPayloadDecoder.fromRegisters(
                rr.registers, 
                byteorder=Endian.Big, 
                wordorder=Endian.Big
            )
            
            value = decoder.decode_32bit_float()
            
            if np.isnan(value) or np.isinf(value):
                return None
                
            return value
            
        except Exception as e:
            return None
    
    def _generate_simulated_value(self, register_address):
        """Generate simulated values for demo purposes"""
        # Add some variation based on meter_id to differentiate meters
        meter_offset = hash(self.meter_id) % 10 / 10.0
        
        voltage_registers = [1, 3, 5, 7, 9, 11, 57, 59]
        current_registers = [13, 15, 17, 61]
        power_registers = [25, 27, 29, 31, 33, 35, 19, 21, 23, 65, 67, 63]
        power_factor_registers = [37, 39, 41, 69]
        frequency_registers = [55]
        thd_registers = [43, 45, 47, 49, 51, 53]
        energy_registers = [801, 805]
        
        base_time = time.time()
        variation = np.sin(base_time / 10 + meter_offset) * 0.1 + np.random.normal(0, 0.02)
        
        if register_address in voltage_registers:
            if register_address in [57, 59]:
                return 230 + variation * 10 + meter_offset * 5
            else:
                return 230 + variation * 15 + meter_offset * 5
        elif register_address in current_registers:
            return 10 + variation * 5 + meter_offset * 3
        elif register_address in power_registers:
            if register_address == 65:
                return 2300 + variation * 300 + meter_offset * 500
            elif register_address in [67, 63]:
                return 2400 + variation * 320 + meter_offset * 500
            else:
                return 760 + variation * 100 + meter_offset * 150
        elif register_address in power_factor_registers:
            return 0.85 + variation * 0.1
        elif register_address in frequency_registers:
            return 50.0 + variation * 0.2
        elif register_address in thd_registers:
            return 2.5 + abs(variation) * 2
        elif register_address in energy_registers:
            return 1000000 + base_time * 100 + meter_offset * 100000
        else:
            return abs(variation) * 100
    
    def read_all_parameters(self):
        """Read all parameters and return as dictionary"""
        data = {}
        
        for param_name, register_addr in self.registers.items():
            try:
                value = self.read_float32_register(register_addr)
                data[param_name] = value
            except Exception as e:
                data[param_name] = None
        
        self.last_reading = data
        self.last_reading_time = datetime.now()
        return data

class MultiMeterDashboard:
    """Main dashboard managing multiple PAC3200 meters"""
    def __init__(self, db_name='multi_pac3200_data.db'):
        self.db_name = db_name
        self.meters = {}  # Dictionary of meter_id: PAC3200Meter instances
        self.init_database()
        self.load_meters_config()
    
    def init_database(self):
        """Initialize SQLite database with multi-meter support"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Check if old table exists with device_id column
            cursor.execute("PRAGMA table_info(pac3200_readings)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'device_id' in columns:
                # Old schema detected, need to migrate
                st.info("Migrating database schema...")
                
                # Backup old data if exists
                cursor.execute("SELECT COUNT(*) FROM pac3200_readings")
                count = cursor.fetchone()[0]
                
                if count > 0:
                    # Create backup
                    cursor.execute("ALTER TABLE pac3200_readings RENAME TO pac3200_readings_backup")
                else:
                    # No data, just drop the table
                    cursor.execute("DROP TABLE IF EXISTS pac3200_readings")
            
            # Create meters configuration table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS meters_config (
                    meter_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    host TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    unit_id INTEGER NOT NULL,
                    location TEXT,
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Drop old table if exists and recreate with correct schema
            cursor.execute("DROP TABLE IF EXISTS pac3200_readings")
            
            # Create readings table with meter_id
            cursor.execute('''
                CREATE TABLE pac3200_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meter_id TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    V1_N_Voltage REAL, V2_N_Voltage REAL, V3_N_Voltage REAL,
                    V1_V2_Voltage REAL, V2_V3_Voltage REAL, V3_V1_Voltage REAL,
                    Maximum_Voltage_V1_n REAL, Maximum_Voltage_V2_n REAL, Maximum_Voltage_V3_n REAL,
                    Maximum_Voltage_V1_2 REAL, Maximum_Voltage_V2_3 REAL, Maximum_Voltage_V3_1 REAL,
                    Minimum_Voltage_V1_n REAL, Minimum_Voltage_V2_n REAL, Minimum_Voltage_V3_n REAL,
                    Minimum_Voltage_V1_2 REAL, Minimum_Voltage_V2_3 REAL, Minimum_Voltage_V3_1 REAL,
                    L1_Current REAL, L2_Current REAL, L3_Current REAL,
                    Maximum_Current_1 REAL, Maximum_Current_2 REAL, Maximum_Current_3 REAL,
                    Minimum_Current_1 REAL, Minimum_Current_2 REAL, Minimum_Current_3 REAL,
                    L1_Active_Power REAL, L2_Active_Power REAL, L3_Active_Power REAL,
                    Maximum_Active_Power_1 REAL, Maximum_Active_Power_2 REAL, Maximum_Active_Power_3 REAL,
                    Minimum_Active_Power_1 REAL, Minimum_Active_Power_2 REAL, Minimum_Active_Power_3 REAL,
                    L1_Reactive_Power REAL, L2_Reactive_Power REAL, L3_Reactive_Power REAL,
                    Maximum_Reactive_Power_1 REAL, Maximum_Reactive_Power_2 REAL, Maximum_Reactive_Power_3 REAL,
                    Minimum_Reactive_Power_1 REAL, Minimum_Reactive_Power_2 REAL, Minimum_Reactive_Power_3 REAL,
                    L1_Apparent_Power REAL, L2_Apparent_Power REAL, L3_Apparent_Power REAL,
                    Maximum_Apparent_Power_1 REAL, Maximum_Apparent_Power_2 REAL, Maximum_Apparent_Power_3 REAL,
                    Minimum_Apparent_Power_1 REAL, Minimum_Apparent_Power_2 REAL, Minimum_Apparent_Power_3 REAL,
                    L1_Power_Factor REAL, L2_Power_Factor REAL, L3_Power_Factor REAL,
                    Maximum_Power_Factor_1 REAL, Maximum_Power_Factor_2 REAL, Maximum_Power_Factor_3 REAL,
                    Minimum_Power_Factor_1 REAL, Minimum_Power_Factor_2 REAL, Minimum_Power_Factor_3 REAL,
                    Total_Active_Power REAL, Total_Reactive_Power REAL, Total_Apparent_Power REAL,
                    Total_Power_Factor REAL, Frequency REAL, Average_Current REAL,
                    Average_Voltage_Vph_n REAL, Average_Voltage_Vph_ph REAL,
                    THD_R_Voltage_1 REAL, THD_R_Voltage_2 REAL, THD_R_Voltage_3 REAL,
                    THD_R_Current_1 REAL, THD_R_Current_2 REAL, THD_R_Current_3 REAL,
                    Amplitude_Unbalance_Voltage REAL, Amplitude_Unbalance_Current REAL,
                    Total_Active_Energy REAL, Total_Reactive_Energy REAL,
                    FOREIGN KEY (meter_id) REFERENCES meters_config(meter_id)
                )
            ''')
            
            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_readings_meter_timestamp 
                ON pac3200_readings(meter_id, timestamp DESC)
            ''')
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            st.error(f"Database initialization error: {e}")
            return False
    
    def add_meter(self, meter_id, name, host, port, unit_id, location="", description=""):
        """Add a new meter to the system"""
        try:
            # Create meter instance
            meter = PAC3200Meter(meter_id, name, host, port, unit_id, 
                                location=location, description=description)
            
            # Save to database
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO meters_config 
                (meter_id, name, host, port, unit_id, location, description, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (meter_id, name, host, port, unit_id, location, description))
            
            conn.commit()
            conn.close()
            
            # Add to meters dictionary
            self.meters[meter_id] = meter
            return True
            
        except Exception as e:
            st.error(f"Error adding meter: {e}")
            return False
    
    def remove_meter(self, meter_id):
        """Remove a meter from the system"""
        try:
            # Disconnect if connected
            if meter_id in self.meters:
                self.meters[meter_id].disconnect()
                del self.meters[meter_id]
            
            # Remove from database
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM meters_config WHERE meter_id = ?', (meter_id,))
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            st.error(f"Error removing meter: {e}")
            return False
    
    def load_meters_config(self):
        """Load meters configuration from database"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM meters_config')
            rows = cursor.fetchall()
            
            for row in rows:
                meter_id, name, host, port, unit_id, location, description = row[:7]
                meter = PAC3200Meter(meter_id, name, host, port, unit_id,
                                    location=location or "", description=description or "")
                self.meters[meter_id] = meter
            
            conn.close()
            
        except Exception as e:
            # Table might not exist yet
            pass
    
    def save_reading(self, meter_id, data):
        """Save reading for a specific meter"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Filter out None values and add meter_id
            valid_data = {k: v for k, v in data.items() if v is not None and not (isinstance(v, float) and np.isnan(v))}
            valid_data['meter_id'] = meter_id
            
            # Get existing columns from the database
            cursor.execute("PRAGMA table_info(pac3200_readings)")
            existing_columns = [row[1] for row in cursor.fetchall()]
            
            # Filter data to only include existing columns
            db_columns = [col for col in existing_columns if col not in ['id', 'timestamp']]
            filtered_data = {k: v for k, v in valid_data.items() if k in db_columns}
            
            if not filtered_data:
                return None
            
            columns = list(filtered_data.keys())
            values = list(filtered_data.values())
            
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join(columns)
            
            query = f'''
                INSERT INTO pac3200_readings ({column_names}) 
                VALUES ({placeholders})
            '''
            
            cursor.execute(query, values)
            conn.commit()
            record_id = cursor.lastrowid
            conn.close()
            
            return record_id
            
        except Exception as e:
            st.error(f"Database save error: {e}")
            return None
    
    def get_meter_readings(self, meter_id, hours=24):
        """Get readings for a specific meter"""
        try:
            conn = sqlite3.connect(self.db_name)
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            query = '''
                SELECT * FROM pac3200_readings 
                WHERE meter_id = ? AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp DESC
            '''
            
            df = pd.read_sql_query(query, conn, params=[meter_id, start_time, end_time])
            conn.close()
            return df
            
        except Exception as e:
            return pd.DataFrame()
    
    def get_all_meters_latest(self):
        """Get latest reading for all meters"""
        try:
            conn = sqlite3.connect(self.db_name)
            
            query = '''
                SELECT r.*, m.name, m.location
                FROM pac3200_readings r
                INNER JOIN meters_config m ON r.meter_id = m.meter_id
                INNER JOIN (
                    SELECT meter_id, MAX(timestamp) as max_timestamp
                    FROM pac3200_readings
                    GROUP BY meter_id
                ) latest ON r.meter_id = latest.meter_id AND r.timestamp = latest.max_timestamp
                ORDER BY m.name
            '''
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
            
        except Exception as e:
            return pd.DataFrame()
    
    def get_aggregated_data(self, hours=24):
        """Get aggregated data from all meters"""
        try:
            conn = sqlite3.connect(self.db_name)
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            query = '''
                SELECT 
                    timestamp,
                    SUM(Total_Active_Power) as Total_System_Power,
                    AVG(Frequency) as Avg_Frequency,
                    AVG(Total_Power_Factor) as Avg_Power_Factor,
                    COUNT(DISTINCT meter_id) as Active_Meters
                FROM pac3200_readings
                WHERE timestamp BETWEEN ? AND ?
                GROUP BY timestamp
                ORDER BY timestamp DESC
            '''
            
            df = pd.read_sql_query(query, conn, params=[start_time, end_time])
            conn.close()
            return df
            
        except Exception as e:
            return pd.DataFrame()

def create_meter_overview_card(meter, latest_data):
    """Create an overview card for a single meter"""
    status_color = "🟢" if meter.connected else "🔴"
    
    with st.container():
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
        
        with col1:
            st.markdown(f"**{status_color} {meter.name}**")
            if meter.location:
                st.caption(f"📍 {meter.location}")
        
        with col2:
            # Handle both dict and pandas Series
            if isinstance(latest_data, pd.Series):
                power = latest_data.get('Total_Active_Power', 0) if not latest_data.empty else 0
            elif isinstance(latest_data, dict):
                power = latest_data.get('Total_Active_Power', 0) if latest_data else 0
            else:
                power = 0
            power = power if power and not pd.isna(power) else 0
            st.metric("Power", f"{power:.1f} W")
        
        with col3:
            if isinstance(latest_data, pd.Series):
                voltage = latest_data.get('Average_Voltage_Vph_n', 0) if not latest_data.empty else 0
            elif isinstance(latest_data, dict):
                voltage = latest_data.get('Average_Voltage_Vph_n', 0) if latest_data else 0
            else:
                voltage = 0
            voltage = voltage if voltage and not pd.isna(voltage) else 0
            st.metric("Voltage", f"{voltage:.1f} V")
        
        with col4:
            if isinstance(latest_data, pd.Series):
                current = latest_data.get('Average_Current', 0) if not latest_data.empty else 0
            elif isinstance(latest_data, dict):
                current = latest_data.get('Average_Current', 0) if latest_data else 0
            else:
                current = 0
            current = current if current and not pd.isna(current) else 0
            st.metric("Current", f"{current:.1f} A")
        
        with col5:
            if isinstance(latest_data, pd.Series):
                pf = latest_data.get('Total_Power_Factor', 0) if not latest_data.empty else 0
            elif isinstance(latest_data, dict):
                pf = latest_data.get('Total_Power_Factor', 0) if latest_data else 0
            else:
                pf = 0
            pf = pf if pf and not pd.isna(pf) else 0
            st.metric("PF", f"{pf:.2f}")

def create_comparison_chart(dashboard, meter_ids, parameter, hours=24):
    """Create comparison chart for multiple meters"""
    fig = go.Figure()
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
    
    for i, meter_id in enumerate(meter_ids):
        df = dashboard.get_meter_readings(meter_id, hours)
        if not df.empty and parameter in df.columns:
            meter_name = dashboard.meters[meter_id].name if meter_id in dashboard.meters else meter_id
            
            fig.add_trace(go.Scatter(
                x=pd.to_datetime(df['timestamp']),
                y=df[parameter],
                mode='lines+markers',
                name=meter_name,
                line=dict(width=2, color=colors[i % len(colors)]),
                marker=dict(size=4)
            ))
    
    fig.update_layout(
        title=f'{parameter.replace("_", " ")} Comparison',
        xaxis_title='Time',
        yaxis_title=parameter.replace("_", " "),
        hovermode='x unified',
        height=400,
        showlegend=True
    )
    
    return fig

def main():
    st.title("⚡ Multi-Meter PAC3200 Energy Monitoring Dashboard")
    st.markdown("---")
    
    # Initialize session state
    if 'dashboard' not in st.session_state:
        st.session_state.dashboard = MultiMeterDashboard()
    if 'selected_meters' not in st.session_state:
        st.session_state.selected_meters = []
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = False
    
    dashboard = st.session_state.dashboard
    
    # Sidebar - Meter Management
    st.sidebar.header("🔧 Meter Management")
    
    # Database management section
    with st.sidebar.expander("🗄️ Database Management", expanded=False):
        if st.button("🔄 Reset Database", help="This will clear all data and recreate tables"):
            if st.checkbox("I understand this will delete all data"):
                try:
                    # Close any existing connections
                    for meter in dashboard.meters.values():
                        meter.disconnect()
                    
                    # Drop and recreate tables
                    conn = sqlite3.connect(dashboard.db_name)
                    cursor = conn.cursor()
                    cursor.execute("DROP TABLE IF EXISTS pac3200_readings")
                    cursor.execute("DROP TABLE IF EXISTS pac3200_readings_backup")
                    cursor.execute("DROP TABLE IF EXISTS meters_config")
                    conn.commit()
                    conn.close()
                    
                    # Reinitialize
                    dashboard.init_database()
                    dashboard.meters = {}
                    st.session_state.selected_meters = []
                    
                    st.success("✅ Database reset successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error resetting database: {e}")
        
        if st.button("🔍 Check Database Schema"):
            try:
                conn = sqlite3.connect(dashboard.db_name)
                cursor = conn.cursor()
                
                # Check tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                st.info(f"Tables: {[t[0] for t in tables]}")
                
                # Check columns in pac3200_readings
                cursor.execute("PRAGMA table_info(pac3200_readings)")
                columns = cursor.fetchall()
                important_cols = [col[1] for col in columns if col[1] in ['meter_id', 'device_id', 'timestamp']]
                st.info(f"Key columns: {important_cols}")
                
                conn.close()
            except Exception as e:
                st.error(f"Error checking schema: {e}")
    
    # Add new meter section
    with st.sidebar.expander("➕ Add New Meter", expanded=False):
        meter_id = st.text_input("Meter ID", value=f"meter_{len(dashboard.meters) + 1}")
        meter_name = st.text_input("Meter Name", value=f"PAC3200 #{len(dashboard.meters) + 1}")
        meter_host = st.text_input("IP Address", value="192.168.0.101")
        meter_port = st.number_input("Port", value=502, min_value=1, max_value=65535)
        meter_unit = st.number_input("Unit ID", value=1, min_value=1, max_value=255)
        meter_location = st.text_input("Location (optional)", value="")
        meter_description = st.text_area("Description (optional)", value="")
        
        if st.button("Add Meter", type="primary"):
            if dashboard.add_meter(meter_id, meter_name, meter_host, meter_port, 
                                    meter_unit, meter_location, meter_description):
                st.success(f"✅ Added meter: {meter_name}")
                st.rerun()
            else:
                st.error("Failed to add meter")
    
    # List existing meters
    st.sidebar.markdown("### 📊 Configured Meters")
    
    if dashboard.meters:
        for meter_id, meter in dashboard.meters.items():
            with st.sidebar.container():
                col1, col2, col3 = st.sidebar.columns([1, 1, 1])
                
                with col1:
                    # Checkbox for selection
                    selected = st.checkbox(meter.name, key=f"select_{meter_id}", 
                                           value=meter_id in st.session_state.selected_meters)
                    if selected and meter_id not in st.session_state.selected_meters:
                        st.session_state.selected_meters.append(meter_id)
                    elif not selected and meter_id in st.session_state.selected_meters:
                        st.session_state.selected_meters.remove(meter_id)
                
                with col2:
                    # Connect/Disconnect button
                    if meter.connected:
                        if st.button("🔌", key=f"disconnect_{meter_id}", help="Disconnect"):
                            meter.disconnect()
                            st.rerun()
                    else:
                        if st.button("🔗", key=f"connect_{meter_id}", help="Connect"):
                            if meter.connect():
                                st.success(f"Connected to {meter.name}")
                            else:
                                st.error(f"Failed to connect to {meter.name}")
                            st.rerun()
                
                with col3:
                    # Remove button
                    if st.button("🗑️", key=f"remove_{meter_id}", help="Remove meter"):
                        if dashboard.remove_meter(meter_id):
                            st.success(f"Removed {meter.name}")
                            if meter_id in st.session_state.selected_meters:
                                st.session_state.selected_meters.remove(meter_id)
                            st.rerun()
                
                # Show meter details
                st.sidebar.caption(f"📡 {meter.host}:{meter.port} (Unit {meter.unit_id})")
                if meter.location:
                    st.sidebar.caption(f"📍 {meter.location}")
                
                st.sidebar.markdown("---")
    else:
        st.sidebar.info("No meters configured. Add a meter to get started.")
    
    # Data collection controls
    st.sidebar.markdown("### 📊 Data Collection")
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("📥 Collect All", disabled=not dashboard.meters):
            collected = 0
            failed = 0
            
            for meter_id, meter in dashboard.meters.items():
                if meter.connected or not MODBUS_AVAILABLE:
                    with st.spinner(f"Reading {meter.name}..."):
                        data = meter.read_all_parameters()
                        if data:
                            record_id = dashboard.save_reading(meter_id, data)
                            if record_id:
                                collected += 1
                            else:
                                failed += 1
                        else:
                            failed += 1
                else:
                    failed += 1
            
            if collected > 0:
                st.sidebar.success(f"✅ Collected data from {collected} meter(s)")
            if failed > 0:
                st.sidebar.warning(f"⚠️ Failed to collect from {failed} meter(s)")
            
            st.rerun()
    
    with col2:
        if st.button("📥 Collect Selected", disabled=not st.session_state.selected_meters):
            collected = 0
            failed = 0
            
            for meter_id in st.session_state.selected_meters:
                if meter_id in dashboard.meters:
                    meter = dashboard.meters[meter_id]
                    if meter.connected or not MODBUS_AVAILABLE:
                        with st.spinner(f"Reading {meter.name}..."):
                            data = meter.read_all_parameters()
                            if data:
                                record_id = dashboard.save_reading(meter_id, data)
                                if record_id:
                                    collected += 1
                                else:
                                    failed += 1
                            else:
                                failed += 1
                    else:
                        failed += 1
            
            if collected > 0:
                st.sidebar.success(f"✅ Collected data from {collected} meter(s)")
            if failed > 0:
                st.sidebar.warning(f"⚠️ Failed to collect from {failed} meter(s)")
            
            st.rerun()
    
    # Auto refresh
    st.session_state.auto_refresh = st.sidebar.checkbox("🔄 Auto Refresh (30s)", value=st.session_state.auto_refresh)
    
    # Generate sample data for demo
    if not MODBUS_AVAILABLE:
        if st.sidebar.button("🎲 Generate Sample Data"):
            with st.spinner("Generating sample data..."):
                for meter_id, meter in dashboard.meters.items():
                    for i in range(10):
                        data = meter.read_all_parameters()
                        dashboard.save_reading(meter_id, data)
                        time.sleep(0.1)
                st.sidebar.success("Sample data generated!")
                st.rerun()
    
    # Time range selector
    st.sidebar.markdown("### ⏰ Time Range")
    time_range = st.sidebar.selectbox(
        "Select time range",
        ["Last Hour", "Last 6 Hours", "Last 24 Hours", "Last 7 Days"],
        index=2
    )
    
    time_mapping = {
        "Last Hour": 1,
        "Last 6 Hours": 6,
        "Last 24 Hours": 24,
        "Last 7 Days": 168
    }
    
    hours = time_mapping[time_range]
    
    # Main dashboard
    if not dashboard.meters:
        st.info("👋 Welcome! Start by adding a meter in the sidebar.")
        return
    
    # Create tabs
    tabs = ["🏠 Overview", "📊 Individual Meters", "📈 Comparison", "⚡ System Analysis", "📋 Data Export"]
    tab1, tab2, tab3, tab4, tab5 = st.tabs(tabs)
    
    with tab1:
        st.header("System Overview")
        
        # Get latest data for all meters
        latest_df = dashboard.get_all_meters_latest()
        
        if not latest_df.empty:
            # System-wide metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_power = latest_df['Total_Active_Power'].sum()
                st.metric("Total System Power", f"{total_power:.1f} W")
            
            with col2:
                avg_frequency = latest_df['Frequency'].mean()
                st.metric("Average Frequency", f"{avg_frequency:.2f} Hz")
            
            with col3:
                avg_pf = latest_df['Total_Power_Factor'].mean()
                st.metric("Average Power Factor", f"{avg_pf:.3f}")
            
            with col4:
                connected_count = sum(1 for m in dashboard.meters.values() if m.connected)
                st.metric("Connected Meters", f"{connected_count}/{len(dashboard.meters)}")
            
            st.markdown("---")
            
            # Meter overview cards
            st.subheader("Meter Status")
            
            for _, row in latest_df.iterrows():
                meter_id = row['meter_id']
                if meter_id in dashboard.meters:
                    meter = dashboard.meters[meter_id]
                    create_meter_overview_card(meter, row)
                    st.markdown("---")
            
            # System power distribution pie chart
            col1, col2 = st.columns(2)
            
            with col1:
                fig_pie = go.Figure(data=[go.Pie(
                    labels=latest_df['name'].tolist(),
                    values=latest_df['Total_Active_Power'].tolist(),
                    hole=0.4
                )])
                fig_pie.update_layout(
                    title="Power Distribution by Meter",
                    height=400
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Aggregated trends
                agg_df = dashboard.get_aggregated_data(hours)
                if not agg_df.empty:
                    fig_trend = go.Figure()
                    fig_trend.add_trace(go.Scatter(
                        x=pd.to_datetime(agg_df['timestamp']),
                        y=agg_df['Total_System_Power'],
                        mode='lines+markers',
                        name='Total System Power',
                        line=dict(width=3, color='#FF6B6B')
                    ))
                    fig_trend.update_layout(
                        title="System Power Trend",
                        xaxis_title="Time",
                        yaxis_title="Power (W)",
                        height=400
                    )
                    st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.warning("No data available. Collect some readings first.")
    
    with tab2:
        st.header("Individual Meter Analysis")
        
        if dashboard.meters:
            selected_meter = st.selectbox(
                "Select Meter",
                options=list(dashboard.meters.keys()),
                format_func=lambda x: dashboard.meters[x].name
            )
            
            if selected_meter:
                meter = dashboard.meters[selected_meter]
                df = dashboard.get_meter_readings(selected_meter, hours)
                
                if not df.empty:
                    # Meter information
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.info(f"**Name:** {meter.name}")
                    with col2:
                        st.info(f"**Location:** {meter.location or 'Not specified'}")
                    with col3:
                        status = "🟢 Connected" if meter.connected else "🔴 Disconnected"
                        st.info(f"**Status:** {status}")
                    
                    # Latest readings
                    st.subheader("Current Readings")
                    latest = df.iloc[0]
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        # Safe value extraction with null checking
                        total_power = latest.get('Total_Active_Power', 0)
                        total_power = total_power if total_power and not pd.isna(total_power) else 0
                        frequency = latest.get('Frequency', 0)
                        frequency = frequency if frequency and not pd.isna(frequency) else 0
                        
                        st.metric("Total Power", f"{total_power:.1f} W")
                        st.metric("Frequency", f"{frequency:.2f} Hz")
                    
                    with col2:
                        v1 = latest.get('V1_N_Voltage', 0)
                        v1 = v1 if v1 and not pd.isna(v1) else 0
                        v2 = latest.get('V2_N_Voltage', 0)
                        v2 = v2 if v2 and not pd.isna(v2) else 0
                        v3 = latest.get('V3_N_Voltage', 0)
                        v3 = v3 if v3 and not pd.isna(v3) else 0
                        
                        st.metric("V1 Voltage", f"{v1:.1f} V")
                        st.metric("V2 Voltage", f"{v2:.1f} V")
                        st.metric("V3 Voltage", f"{v3:.1f} V")
                    
                    with col3:
                        l1 = latest.get('L1_Current', 0)
                        l1 = l1 if l1 and not pd.isna(l1) else 0
                        l2 = latest.get('L2_Current', 0)
                        l2 = l2 if l2 and not pd.isna(l2) else 0
                        l3 = latest.get('L3_Current', 0)
                        l3 = l3 if l3 and not pd.isna(l3) else 0
                        
                        st.metric("L1 Current", f"{l1:.2f} A")
                        st.metric("L2 Current", f"{l2:.2f} A")
                        st.metric("L3 Current", f"{l3:.2f} A")
                    
                    with col4:
                        pf = latest.get('Total_Power_Factor', 0)
                        pf = pf if pf and not pd.isna(pf) else 0
                        energy = latest.get('Total_Active_Energy', 0)
                        energy = energy if energy and not pd.isna(energy) else 0
                        
                        st.metric("Power Factor", f"{pf:.3f}")
                        st.metric("Total Energy", f"{energy:.0f} Wh")
                    
                    # Trends
                    st.subheader("Trends")
                    
                    # Voltage trend
                    fig_voltage = go.Figure()
                    for phase in ['V1_N_Voltage', 'V2_N_Voltage', 'V3_N_Voltage']:
                        if phase in df.columns:
                            fig_voltage.add_trace(go.Scatter(
                                x=pd.to_datetime(df['timestamp']),
                                y=df[phase],
                                mode='lines',
                                name=phase.replace('_', ' ')
                            ))
                    fig_voltage.update_layout(
                        title="Voltage Trends",
                        xaxis_title="Time",
                        yaxis_title="Voltage (V)",
                        height=400
                    )
                    st.plotly_chart(fig_voltage, use_container_width=True)
                    
                    # Power trend
                    if 'Total_Active_Power' in df.columns:
                        fig_power = go.Figure()
                        fig_power.add_trace(go.Scatter(
                            x=pd.to_datetime(df['timestamp']),
                            y=df['Total_Active_Power'],
                            mode='lines+markers',
                            name='Total Active Power',
                            line=dict(width=3, color='#FF6B6B')
                        ))
                        fig_power.update_layout(
                            title="Power Consumption",
                            xaxis_title="Time",
                            yaxis_title="Power (W)",
                            height=400
                        )
                        st.plotly_chart(fig_power, use_container_width=True)
                else:
                    st.warning(f"No data available for {meter.name}")
        else:
            st.info("No meters configured. Add meters in the sidebar.")
    
    with tab3:
        st.header("Multi-Meter Comparison")
        
        if len(dashboard.meters) > 1:
            # Select meters to compare
            compare_meters = st.multiselect(
                "Select meters to compare",
                options=list(dashboard.meters.keys()),
                format_func=lambda x: dashboard.meters[x].name,
                default=list(dashboard.meters.keys())[:min(3, len(dashboard.meters))]
            )
            
            if compare_meters:
                # Select parameter to compare
                param_groups = {
                    "Power": ['Total_Active_Power', 'Total_Reactive_Power', 'Total_Apparent_Power'],
                    "Voltage": ['V1_N_Voltage', 'V2_N_Voltage', 'V3_N_Voltage', 'Average_Voltage_Vph_n'],
                    "Current": ['L1_Current', 'L2_Current', 'L3_Current', 'Average_Current'],
                    "Power Factor": ['Total_Power_Factor', 'L1_Power_Factor', 'L2_Power_Factor', 'L3_Power_Factor'],
                    "Energy": ['Total_Active_Energy', 'Total_Reactive_Energy'],
                    "Quality": ['Frequency', 'THD_R_Voltage_1', 'THD_R_Current_1']
                }
                
                col1, col2 = st.columns(2)
                with col1:
                    param_group = st.selectbox("Parameter Group", list(param_groups.keys()))
                with col2:
                    parameter = st.selectbox("Parameter", param_groups[param_group])
                
                # Create comparison chart
                fig = create_comparison_chart(dashboard, compare_meters, parameter, hours)
                st.plotly_chart(fig, use_container_width=True)
                
                # Comparison table
                st.subheader("Current Values Comparison")
                comparison_data = []
                
                for meter_id in compare_meters:
                    df = dashboard.get_meter_readings(meter_id, hours)
                    if not df.empty:
                        latest = df.iloc[0]
                        comparison_data.append({
                            'Meter': dashboard.meters[meter_id].name,
                            'Location': dashboard.meters[meter_id].location,
                            parameter: latest.get(parameter, 0)
                        })
                
                if comparison_data:
                    comparison_df = pd.DataFrame(comparison_data)
                    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
        else:
            st.info("Add more meters to enable comparison features.")
    
    with tab4:
        st.header("System Analysis")
        
        # Aggregate statistics
        st.subheader("System Statistics")
        
        all_data = []
        for meter_id in dashboard.meters.keys():
            df = dashboard.get_meter_readings(meter_id, hours)
            if not df.empty:
                df['meter_name'] = dashboard.meters[meter_id].name
                all_data.append(df)
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            
            # System health metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_energy = combined_df.groupby('meter_name')['Total_Active_Energy'].last().sum()
                st.metric("Total System Energy", f"{total_energy:.0f} Wh")
            
            with col2:
                avg_efficiency = combined_df['Total_Power_Factor'].mean()
                efficiency_status = "🟢" if avg_efficiency > 0.9 else "🟡" if avg_efficiency > 0.8 else "🔴"
                st.metric("System Efficiency", f"{efficiency_status} {avg_efficiency:.3f}")
            
            with col3:
                max_demand = combined_df.groupby('timestamp')['Total_Active_Power'].sum().max()
                st.metric("Peak Demand", f"{max_demand:.1f} W")
            
            with col4:
                load_factor = combined_df.groupby('timestamp')['Total_Active_Power'].sum().mean() / max_demand if max_demand > 0 else 0
                st.metric("Load Factor", f"{load_factor:.3f}")
            
            # Alert conditions
            st.subheader("System Alerts")
            
            alerts = []
            latest_df = dashboard.get_all_meters_latest()
            
            if not latest_df.empty:
                # Check for power factor issues
                low_pf_meters = latest_df[latest_df['Total_Power_Factor'] < 0.85]
                if not low_pf_meters.empty:
                    for _, meter in low_pf_meters.iterrows():
                        alerts.append(f"⚠️ Low power factor on {meter['name']}: {meter['Total_Power_Factor']:.3f}")
                
                # Check for frequency deviations
                freq_issues = latest_df[(latest_df['Frequency'] < 49.5) | (latest_df['Frequency'] > 50.5)]
                if not freq_issues.empty:
                    for _, meter in freq_issues.iterrows():
                        alerts.append(f"⚠️ Frequency deviation on {meter['name']}: {meter['Frequency']:.2f} Hz")
                
                # Check for high THD
                for col in ['THD_R_Voltage_1', 'THD_R_Current_1']:
                    if col in latest_df.columns:
                        high_thd = latest_df[latest_df[col] > 5]
                        if not high_thd.empty:
                            for _, meter in high_thd.iterrows():
                                alerts.append(f"⚠️ High {col.replace('_', ' ')} on {meter['name']}: {meter[col]:.2f}%")
            
            if alerts:
                for alert in alerts[:10]:  # Show max 10 alerts
                    st.warning(alert)
            else:
                st.success("✅ All systems operating normally")
            
            # Load distribution chart
            st.subheader("Load Distribution Over Time")
            
            # FIX: Convert 'timestamp' column to datetime before resampling
            combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
            
            hourly_data = combined_df.set_index('timestamp').resample('1H')['Total_Active_Power'].sum().reset_index()
            
            fig_load = go.Figure()
            fig_load.add_trace(go.Bar(
                x=hourly_data['timestamp'],
                y=hourly_data['Total_Active_Power'],
                marker_color='#4ECDC4'
            ))
            fig_load.update_layout(
                title="Hourly Energy Consumption",
                xaxis_title="Time",
                yaxis_title="Energy (Wh)",
                height=400
            )
            st.plotly_chart(fig_load, use_container_width=True)
    
    with tab5:
        st.header("Data Export")
        
        # Export options
        export_option = st.radio(
            "Select export option",
            ["All meters - Latest readings", "All meters - Historical data", "Selected meters - Historical data", "Raw database export"]
        )
        
        if export_option == "All meters - Latest readings":
            df_export = dashboard.get_all_meters_latest()
        elif export_option == "All meters - Historical data":
            all_data = []
            for meter_id in dashboard.meters.keys():
                df = dashboard.get_meter_readings(meter_id, hours)
                if not df.empty:
                    df['meter_name'] = dashboard.meters[meter_id].name
                    all_data.append(df)
            df_export = pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()
        elif export_option == "Selected meters - Historical data":
            selected_export = st.multiselect(
                "Select meters to export",
                options=list(dashboard.meters.keys()),
                format_func=lambda x: dashboard.meters[x].name
            )
            all_data = []
            for meter_id in selected_export:
                df = dashboard.get_meter_readings(meter_id, hours)
                if not df.empty:
                    df['meter_name'] = dashboard.meters[meter_id].name
                    all_data.append(df)
            df_export = pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()
        else:
            # Raw database export
            conn = sqlite3.connect(dashboard.db_name)
            df_export = pd.read_sql_query("SELECT * FROM pac3200_readings ORDER BY timestamp DESC", conn)
            conn.close()
        
        if not df_export.empty:
            st.dataframe(df_export.head(100), use_container_width=True)
            
            # Download button
            csv = df_export.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"pac3200_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("No data available for export.")
    
    # Auto refresh
    if st.session_state.auto_refresh:
        time.sleep(30)
        st.rerun()

if __name__ == "__main__":
    main()

