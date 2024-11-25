// Track fan status received from server
let fanStatus = false;
let fanFrame = 0; // To track the current frame of the fan animation
const totalFrames = 7; // Total number of fan images
let spinInterval;
const gaugeElementTemp = document.getElementById("temp");
const gaugeElementHum = document.getElementById("hum");

function setGaugeValueTemp(gauge, value) {
  if (value < 0 || value > 1) {
    return;
  }

  gauge.querySelector(".gauge__fill").style.transform = `rotate(${
    value / 2
  }turn)`;
  gauge.querySelector(".gauge__cover").textContent = `${value * 100}°C`;
}

function setGaugeValueHum(gauge, value) {
  if (value < 0 || value > 1) {
    return;
  }

  gauge.querySelector(".gauge__fill").style.transform = `rotate(${
    value / 2
  }turn)`;
  gauge.querySelector(".gauge__cover").textContent = `${value * 100}%`;
}

function updateDashboard() {
  fetch("/sensor_data")
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

// Fetch data every 5 seconds
setInterval(updateDashboard, 5000);

// Call updateDashboard initially
updateDashboard();
