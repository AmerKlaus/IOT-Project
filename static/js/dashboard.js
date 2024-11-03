// Track fan status received from server
let fanStatus = false;
let fanFrame = 0; // To track the current frame of the fan animation
const totalFrames = 7; // Total number of fan images
let spinInterval;

function updateDashboard() {
  // Fetching data from IoT server (use actual endpoints)
  fetch('/sensor_data')
    .then(response => response.json())
    .then(data => {
      const { temperature, humidity, fanOn } = data;

      // Update gauges
      updateGauge('temperatureGauge', temperature, '°C');
      updateGauge('humidityGauge', humidity, '%');

      // Update fan status
      fanStatus = fanOn;
      updateFanIcon();
    })
    .catch(error => console.error('Error fetching data:', error));
}

// Update the gauge display for temperature and humidity
function updateGauge(id, value, unit) {
  document.getElementById(id).textContent = ` ${value}${unit}`;
}

// Update the fan icon display based on fanStatus
function updateFanIcon() {
  const fanIcon = document.getElementById('fanIcon');
  const fanStatusText = document.getElementById('fanStatus');

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
  const fanIcon = document.getElementById('fanIcon');
  clearInterval(spinInterval); // Clear any existing intervals

  spinInterval = setInterval(() => {
    fanFrame = (fanFrame + 1) % totalFrames; // Cycle through frames
    fanIcon.src = `/static/images/fan${fanFrame + 1}.png`; // Update image source
  }, 100); // Adjust the speed of the spin by changing the interval time (in ms)
}

// Fetch data every 5 seconds
setInterval(updateDashboard, 5000);

// Call updateDashboard initially
updateDashboard();