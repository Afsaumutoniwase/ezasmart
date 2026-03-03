// Dashboard JavaScript

// Add subtle animation on page load
window.addEventListener('load', function() {
    const cards = document.querySelectorAll('.shadow-lg');
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'all 0.5s ease';
            
            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 50);
        }, index * 100);
    });
});

// ===== SENSOR MONITORING FUNCTIONALITY =====

// Handle sensor form submission
document.addEventListener('DOMContentLoaded', function() {
    const sensorForm = document.getElementById('sensor-form');
    
    if (sensorForm) {
        sensorForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Get form values
            const cropId = document.getElementById('crop-id').value;
            const phLevel = document.getElementById('ph-level').value;
            const ecValue = document.getElementById('ec-value').value;
            const temp = document.getElementById('temp').value;
            
            // Validate inputs
            if (!cropId || !phLevel || !ecValue || !temp) {
                showSensorError('Please fill in all required fields.');
                return;
            }
            
            // Show loading, hide previous results
            showSensorLoading();
            hideSensorPrediction();
            hideSensorError();
            
            try {
                // Send request to backend
                const response = await fetch('/api/predict-sensor', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        crop_id: cropId,
                        ph_level: parseFloat(phLevel),
                        ec_value: parseFloat(ecValue),
                        ambient_temp: parseFloat(temp)
                    })
                });
                
                const data = await response.json();
                
                if (response.ok && data.success) {
                    // Show prediction
                    showSensorPrediction(data);
                } else {
                    // Show error
                    showSensorError(data.error || 'Failed to analyze sensor data. Please try again.');
                }
            } catch (error) {
                console.error('Error:', error);
                showSensorError('An error occurred while connecting to the server. Please check your connection and try again.');
            } finally {
                hideSensorLoading();
            }
        });
    }
});

// Show sensor loading indicator
function showSensorLoading() {
    const loading = document.getElementById('sensor-loading');
    const submitBtn = document.getElementById('sensor-submit-btn');
    
    loading.classList.remove('hidden');
    submitBtn.disabled = true;
    submitBtn.classList.add('opacity-50', 'cursor-not-allowed');
}

// Hide sensor loading indicator
function hideSensorLoading() {
    const loading = document.getElementById('sensor-loading');
    const submitBtn = document.getElementById('sensor-submit-btn');
    
    loading.classList.add('hidden');
    submitBtn.disabled = false;
    submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
}

// Show sensor prediction
function showSensorPrediction(data) {
    const predictionDiv = document.getElementById('sensor-prediction');
    const contentDiv = document.getElementById('sensor-prediction-content');
    
    // Format action with appropriate icon
    let actionIcon = '✓';
    if (data.action === 'Add_pH_Up') actionIcon = '⬆️';
    else if (data.action === 'Add_pH_Down') actionIcon = '⬇️';
    else if (data.action === 'Add_Nutrients') actionIcon = '🌱';
    else if (data.action === 'Dilute') actionIcon = '💧';
    else if (data.action === 'Maintain') actionIcon = '✅';
    
    // Build HTML content
    const html = `
        <div class="space-y-4">
            <div class="flex items-center space-x-3">
                <span class="text-3xl">${actionIcon}</span>
                <div>
                    <h4 class="text-xl font-bold text-[#28844b]">${data.action.replace(/_/g, ' ')}</h4>
                    <p class="text-sm text-gray-500">Confidence: ${data.confidence}%</p>
                </div>
            </div>
            
            <div class="border-t border-gray-200 pt-4">
                <p class="text-gray-700 leading-relaxed mb-4">${data.description}</p>
                
                <div class="bg-white border border-gray-200 rounded-md p-4">
                    <h5 class="font-semibold text-gray-800 mb-2">Your Sensor Readings:</h5>
                    <div class="grid grid-cols-2 gap-2 text-sm">
                        <div class="text-gray-600">Crop:</div>
                        <div class="font-semibold">${data.inputs.crop}</div>
                        
                        <div class="text-gray-600">pH Level:</div>
                        <div class="font-semibold">${data.inputs.pH}</div>
                        
                        <div class="text-gray-600">EC Value:</div>
                        <div class="font-semibold">${data.inputs.EC} mS/cm</div>
                        
                        <div class="text-gray-600">Temperature:</div>
                        <div class="font-semibold">${data.inputs.Temperature}°C</div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    contentDiv.innerHTML = html;
    predictionDiv.classList.remove('hidden');
    
    // Scroll to prediction
    setTimeout(() => {
        predictionDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 100);
}

// Hide sensor prediction
function hideSensorPrediction() {
    const predictionDiv = document.getElementById('sensor-prediction');
    predictionDiv.classList.add('hidden');
}

// Show sensor error
function showSensorError(message) {
    const errorDiv = document.getElementById('sensor-error');
    const errorContent = document.getElementById('sensor-error-content');
    
    errorContent.textContent = message;
    errorDiv.classList.remove('hidden');
    
    // Scroll to error
    setTimeout(() => {
        errorDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 100);
}

// Hide sensor error
function hideSensorError() {
    const errorDiv = document.getElementById('sensor-error');
    errorDiv.classList.add('hidden');
}

// Reset sensor form
function resetSensorForm() {
    const form = document.getElementById('sensor-form');
    form.reset();
    hideSensorPrediction();
    hideSensorError();
    
    // Focus on the crop selector
    setTimeout(() => {
        document.getElementById('crop-id').focus();
    }, 500);
}
