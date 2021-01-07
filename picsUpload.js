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
var Gpio = require('onoff').Gpio; //include onoff to interact with the GPIO
var LED = new Gpio(17, 'out'); //use GPIO pin 17 PC, and specify that it is output
var mongo = require('mongodb');
var mongoClient = require('mongodb').MongoClient;
var urlMongo = "mongodb://127.0.0.1:27017/";//currentPicURL

const { Worker } = require('worker_threads') 

var  SERIAL_PORT = "/dev/ttyS0";
var ping = require('ping');
var hosts = ['192.168.100.201', '192.168.100.202', '192.168.100.203', '192.168.100.204'];
var arrayCamOnline = [];

var countSend = 0;
const timeLoop = 2000;

var carID = 99;
var server = "";
var numCamera = "";

mongoClient.connect(urlMongo, function(err, db) {
    if (err) 
    {
        console.log(err);
        throw err;

    }

    var dbo = db.db("pihos");
    var myquery = {};
    //myquery['CarID'] = car_id ;
    dbo.collection("configs").findOne({}, function(err, _res) {
        if (err) 
        {
            console.log(err);
            throw err;

        }
        console.log(_res);
        carID = _res['id'];
        numCamera  = _res['camN'];
        server = _res['server'];


        db.close();
    });
  });

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

function camStatus(msg) { 
    mongoClient.connect(urlMongo, function(err, db) {
        if (err)
            throw err;
        var dbo = db.db("pihos");
        var myquery = {$set: {'statusPIC': msg}};
        //myquery['CarID'] = car_id ;
        dbo.collection("status").updateOne({},myquery, function(err, _res) {
            if (err)
                throw err;
            db.close();
        });
      });
} 
  
async function main() 
{ 
    await getCameraOnline();
    var programEnd = Date.now() + 600000;
    
    console.log(carID);
    console.log(server);
    console.log(numCamera);
    
    var numCam = arrayCamOnline.length;
    console.log(arrayCamOnline);
    console.log(numCam);
    mongoClient.connect(urlMongo, function(err, db) {
        if (err)
            throw err;
        var dbo = db.db("pihos");
        var myquery = {$set: {'numCam': numCam}};
        //myquery['CarID'] = car_id ;
        dbo.collection("status").updateOne({},myquery, function(err, _res) {
            if (err)
                throw err;
            db.close();
        });
      });

    
    arrayCamOnline = [];
    console.log("Loop");
    for (var iCount =1; iCount < (numCamera+1) ; iCount++) 
    {
        var msgCam =  'CAM'+ iCount;
        console.log(msgCam);
        arrayCamOnline.push( msgCam);    
    }
    
    
    console.log(arrayCamOnline);

    if(arrayCamOnline.length <= 1)
    {
        programEnd = Date.now() + 30000;
    }

    if(arrayCamOnline.length == 0)
    {
        programEnd = Date.now() + 3000;
    }

    
    while(Date.now() < programEnd)
    {
        var programLoopTime = Date.now()
        var arrayCamPic = [];
        var arrayCamError = [];
        var GetPicError = 0;
        
        for (let cam of arrayCamOnline) {
            const result1 = await runServiceCam(cam);

            //console.log(result1.Data);
            if(result1.Data == 'Error')
            {
                arrayCamError.push(cam +' '+result1.Data)
                console.log(cam +' '+result1.Data);
                LED.writeSync(1);
                await wasteTime(100);
                LED.writeSync(0);
                await wasteTime(100);
                LED.writeSync(1);
                await wasteTime(100);
                LED.writeSync(0);
            }else{
                arrayCamError.push(cam +' Ok')
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
            LED.writeSync(1);
            var url = server + ':3000/fileupload'
            const r = request.post(url, function optionalCallback(err, httpResponse, body) {
                //console.log('status', httpResponse && httpResponse.statusCode); 
                if (err) {
                    LED.writeSync(0);
                    console.error(err)
                    arrayCamError.push('Send Error')
                }
                console.log('Time:'+((programEnd - Date.now())/1000  )+ ' Count:'+countSend +' Code:', httpResponse && httpResponse.statusCode);
            })
            const form = r.form();
            form.append('ID', carID);
            form.append('Time', countSend);
            for (let pic of arrayCamPic)
            {
                form.append(pic.Name,  Buffer.from(pic.Data), {
                    filename: 'unicycle.jpg',
                    contentType: 'image/jpeg'
                  });
            }
            arrayCamError.push('Send OK')
            LED.writeSync(0);
        }
        //gps.update("$GPGGA,224900.000,4832.3762,N,00903.5393,E,1,04,7.8,498.6,M,48.0,M,,0000*5E");
        var programLoopTimeDiff = Date.now() - programLoopTime;
        if(programLoopTimeDiff > timeLoop)
        {
            programLoopTimeDiff = timeLoop;
        }
        //console.log('sleep ' + programLoopTimeDiff)
        camStatus(arrayCamError);
        await sleep(timeLoop -  programLoopTimeDiff);

        console.log('loop ' + (Date.now() - programLoopTime) +' ms timeDiff ' + programLoopTimeDiff + ' ms.') 
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


function wasteTime(ms) {
    const end = Date.now() + ms;
    while (Date.now() < end) { }
}

