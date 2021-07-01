const fs = require('fs');
const fetch = require('node-fetch');
const AbortController = require('abort-controller');
const { workerData, parentPort } = require('worker_threads') 
const controller = new AbortController();
const timeout = setTimeout(() => {
	controller.abort();
}, 2000);

const url1 = "http://192.168.100.201:8080/cgi-bin/camera_settings.sh?rotate=yes"
const url2 = "http://192.168.100.202:8080/cgi-bin/camera_settings.sh?rotate=yes"
const url3 = "http://192.168.100.203:8080/cgi-bin/camera_settings.sh?rotate=yes"
const url4 = "http://192.168.100.204:8080/cgi-bin/camera_settings.sh?rotate=no"

const url5 = "http://192.168.100.201:8080/cgi-bin/get_configs.sh?conf=system"
const url6 = "http://192.168.100.202:8080/cgi-bin/get_configs.sh?conf=system"

const url7 = "http://192.168.100.201:8080/cgi-bin/service.sh?name=rtsp&action=status&param1=both"
const url8 = "http://192.168.100.202:8080/cgi-bin/service.sh?name=rtsp&action=status&param1=both"

const url9 =  "http://192.168.100.201:8080/cgi-bin/service.sh?name=rtsp&action=start&param1=both"
const url10 = "http://192.168.100.202:8080/cgi-bin/service.sh?name=rtsp&action=start&param1=both"

var url = url5;

//console.log('Read Cam no ' + workerData);

async function sendAPI() 
{

    var buffer = 'Error';
    try {
        const response = await fetch(url5, {signal: controller.signal});
        buffer = await response.json();
        console.log('CAM1');
        console.log(buffer);
        //}
    } catch (error) {

        //if (error instanceof fetch.AbortError) {
            console.log('request was aborted');
        //}
    } finally {
        clearTimeout(timeout);
    }

    var buffer = 'Error';
    try {
        const response = await fetch(url6, {signal: controller.signal});
        buffer = await response.json();
        console.log('CAM2');
        console.log(buffer);
        //}
    } catch (error) {

        //if (error instanceof fetch.AbortError) {
            console.log('request was aborted');
        //}
    } finally {
        clearTimeout(timeout);
    }
}

sendAPI();