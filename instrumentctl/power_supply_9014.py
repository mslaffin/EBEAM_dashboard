import serial
import threading
import time

class PowerSupply9014:
    def __init__(self, port, baudrate=9600, timeout=1, messages_frame=None, debug_mode=False):
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        self.debug_mode = debug_mode
        self.messages_frame = messages_frame

    def send_command(self, command):
        """Send a command to the power supply and read the response."""
        if self.debug_mode:
            return "Mock response based on " + command
        try:
            self.ser.write(f"{command}\r".encode())
            response = self.ser.readline().decode().strip()
            if not response:
                raise ValueError("No response received from the device.")
            return response
        except serial.SerialException as e:
            self.log_message(f"Serial error: {e}")
            return None
        except ValueError as e:
            self.log_message(f"Error processing response for command '{command}': {str(e)}")
            return None

    def set_output(self, state):
        """Set the output on/off."""
        command = f"SOUT{state}"
        return self.send_command(command)

    def get_output_status(self):
        """Get the output status."""
        command = "GOUT"
        return self.send_command(command)

    def set_voltage(self, preset, voltage):
        """Set the output voltage. Assumes input voltage is in a form such as: 5.00"""
        formatted_voltage = int(voltage * 100)
        command = f"VOLT {preset}{formatted_voltage:04d}"
    
        response = self.send_command(command)
        if response and response.strip() == "OK":
            return True
        else:
            error_message = "No response" if response is None else response
            self.log_message(f"Error setting voltage: {error_message}")
            return False
    
    def set_current(self, preset, current):
        """Set the output current."""
        formatted_current = int(current * 100)
        command = f"CURR {preset}{formatted_current:04d}"
        response = self.send_command(command)
        if response and response.strip() == "OK":
            return True
        else:
            error_message = "No response" if response is None else response
            self.log_message(f"Error setting current: {error_message}")
            return False

    def ramp_voltage(self, target_voltage, ramp_rate=0.01, callback=None):
        """
        Slowly ramp the voltage to the target voltage at the specified ramp rate.
        Runs in a separate thread to avoid blocking the GUI
        
        Args:
            target_voltage (float): The target voltage to reach in volts.
            ramp_rate (float): The rate at which to change the voltage in volts per second.
            callback (function): Optional function to call when ramping is complete.
        """        
        thread = threading.Thread(target=self._ramp_voltage_thread,
                                  args=(target_voltage, ramp_rate, callback))
        thread.start()

    def _ramp_voltage_thread(self, target_voltage, ramp_rate, callback):
        current_voltage = 0.0  # Starting voltage, adjust if you can fetch from the PSU.
        step_size = 0.1  # Voltage step in volts.
        step_delay = step_size / ramp_rate  # Delay in seconds.

        while current_voltage < target_voltage:
            next_voltage = min(current_voltage + step_size, target_voltage)
            if not self.set_voltage(1, next_voltage):  # Assume preset 1
                self.log_message(f"Failed to set voltage to {next_voltage:.2f}V.")
                if callback:
                    callback(False)
                return

            # self.log_message(f"Voltage set to {next_voltage:.2f}V.")
            time.sleep(step_delay)
            current_voltage = next_voltage

        self.log_message("Target voltage reached.")
        if callback:
            callback(True)

    
    def set_over_voltage_protection(self, ovp):
        """Set the over voltage protection value."""
        command = f"SOVP{ovp}"
        return self.send_command(command)

    def get_display_readings(self):
        """Get the display readings for voltage and current mode."""
        command = "GETD"
        return self.send_command(command)
    
    def get_voltage_current_mode(self):
        """
        Extract voltage and current from the power supply reading.
        
        Returns:
        (voltage, current, mode)
        """
        reading = self.get_display_readings()
        if reading:
            # Example response: '050001000\r\nOK\r\n' pg. 5 programming manual
            try:
                # Remove any trailing newlines or carriage returns
                reading = reading.strip()
                # Assuming the response format is consistent with the example '050001000OK'
                voltage = float(reading[0:5]) / 1000  # Convert to float and adjust scale
                current = float(reading[5:10]) / 1000  # Convert to float and adjust scale
                mode = 'CV Mode' if reading[10] == '0' else 'CC Mode'
                return voltage, current, mode
            except (ValueError, IndexError) as e:
                self.log_message(f"Error parsing voltage/current/mode: {str(e)}")
                return 0.0, 0.0, "Err"
        else:
            self.log_message("Failed to get display readings.")
            return 0.0, 0.0, "Err"

    def set_over_current_protection(self, ocp):
        """Set the over current protection value."""
        command = f"SOCP{ocp}"
        return self.send_command(command)

    def get_over_voltage_protection(self):
        """Get the upper limit of the output voltage."""
        command = "GOVP"
        return self.send_command(command)

    def get_over_current_protection(self):
        """Get the upper limit of the output current."""
        command = "GOCP"
        return self.send_command(command)

    def set_preset(self, preset, voltage, current):
        """Set the voltage and current for a preset."""
        command = f"SETD{preset}{voltage}{current}"
        return self.send_command(command)

    def get_settings(self, preset):
        """Get settings of a preset."""
        command = f"GETS{preset}"
        return self.send_command(command)

    def get_preset_selection(self):
        """Get the current preset selection."""
        command = "GABC"
        return self.send_command(command)

    def set_preset_selection(self, preset):
        """Set the ABC select."""
        command = f"SABC{preset}"
        return self.send_command(command)

    def get_delta_time(self, index):
        """Get delta time setting value."""
        command = f"GDLT{index}"
        return self.send_command(command)

    def set_delta_time(self, index, time):
        """Set delta time."""
        command = f"SDLT{index}{time:02}"
        return self.send_command(command)

    def get_sw_time(self):
        """Get SW time."""
        command = "GSWT"
        return self.send_command(command)

    def set_sw_time(self, sw_time):
        """Set SW time."""
        command = f"SSWT{sw_time:03}"
        return self.send_command(command)

    def run_sw(self, first, end):
        """Run SW running."""
        command = f"RUNP{first}{end}"
        return self.send_command(command)

    def stop_sw(self):
        """Stop SW running."""
        command = "STOP"
        return self.send_command(command)

    def disable_keyboard(self):
        """Disable keyboard."""
        command = "SESS"
        return self.send_command(command)

    def enable_keyboard(self):
        """Enable keyboard."""
        command = "ENDS"
        return self.send_command(command)

    def get_all_information(self):
        """Get all information from the power supply."""
        command = "GALL"
        return self.send_command(command)

    def configure_presets(self, setv1, seti1, swtime1, setv2, seti2, swtime2, setv3, seti3, swtime3):
        """Configure presets for voltage, current, and SW time."""
        command = f"SETM{setv1:04}{seti1:04}{swtime1:03}{setv2:04}{seti2:04}{swtime2:03}{setv3:04}{seti3:04}{swtime3:03}"
        return self.send_command(command)

    def close(self):
        """Close the serial connection."""
        self.ser.close()

    def log_message(self, message):
        if hasattr(self, 'messages_frame') and self.messages_frame:
            self.messages_frame.log_message(message)
        else:
            self.parent.after(0, print(message))