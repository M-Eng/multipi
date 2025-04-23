document.addEventListener('DOMContentLoaded', function () {
    var autoRefreshCheckbox = document.getElementById('autoRefreshCheckbox');
    var refreshIntervalInput = document.getElementById('refreshInterval');
    var intervalId;

    function startAutoRefresh() {
        if (intervalId) {
            clearInterval(intervalId);
        }

        if (!refreshIntervalInput.value) {
            refreshIntervalInput.value = "30";
        }

        var interval = parseInt(refreshIntervalInput.value, 10) * 1000;
        if (!isNaN(interval) && interval > 0) {
            intervalId = setInterval(pingAllDevices, interval);
        }
    }

    autoRefreshCheckbox.addEventListener('change', function () {
        if (autoRefreshCheckbox.checked) {
            startAutoRefresh();
        } else {
            clearInterval(intervalId);
        }
    });

    refreshIntervalInput.addEventListener('input', function () {
        if (autoRefreshCheckbox.checked) {
            startAutoRefresh();
        }
    });

});

document.addEventListener('DOMContentLoaded', function () {
    var autoRefreshCheckbox = document.getElementById('autoRefreshPicturesCheckbox');
    var refreshIntervalInput = document.getElementById('refreshPicturesInterval');
    var intervalId;

    function startAutoRefresh() {
        if (intervalId) {
            clearInterval(intervalId);
        }

        if (!refreshIntervalInput.value) {
            refreshIntervalInput.value = "60";
          }

        var interval = parseInt(refreshIntervalInput.value, 10) * 1000;
        if (!isNaN(interval) && interval > 0) {
            intervalId = setInterval(showAllPictures, interval);
        }
    }

    autoRefreshCheckbox.addEventListener('change', function () {
        if (autoRefreshCheckbox.checked) {
            startAutoRefresh();
        } else {
            clearInterval(intervalId);
        }
    });

    refreshIntervalInput.addEventListener('input', function () {
        if (autoRefreshCheckbox.checked) {
            startAutoRefresh();
        }
    });

});

document.addEventListener('DOMContentLoaded', function () {
    var showStreamCheckBox = document.getElementById('showStreamCheckBox');

    showStreamCheckBox.addEventListener('change', function () {
        document.querySelectorAll('.raspberry-container').forEach(function(piContainer) {
            const piId = piContainer.querySelector('h2').textContent; // Assuming the pi id is the text content of the h2 tag
            update_device_status(piId)
        });
    });
});

