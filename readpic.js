const fs = require('fs');
const fetch = require('node-fetch');
const AbortController = require('abort-controller');
const { workerData, parentPort } = require('worker_threads') 
const controller = new AbortController();
const timeout = setTimeout(() => {
	controller.abort();
}, 2000);

const url1 = "http://192.168.100.201:8080/cgi-bin/snapshot.sh?res=low&watermark=no"
const url2 = "http://192.168.100.202:8080/cgi-bin/snapshot.sh?res=low&watermark=no"
const url3 = "http://192.168.100.203:8080/cgi-bin/snapshot.sh?res=low&watermark=no"
const url4 = "http://192.168.100.204:8080/cgi-bin/snapshot.sh?res=low&watermark=no"

var url = url1;
if(workerData == 'CAM2')
{
    url = url2;
}else if(workerData == 'CAM3')
{
    url = url3;
}else if(workerData == 'CAM4')
{
    url = url4;
}

//console.log('Read Cam no ' + workerData);

async function download() 
{
    var buffer = 'Error';
    try {
        const response = await fetch(url, {signal: controller.signal});
        buffer = await response.buffer();
    } catch (error) {

        //if (error instanceof fetch.AbortError) {
        //    console.log('request was aborted');
        //}
    } finally {
        clearTimeout(timeout);
    }
  //const base64Image1 = await buffer.toString('base64');
   parentPort.postMessage( { Name: workerData, Data: buffer }) ;
}
download();

//parentPort.postMessage( 
//    { fileName: workerData, status: base64Image1 }) 