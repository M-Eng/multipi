 // var socket = io.connect('http://localhost:5000');
 var socket = io();
        
 socket.on('connect', function() {
     console.log("Connected to server!");
 });

 socket.on('new_device', function(device) {
    console.log('new_device');
    console.log(device);
    // Create a new div for the device
    let deviceDiv = document.createElement('div');
    deviceDiv.classList.add('raspberry-container');
    deviceDiv.setAttribute('data-device-id', device.id);

    // Add device details
    deviceDiv.innerHTML = `
        <div class="pi-info">
            <h2>${device.id}</h2>
            <span class="status-line"> <span> Status: <div class="status-box ${device.status}">${device.status}</div> </span> <div class="ip_address">IP Address: ${device.ip_address}</div> </span>

        <div class="streaming-status">
            <h3>Streaming Status</h3>
            <table>
                <thead>
                    <tr>
                        <th>Start</th>
                        <th>Duration</th>
                        <th>File Size</th>
                        <th>End</th>
                    </tr>   
                </thead>
                <tbody>
                    <tr>
                        <td class="stream_start_time">${device.stream_start_time == undefined ? "-" : device.stream_start_time}</td>
                        <td class="stream_duration">${device.stream_duration == undefined ? "-" : device.stream_duration}</td>
                        <td class="stream_file_size">${device.stream_file_size == undefined ? "-" : device.stream_file_size}</td>
                        <td class="stream_end_time">${device.stream_end_time == undefined ? "-" : device.stream_end_time}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    
            <button class="button buttonCont start-stream-btn" onclick="startStream('${device.id}')">Start Stream</button>
            <button class="button buttonCont stop-stream-btn" disabled onclick="stopStream('${device.id}')">Stop Stream</button>
            <button class="button buttonCont" onclick="displayPicture('${device.id}')">Show Picture</button>
            <button class="button buttonCont" onclick="pingDevice('${device.id}')">Ping</button>
            <button class="button buttonCont stop-stream-btn" onclick="shutdownDevice('${device.id}')">Shutdown</button>
        </div>
    
        <div class="pi-image">
            <div id="${device.id}_image_container">
                <!-- This is where the image will be displayed -->
                <img id="${device.id}_image" src="" alt="Camera Image" style="display: none;">
            </div>
        </div>
    `;
    //  <p>Status: ${device.status}</p>

    deviceDiv.querySelector('.pi-image img').addEventListener('click', enlargeImage);

    if (device.last_frame_path != undefined) {
        deviceDiv.querySelector('.pi-image img').src = device.last_frame_path;
        deviceDiv.querySelector('.pi-image img').style.display = "block";
    }

    // Append the new device div to the body or a specific container
    const container = document.getElementById('raspberrylist');

    // if container contains "No Raspberry Pi's found" remove it
    if (container.querySelector('p') != null && container.querySelector('p').textContent == "No Raspberry Pis are currently registered.") {
        container.querySelector('p').remove();
    }

    container.appendChild(deviceDiv);

    update_summary();
 });

 socket.on('pi_status_update', function(data) {
    // console.log('Pi status update');
    // console.log(data);

    window[data.id] = data

    update_device_status(data.id)
 });

 function update_device_status(deviceId) {

    data = window[deviceId]

    let deviceDiv = $(`.raspberry-container[data-device-id="${deviceId}"]`);
    if (data.streaming) {
        deviceDiv.find("button[onclick^='startStream']").prop("disabled", true);
        deviceDiv.find("button[onclick^='stopStream']").prop("disabled", false);
    //  deviceDiv.find("p:contains('Stream started at')").text(`Stream started at: ${data.stream_start_time}`);
    } else {
        deviceDiv.find("button[onclick^='startStream']").prop("disabled", false);
        deviceDiv.find("button[onclick^='stopStream']").prop("disabled", true);
    //  deviceDiv.find("p:contains('Stream started at')").text(`Stream started at: ${data.stream_start_time} ended at ${data.stream_end_time} running for ${data.stream_duration} seconds`);
    }

     update_stream_info(deviceDiv, data)
    // deviceDiv.find("p:contains('Status')").text(`Status: ${data.status}`);
    // update ip address
     deviceDiv.find(".ip_address").text(`IP Address: ${data.ip_address}`);
    
    var showStreamCheckBox = document.getElementById('showStreamCheckBox');

    if (showStreamCheckBox.checked & data.streaming & data.hls_stream_path != undefined) {
        deviceDiv.find("img").first().attr("style", "display: none;");
        if (deviceDiv.find('video').length == 0) {
            update_video_stream_info(data, deviceDiv);
        }
    }
    else if (data.last_frame_path != undefined) {
        remove_video_stream(deviceDiv, deviceId)
        deviceDiv.find("img").first().attr("src", data.last_frame_path);
        deviceDiv.find("img").first().attr("style", "display: block;");
    }else{
        remove_video_stream(deviceDiv, deviceId)
        deviceDiv.find("img").first().attr("style", "display: none;");
    }

    if (data.status != deviceDiv.find(".status-box").text()) {
        deviceDiv.find(".status-box").removeClass(deviceDiv.find(".status-box").text());
        deviceDiv.find(".status-box").addClass(data.status);
        deviceDiv.find(".status-box").text(data.status);
    }
    
    update_summary();
    // deviceDiv.find("pi-image img").attr("src", data.last_frame_path);
 }

 function delay(milliseconds){
    return new Promise(resolve => {
        setTimeout(resolve, milliseconds);
    });
}

 function remove_video_stream(deviceDiv, device_id){
    let video = deviceDiv.find('video');

    if(video.length) {
        window['player_' + device_id].dispose();
        video.remove();
    }
 }
 function update_video_stream_info(data, deviceDiv) {

        let video = document.createElement('video');
        video.muted = true;
        video.autoplay = true;
        video.id = data.id + '_stream_video';
        video.width = 350;
        video.classList.add('video-js');
        video.classList.add('vjs-default-skin');
        video.controls = true;
        let source = document.createElement('source');
        source.src = `${data.hls_stream_path}`;
        source.type = "application/x-mpegURL";
        video.appendChild(source);
        
        // find data.deviceId_image_container and append video
        img_container = deviceDiv.find(`#${data.id}_image_container`);
        img_container.append(video);

        window['player_' + data.id] = videojs(data.id + '_stream_video', {autoplay: false});
        window['player_' + data.id].reloadSourceOnError({

            // getSource allows you to override the source object used when an error occurs
            getSource: function(reload) {
              console.log('Reloading because of an error');
              delay(10000);
              // call reload() with a fresh source object
              // you can do this step asynchronously if you want (but the error dialog will
              // show up while you're waiting)
              reload({
                src: data.hls_stream_path,
                type: 'application/x-mpegURL'
              });
              // sleep for 5 seconds
              
             
            },
          
            // errorInterval specifies the minimum amount of seconds that must pass before
            // another reload will be attempted
            errorInterval: 0
          });
        // setTimeout(function() {
        //     player.play();
        //   }, 5000);
        
        // img_container.append(player);
 }  


 function update_summary() {
        // update global summary
    // count number of devices
    let numDevices = document.querySelectorAll('.raspberry-container').length;

    // count number of devices online
    let numDevicesOnline = document.querySelectorAll('.online').length;

    // count number of devices streaming device is streaming if startStream button is disabled
    let numDevicesStreaming = document.querySelectorAll('.start-stream-btn:disabled').length;

    let totalFileSize = 0;
    document.querySelectorAll('.stream_file_size').forEach(function(fileSize) {
        totalFileSize += convert_string_to_byte(fileSize.textContent);
    });
    
    // update summary table
    let summaryTable = document.querySelector('.summary table');
    summaryTable.querySelector('tr:nth-child(1) td:nth-child(1)').textContent = numDevices;
    summaryTable.querySelector('tr:nth-child(1) td:nth-child(2)').textContent = numDevicesOnline;
    summaryTable.querySelector('tr:nth-child(1) td:nth-child(3)').textContent = numDevices - numDevicesOnline;
    summaryTable.querySelector('tr:nth-child(1) td:nth-child(4)').textContent = numDevicesStreaming;
    summaryTable.querySelector('tr:nth-child(1) td:nth-child(5)').textContent = convert_byte_to_string(totalFileSize);    

 }

 function convert_byte_to_string(byte) {
    if (byte < 1024) {
        return byte + " B";
    } else if (byte < 1000000) {
        return (byte / 1000).toFixed(2) + " KB";
    } else if (byte < 1000 * 1000 * 1000) {
        return (byte / 1000 / 1000).toFixed(2) + " MB";
    } else {
        return (byte / 1000 / 1000 / 1000).toFixed(2) + " GB";
    }
 }

 function convert_string_to_byte(string) {
    let unit = string.slice(-2);
    let value = parseFloat(string.slice(0, -2));
    if (unit == " B") {
        return value;
    } else if (unit == "KB") {
        return value * 1000;
    } else if (unit == "MB") {
        return value * 1000 * 1000;
    } else if (unit == "GB") {
        return value * 1000 * 1000 * 1000;
    } else {
        return NaN;
    }
 }

 function update_stream_info(deviceDiv, data) {
    deviceDiv.find(".stream_start_time").text(data.stream_start_time == undefined ? "-" : data.stream_start_time);
    deviceDiv.find(".stream_duration").text(data.stream_duration == undefined ? "-" : data.stream_duration);
    deviceDiv.find(".stream_file_size").text(data.stream_file_size == undefined ? "-" : data.stream_file_size);
    deviceDiv.find(".stream_end_time").text(data.stream_end_time == undefined ? "-" : data.stream_end_time);
}