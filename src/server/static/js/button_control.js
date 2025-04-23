function startStream(deviceId) {
    fetch(`/start_stream/${deviceId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
           
        } else {
            alert(`Failed to start stream for device ${deviceId}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function stopStream(deviceId) {
    fetch(`/stop_stream/${deviceId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            
        } else {
            console.error("Couldn't stop the stream:", data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function shutdownDevice(deviceId) {
    var confirmed = confirm("Are you sure you want to stop " + deviceId);
    if (confirmed) {
        fetch(`/shutdown/${deviceId}`);
    }
}

// function displayPicture(deviceId) {
//     fetch(`/get_picture/${deviceId}`)
//     .then(response => response.blob())
//     .then(blob => {
//         let imageUrl = URL.createObjectURL(blob);
//         let imageElement = document.getElementById(deviceId + "_image");
//         imageElement.src = imageUrl;
//         imageElement.style.display = "block";
//     });
// }
function displayPicture(deviceId) {
        fetch(`/get_picture/${deviceId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
            
            } else {
                console.error(`Failed to display camera last frame for device ${deviceId}`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }

function pingDevice(deviceId) {
    fetch(`/ping/${deviceId}`);
}

// Delay function using a Promise
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// async function startAllStreams() {
//     // Iterate over all Raspberry Pis and start their stream
//     document.querySelectorAll('.raspberry-container').forEach(function(piContainer) {
//         const piId = piContainer.querySelector('h2').textContent; // Assuming the pi id is the text content of the h2 tag
//         startStream(piId); // Assuming startStream function exists and starts the stream for a given pi
//         // wait 1 second before starting the next stream
//         await delay(1000);
//     });
// }

async function startAllStreams() {
    // Convert NodeList to an array to use for...of loop
    const piContainers = Array.from(document.querySelectorAll('.raspberry-container'));

    for (const piContainer of piContainers) {
        const piId = piContainer.querySelector('h2').textContent; // Assuming the pi id is the text content of the h2 tag
        startStream(piId); // Assuming startStream function exists and starts the stream for a given pi
        // Wait 1 second before starting the next stream
        await delay(500); // Make sure delay is defined or use a similar function
    }
}

function stopAllStreams() {
    // Iterate over all Raspberry Pis and stop their stream
    document.querySelectorAll('.raspberry-container').forEach(function(piContainer) {
        const piId = piContainer.querySelector('h2').textContent; // Assuming the pi id is the text content of the h2 tag
        stopStream(piId); // Assuming stopStream function exists and stops the stream for a given pi
    });
}

function showAllPictures() {
    // Iterate over all Raspberry Pis and request their latest picture
    document.querySelectorAll('.raspberry-container').forEach(function(piContainer) {
        const piId = piContainer.querySelector('h2').textContent; // Assuming the pi id is the text content of the h2 tag
        displayPicture(piId); // Assuming getPicture function exists and fetches the latest picture for a given pi
    });
}

function pingAllDevices() {
    // Iterate over all Raspberry Pis and ping them
    document.querySelectorAll('.raspberry-container').forEach(function(piContainer) {
        const piId = piContainer.querySelector('h2').textContent; // Assuming the pi id is the text content of the h2 tag
        pingDevice(piId); // Assuming pingDevice function exists and pings the device
    });
}

function shutdownAllDevices() {
    var confirmed = confirm("Are you sure you want to stop every devices?");
    if (confirmed) {
        document.querySelectorAll('.raspberry-container').forEach(function(piContainer) {
            const piId = piContainer.querySelector('h2').textContent; // Assuming the pi id is the text content of the h2 tag
            fetch(`/shutdown/${piId}`);
        });
    }
}

// setInterval(pingAllDevices, 5000);