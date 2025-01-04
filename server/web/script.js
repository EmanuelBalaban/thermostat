const progress = document.querySelector('.slider-progress');
const handle = document.querySelector('.slider-handle');
const desiredTemperatureValue = document.querySelector('.desired-temperature');
const temperatureValue = document.querySelector('.temperature-value');
const fireIcon = document.querySelector('.fire-icon');
const warningIcon = document.querySelector('.warning-icon');
const heatingButton = document.getElementById('heating-button');
const radius = 90;
const circumference = 2 * Math.PI * radius;

let angle = 0;
let isDragging = false;
let startAngle = 0;

progress.style.strokeDasharray = circumference;
progress.style.strokeDashoffset = circumference;

function updateSlider(newAngle) {
    angle = newAngle;
    const offset = (360 - angle) / 360 * circumference;
    progress.style.strokeDashoffset = offset;

    const radians = (angle * Math.PI) / 180;
    const cx = 100 + radius * Math.cos(radians);
    const cy = 100 + radius * Math.sin(radians);

    handle.setAttribute('cx', cx);
    handle.setAttribute('cy', cy);

    const temp = Math.round((16 + (angle / 360) * 14) * 10) / 10;
    desiredTemperatureValue.textContent = `${temp}°C`;
}

function getClientCoordinates(e) {
    if (e.touches && e.touches[0]) {
        return {x: e.touches[0].clientX, y: e.touches[0].clientY};
    }
    return {x: e.clientX, y: e.clientY};
}

function angleFromEvent(e) {
    const {x: clientX, y: clientY} = getClientCoordinates(e);
    const rect = handle.parentNode.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    const x = clientX - centerX;
    const y = clientY - centerY;

    const atan = Math.atan2(y, x);
    return ((atan * 180) / Math.PI + 360) % 360;
}


heatingButton.addEventListener('click', () => {
    const isEnabled = !heatingButton.classList.contains('off');
    sendPatch({heating_enabled: !isEnabled});
});

function startDrag(e) {
    if (e.target !== handle) return;
    e.preventDefault();
    isDragging = true;
    const touchAngle = angleFromEvent(e);
    startAngle = touchAngle - angle;
}

function dragMove(e) {
    if (isDragging) {
        const touchAngle = angleFromEvent(e);
        const newAngle = touchAngle - startAngle;
        updateSlider((newAngle + 360) % 360); // Keep the angle within 0-360
    }
}

function endDrag() {
    if (isDragging) {
        isDragging = false;
        sendPatch({desired_temperature: Math.round((16 + (angle / 360) * 14) * 10) / 10});
    }
}

// Mouse events
handle.addEventListener('mousedown', startDrag);
window.addEventListener('mousemove', dragMove);
window.addEventListener('mouseup', endDrag);

// Touch events (for mobile compatibility)
handle.addEventListener('touchstart', startDrag);
window.addEventListener('touchmove', dragMove);
window.addEventListener('touchend', endDrag);

function fetchState() {
    fetch('/state')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(state => {
            updateState(state); // Update the UI or application state with the response
        })
        .catch(error => {
            console.error('Error fetching state:', error);
        });
}

function updateState(state) {
    if (state.temperature !== undefined) {
        temperatureValue.textContent = `${state.temperature}°C`;
    }
    if (state.desired_temperature !== undefined && !isDragging) {
        const newAngle = ((state.desired_temperature - 16) / 14) * 360;
        updateSlider(newAngle);
    }
    if (state.relay_state !== undefined) {
        fireIcon.style.display = state.relay_state ? 'inline' : 'none';
    }
    if (state.gas_detected !== undefined) {
        warningIcon.style.display = state.gas_detected ? 'inline' : 'none';
    }
    if (state.heating_enabled !== undefined) {
        heatingButton.textContent = state.heating_enabled ? 'Heating On' : 'Heating Off';
        heatingButton.classList.toggle('off', !state.heating_enabled);
    }
}

function sendPatch(data) {
    fetch('/state', {
        method: 'PATCH', headers: {
            'Content-Type': 'application/json',
        }, body: JSON.stringify(data),
    }).then(_ => fetchState());
}

setInterval(fetchState, 5000);
fetchState();