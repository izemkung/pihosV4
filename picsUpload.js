const SerialPort = require("serialport");
var sizeof = require('object-sizeof')
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
var IO_CAM1 = new Gpio(8, 'out');
var IO_CAM2 = new Gpio(9, 'out');
var IO_CAM3 = new Gpio(10, 'out');
var IO_CAM4 = new Gpio(11, 'out');
var mongo = require('mongodb');
var mongoClient = require('mongodb').MongoClient;
var urlMongo = "mongodb://127.0.0.1:27017/";//currentPicURL

const { Worker } = require('worker_threads') 

var ping = require('ping');
var hosts = ['192.168.100.201', '192.168.100.202', '192.168.100.203', '192.168.100.204'];
var arrayCamOnline = [];


var countSend = 0;
const timeLoop = 3000;
var arrayCamErrorCount = [0,0,0,0];
var timeStartResetCAM = [0,0,0,0];
var carID = 99;
var server = "";
var apiVersion = "";
var numCamera = "";

IO_CAM1.writeSync(1);
IO_CAM2.writeSync(1);
IO_CAM3.writeSync(1);
IO_CAM4.writeSync(1);

readConfigs();

function readConfigs() {
    mongoClient.connect(urlMongo, function(err, db) {
        if (err) 
        {
            console.log(err);
            throw err;

        }
        var dbo = db.db("pihos");
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
            apiVersion = _res['apiVersion'];

            db.close();
        });
    });
}

//Get pic
function runServiceCamGetPic(workerData) { 
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

Object.size = function(obj) {
    var size = 0,
    key;
    for (key in obj) {
        if (obj.hasOwnProperty(key)) size++;
    }
    return size;
};

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
    for (var iCount =1; iCount < 5 ; iCount++) 
    {
        var msgCam =  'CAM'+ iCount;
        console.log(msgCam);
        if(iCount < numCamera+1)
            arrayCamOnline.push( msgCam);   
        else 
            arrayCamOnline.push("NULL"); 
    }
    
    
    console.log(arrayCamOnline);


    var programEnd = Date.now() + 600000;//600 Sec
    var programStart = Date.now();
    if(arrayCamOnline.length <= 1)
    {
        programEnd = Date.now() + 30000;//30 Sec
    }

    if(arrayCamOnline.length == 0)
    {
        programEnd = Date.now() + 3000;
    }

    for (var iCount =0; iCount < 4 ; iCount++) 
    {
        timeStartResetCAM[iCount] = Date.now(); 
    }
    
    var GetPicError = 0;
    while(Date.now() < programEnd)
    {
        var programLoopTime = Date.now()
        var arrayResult = [];
        var arrayCamPic = [];
        var arrayCamError = [];
        
        
        const [result1, result2 ,result3,result4] = await Promise.all([runServiceCamGetPic(arrayCamOnline[0]), runServiceCamGetPic(arrayCamOnline[1]),runServiceCamGetPic(arrayCamOnline[2]),runServiceCamGetPic(arrayCamOnline[3])]);
        arrayResult.push(result1);
        arrayResult.push(result2);
        arrayResult.push(result3);
        arrayResult.push(result4);

        var countCam = 0;
        var sizeOfPic = 0;
        for (let cam of arrayResult) {
            //const result1 = await runServiceCamGetPic(cam);

            //console.log(result1.Data);
            if(cam.Data == 'Error' || cam.Data == null)
            {
                arrayCamError.push(cam.Name +' '+cam.Data)
                console.log(cam.Name +' '+cam.Data);
                LED.writeSync(1);
                await wasteTime(100);
                LED.writeSync(0);
                await wasteTime(100);
                LED.writeSync(1);
                await wasteTime(100);
                LED.writeSync(0);
                GetPicError += 1;
                arrayCamErrorCount[countCam] += 1;
            }else if(cam.Data == 'NULL')
            {

            }else{
                var size = sizeof(cam);
                //console.log(size);
                if(size > 100000)
                {
                    sizeOfPic += size;
                    arrayCamError.push(cam.Name +' Ok')
                    arrayCamPic.push(cam);
                    arrayCamErrorCount[countCam] = 0;
                }else{
                    //console.log('Size error');
                }
            }
            countCam+=1;
        }

        
        //const result2 = await runServiceCamGetPic('CAM2') 
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
                if (err) {
                    LED.writeSync(0);
                    console.error(err);
                    arrayCamError.push('Send Error')
                    GetPicError += 1;
                }
                console.log('Time:'+((programEnd - Date.now())/1000  )+ ' Count:'+countSend + ' Size: '+ (sizeOfPic/1000) +' kb Code:', httpResponse && httpResponse.statusCode);
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
            arrayCamError.push('Send OK');
            
            await wasteTime(50);
            
            LED.writeSync(0);
        }

        var programLoopTimeDiff = Date.now() - programLoopTime;
        if(programLoopTimeDiff > timeLoop)
        {
            programLoopTimeDiff = timeLoop;
        }
        
        camStatus(arrayCamError);
        await wasteTime(timeLoop -  programLoopTimeDiff);

        //console.log('loop ' + (Date.now() - programLoopTime) +' ms timeDiff ' + programLoopTimeDiff + ' ms.') 

        if(countCam >= numCamera)
        {
            GetPicError = 0;
        }

        if(GetPicError < 40) 
        {
            programEnd = Date.now() + 60000;//60 Sec
        }
        else if(GetPicError > 40) 
        {
            GetPicError = 0;
            programEnd = Date.now() - 100;
        }

        //Reset Cam

        for (var iCount =0; iCount < 4 ; iCount++) 
        {
            if(arrayCamErrorCount[iCount] > 10 )
            {
                arrayCamErrorCount[iCount] = 0;
                console.log('-------------CAM'+ (iCount+1) + ' Error I/O----------------');

                if((Date.now() - timeStartResetCAM[iCount]) > 180000)//4 min
                {
                    timeStartResetCAM[iCount] = Date.now(); 

                    if(iCount == 0)
                    {
                        console.log('-------------CAM'+ (iCount+1) + ' Reset');

                        IO_CAM1.writeSync(0);
                        await wasteTime(2000);
                        IO_CAM1.writeSync(1);           
                    }

                    if(iCount == 1)
                    {
                        console.log('-------------CAM'+ (iCount+1) + ' Reset');

                        IO_CAM2.writeSync(0);
                        await wasteTime(2000);
                        IO_CAM2.writeSync(1);           
                    }

                    if(iCount == 2)
                    {
                        console.log('-------------CAM'+ (iCount+1) + ' Reset');

                        IO_CAM3.writeSync(0);
                        await wasteTime(2000);
                        IO_CAM3.writeSync(1);           
                    }

                    if(iCount == 3)
                    {
                        console.log('-------------CAM'+ (iCount+1) + ' Reset');

                        IO_CAM4.writeSync(0);
                        await wasteTime(2000);
                        IO_CAM4.writeSync(1);           
                    }
                     
                }
                
            }
        }
        
    }
    
   
    process.exit(1);
    
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
            //arrayCamOnline.push("NULL");
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

