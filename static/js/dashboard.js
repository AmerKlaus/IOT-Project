// Track fan status received from server
let fanStatus = false;
let fanFrame = 0; // To track the current frame of the fan animation
const totalFrames = 7; // Total number of fan images
let spinInterval;
const gaugeElementTemp = document.getElementById("temp");
const gaugeElementHum = document.getElementById("hum");

async function fetchRfidData() {
  try {
    const response = await fetch("http://0.0.0.0:5000/sensor_data/rfid");
    const data = await response.json();
    if (data.success) {
      const rfidTag = data.rfid_tag;
      //document.getElementById('rfid-tag-value').textContent = rfidTag;
      fetchUserProfile(rfidTag);
      updateDashboard();
    } else {
      document.getElementById("rfid-tag-value").textContent =
        "No RFID tag available";
    }
  } catch (error) {
    console.error("Error fetching RFID data:", error);
  }
}

async function fetchUserProfile() {
  try {
    const response = await fetch("http://0.0.0.0:5000/user_profile");
    const data = await response.json();
    if (data.success) {
      const profile = data.profile;
      document.getElementById("profile").textContent = profile.user_name;
      document.getElementById("temperature").textContent =
        profile.temperature_threshold;
      document.getElementById("light").textContent =
        profile.light_intensity_threshold;
      document.getElementById("pfp").src = profile.user_picture;
    } else {
      document.getElementById("profile").textContent = "User not found";
    }
  } catch (error) {
    console.error("Error fetching user profile:", error);
  }
}

// Polling every 3 seconds to check for RFID data
setInterval(fetchRfidData, 3000);

function setGaugeValueTemp(gauge, value) {
  if (value < 0 || value > 1) {
    return;
  }

  gauge.querySelector(".gauge__fill").style.transform = `rotate(${
    value / 2
  }turn)`;
  gauge.querySelector(".gauge__cover").textContent = `${(value * 100).toFixed(2)}°C`;
}

function setGaugeValueHum(gauge, value) {
  if (value < 0 || value > 1) {
    return;
  }

  gauge.querySelector(".gauge__fill").style.transform = `rotate(${
    value / 2
  }turn)`;
  gauge.querySelector(".gauge__cover").textContent = `${(value * 100).toFixed(2)}%`;
}

function updateDashboard() {
  fetch("http://0.0.0.0:5000/sensor_data")
    .then((response) => response.json())
    .then((data) => {
      const {
        temperature,
        humidity,
        fanOn,
        light_intensity,
        led_status,
        email_sent,
      } = data;

      // Update gauges
      setGaugeValueTemp(gaugeElementTemp, temperature / 100);
      setGaugeValueHum(gaugeElementHum, humidity / 100);

      // Update fan status
      fanStatus = fanOn;
      updateFanIcon();

      // Update additional sensor data
      document.getElementById("lightIntensity").innerText = light_intensity;
      document.getElementById("ledStatus").innerText = led_status;
      document.getElementById("emailStatus").innerText = email_sent;

      //turn on and off the lightbulb
      if (led_status == "ON") {
        document.getElementById("lightbulb").className = "bx bxs-bulb";
      }
      else {
        document.getElementById("lightbulb").className = "bx bx-bulb";
      }

      // Convert light intensity to a number and calculate progress bar value
      const lightIntensity = Number(light_intensity);
      const value = lightIntensity / 40; // Adjust division factor as needed

      // Update the progress bar
      const progress = document.querySelector(".progress");
      progress.style.setProperty("--progress", `${value}%`);
    })
    .catch((error) => console.error("Error fetching data:", error));
    
}

// Update the fan icon display based on fanStatus
function updateFanIcon() {
  const fanIcon = document.getElementById("fanIcon");
  const fanStatusText = document.getElementById("fanStatus");

  if (fanStatus) {
    fanStatusText.textContent = "Status: ON"; // Update fan status text
    cycleFanFrames(); // Start spinning animation
  } else {
    fanStatusText.textContent = "Status: OFF"; // Update fan status text
    fanFrame = 0;
    fanIcon.src = `/static/images/fan1.png`; // Show the first image when fan is off
    clearInterval(spinInterval); // Stop the spinning interval
  }
}

// Function to animate the fan
function cycleFanFrames() {
  const fanIcon = document.getElementById("fanIcon");
  clearInterval(spinInterval); // Clear any existing intervals

  spinInterval = setInterval(() => {
    fanFrame = (fanFrame + 1) % totalFrames; // Cycle through frames
    fanIcon.src = `/static/images/fan${fanFrame + 1}.png`; // Update image source
  }, 100); // Adjust the speed of the spin by changing the interval time (in ms)
}

// Function to start scanning for Bluetooth devices
async function startScan() {
  try {
      // Send a request to the backend to start scanning
      const response = await fetch('http://0.0.0.0:5000/scan');
      if (!response.ok) {
          const errorData = await response.json();
          console.error('Error response from server:', errorData);
          alert(`Error: ${errorData.message}`);
          return;
      }

      // Parse the response data
      const data = await response.json();
      console.log('Scan response data:', data); // Debugging log

      // Check if the data contains the expected keys
      if (typeof data.device_count === 'undefined' || !Array.isArray(data.devices)) {
          console.error('Unexpected data format:', data);
          alert('Error: Received unexpected data from server.');
          return;
      }

      // Update the device count in the UI
      document.getElementById('deviceCount').innerText = data.device_count;

      // Update the device list in the UI
      const deviceList = document.getElementById('deviceList');
      deviceList.innerHTML = ''; // Clear previous device list

      data.devices.forEach((device) => {
          const listItem = document.createElement('li');
          listItem.textContent = `${device.name} (${device.address})`;
          deviceList.appendChild(listItem);
      });
  } catch (error) {
      console.error('Error during scanning:', error);
      alert('Failed to fetch scan data. Please try again.');
  }
}

// Function to update the RSSI threshold
async function updateThreshold() {
  const thresholdInput = document.getElementById('thresholdInput');
  const newThreshold = thresholdInput.value;

  // Validate input
  if (!newThreshold) {
      alert('Please enter a valid RSSI threshold.');
      return;
  }

  try {
      // Send request to backend to update the threshold
      const response = await fetch('http://0.0.0.0:5000/set_threshold', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ threshold: parseInt(newThreshold) })
      });

      const data = await response.json();
      if (response.ok) {
          // Update the UI with the new threshold
          document.getElementById('rssiThreshold').innerText = data.rssi_threshold;
          thresholdInput.value = ''; // Clear input field
          alert('RSSI threshold updated successfully!');
      } else {
          alert(`Error: ${data.message}`);
      }
  } catch (error) {
      console.error('Error during threshold update:', error);
      alert('Failed to update RSSI threshold. Please try again.');
  }
}

// Fetch data every 5 seconds
setInterval(updateDashboard, 5000);

// Call updateDashboard initially
updateDashboard();
