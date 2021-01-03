const SerialPort = require("serialport");
const SerialPortParser = require("@serialport/parser-readline");
const GPS = require("gps");
const Axios = require("axios");
const GeoJSON = require("geojson");
const OS = require("os");
const Moment = require("moment");
var net = require('net');
var request = require('request');
const fs = require('fs');


const { Worker } = require('worker_threads') 

var  SERIAL_PORT = "/dev/ttyS0";
var ping = require('ping');
var hosts = ['192.168.100.201', '192.168.100.202', '192.168.100.203', '192.168.100.204'];
var arrayCamOnline = [];

var client;
var isConnect = 0;
var countSend = 0;

//GPS Update


//Get pic
function runServiceCam(workerData) { 
    return new Promise((resolve, reject) => { 
        const worker = new Worker( 
                './readpic.js', { workerData }); 
                worker.on('message', resolve); 
                worker.on('error', reject); 
                worker.on('exit', (code) => { 
            if (code !== 0) 
                reject(new Error( 
`Stopped the Worker Thread with the exit code: ${code}`)); 
        }) 
    }) 
} 
  
async function main() 
{ 
    await getCameraOnline();
    var programEnd = Date.now() + 600000;

    if(arrayCamOnline.length <= 1)
    {
        programEnd = Date.now() + 30000;
    }

    while(Date.now() < programEnd)
    {
        var arrayCamPic = [];
        var GetPicError = 0;
        for (let cam of arrayCamOnline) {
            const result1 = await runServiceCam(cam);

            //console.log(result1.Data);
            if(result1.Data == 'Error')
            {
                console.log(result1.Data);
            }else{
                arrayCamPic.push(result1); 
            }
        }
        //const result2 = await runServiceCam('CAM2') 
        //arrayCamPic.push(result2);
        
        //console.log(result2); 
        
        if(arrayCamPic.length > 0)
        {
            //console.log(arrayCamPic['CAM1'])
            //console.log(arrayCamPic['CAM1'])
            countSend++;
            const r = request.post('http://202.183.192.149:3000/fileupload', function optionalCallback(err, httpResponse, body) {
                //console.log('status', httpResponse && httpResponse.statusCode); 

                console.log('Time:'+(programEnd - Date.now())  + ' Count:'+countSend +' Code:', httpResponse && httpResponse.statusCode);
            })
            const form = r.form();
            form.append('ID', '1');
            form.append('Time', countSend);
            for (let pic of arrayCamPic)
            {
                form.append(pic.Name,  Buffer.from(pic.Data), {
                    filename: 'unicycle.jpg',
                    contentType: 'image/jpeg'
                  });
            }
            
        }
        //gps.update("$GPGGA,224900.000,4832.3762,N,00903.5393,E,1,04,7.8,498.6,M,48.0,M,,0000*5E");

    }
    
   
    process.exit(1);
    //destroy(parser)
    //destroy(gps)
    
} 

async function getCameraOnline() 
{
    var count = 1;
    arrayCamOnline = [];
    for(let host of hosts){
        let isAlive = await ping.promise.probe(host);
        //console.log(isAlive.alive);
        if(isAlive.alive)
        {
            var msg = 'host ' + host + ' CAM'+ count + ' is alive' ;
            console.log(msg);
            var msgCam =  'CAM'+ count;
            arrayCamOnline.push(msgCam);
        }else{
            var msg = 'host ' + host + ' CAM'+ count + ' is death' ;
            console.log(msg);
        } 
        count++;
    }
    console.log(arrayCamOnline); 
}


main().catch(err => console.error(err)) 

/*
require('dns').resolve('www.google.com', function(err) {
  if (err) {
     console.log("No connection");
  } else {
      console.log("Connected internet");

      client = new net.Socket({writeable: true}); //writeable true does not appear to help

      client.on('close', function() {
        console.log('Connection closed');
        isConnect = 0;
      });

      
      client.on('data', function(data) {
        console.log(data);
        
      });

      client.on('error', function(err) {
        console.error('Connection error: ' + err);
        console.error(new Error().stack);
      });

      client.connect(3000, '202.183.192.149',async function() {
        var count = 0;
        console.log('Connected');
        console.log('IP '+ client.remoteAddress +':'+client.remotePort);

          isConnect  = 1;
          //for(var i = 0; i < 100000; i++) {
          //  client.write('' + i + '');
          //  await sleep(10);
          //bufferSize does not seem to be an issue
          //  console.info(count++);
          //}
      });
    

  }
});
*/

function sleep(ms) {
    return new Promise((resolve) => {
      setTimeout(resolve, ms);
    });
  }   


function wasteTime() {
    const end = Date.now() + 3000;
    while (Date.now() < end) { }
}

