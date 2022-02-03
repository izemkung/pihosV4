const SerialPort = require("serialport");
var sizeof = require('object-sizeof')
const SerialPortParser = require("@serialport/parser-readline");
const GPS = require("gps");
const Axios = require("axios");
const GeoJSON = require("geojson");
const OS = require("os");
const Moment = require("moment");
var cv2 = "";
const child_process = require('child_process'); 
var net = require('net');
var request = require('request');
const fs = require('fs');
const fetch = require('node-fetch');
var Gpio = require('onoff').Gpio; //include onoff to interact with the GPIO
var LED = new Gpio(17, 'out'); //use GPIO pin 17 PC, and specify that it is output
//var IO_CAM1 = new Gpio(8, 'out');
//var IO_CAM2 = new Gpio(9, 'out');
//var IO_CAM3 = new Gpio(10, 'out');
//var IO_CAM4 = new Gpio(11, 'out');
var mongo = require('mongodb');
var mongoClient = require('mongodb').MongoClient;
var urlMongo = "mongodb://127.0.0.1:27017/";//currentPicURL


const { Worker } = require('worker_threads') 

var ping = require('ping');
var hosts = ['192.168.100.201', '192.168.100.202', '192.168.100.203', '192.168.100.204'];
var arrayCamOnline = [];

var cameras = [
    {name: "CAM1",data:"",dataUpdate:false , rtsp: "rtsp://192.168.100.201/ch0_1.h264" , rtspHD: "rtsp://192.168.100.201/ch0_0.h264" ,liveStarted:false ,updateTime:"0"},
    {name: "CAM2",data:"",dataUpdate:false , rtsp: "rtsp://192.168.100.202/ch0_1.h264" , rtspHD: "rtsp://192.168.100.202/ch0_0.h264" ,liveStarted:false ,updateTime:"0"}
];

var countSend = 0;
const timeLoop = 3500;
var arrayCamErrorCount = [0,0,0,0];
var timeStartResetCAM = [0,0,0,0];
var sendRotagetionPic = [0,0,0,0];
var carID = 99;
var server = "";
var apiVersion = "";
var numCamera = "";
var GetPicError = 0;
var timeRestart = 0;
var countWaitTwoPic = 0;


var optionsToNewServer = {
    'method': 'POST',
    'url': 'http://27.254.149.188/api/snapshot/postAmbulanceImageUpload',
    'headers': {
    },
    formData: {
      'ambulance_id': '60587c82163f1cbdfe6f91b8',
      'ambulance_box_code': '99',
      'images_count': '2',
      'images_name_1': {
        'value': '',
        'options': {
          'filename': 'images_name_1.png',
          'contentType': null
        }
      },
      'images_name_2': {
        'value': '',
        'options': {
          'filename': 'images_name_2.png',
          'contentType': null
        }
      },
      'images_name_3': {
        'value': '',
        'options': {
          'filename': 'images_name_3.png',
          'contentType': null
        }
      },
      'images_name_4': {
        'value': '',
        'options': {
          'filename': 'images_name_4.png',
          'contentType': null
        }
      }
    }
  };


async function setup()
{
    await readConfigs();
    await getCameraOnline();
    
    if(apiVersion == 4)//stream to up pic
    {
        //console.log("Define CV2");
        //cv2 = require('opencv4nodejs');
        
    }
    
    if(apiVersion == 1 || apiVersion == 2 || apiVersion == 3)
    {
        mainV3().catch(err => console.error(err)); 
    }
        
    if(apiVersion == 4 || apiVersion == 5)
    {
        mainV4().catch(err => console.error(err)); 
    }

    console.log('API Version  : ' + apiVersion);
    printAPI_DIS();
    console.log("Setup End");

}

function printAPI_DIS()
{
    if(apiVersion == 2)
    {
        console.log("Get pic by get url and ticker Streming");
    }
    if(apiVersion == 3)
    {
        console.log("Get pic by get url and Auto upload Streming");
    }
    if(apiVersion == 4)
    {
        console.log("Get pic from Streming");
    }
    if(apiVersion == 5)
    {
        console.log("New Server Get pic from Streming");
    }
}


function readConfigs() {
    mongoClient.connect(urlMongo, function(err, db) {
        if (err) 
        {
            console.log(err);
            throw err;
            return false;
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
            return true;
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
`Stopped runServiceCamGetPic the Worker Thread with the exit code: ${code}`)); 
        }) 
    }) 
} 

//Rotage pic
function runServiceCamRotage(workerData) { 
    return new Promise((resolve, reject) => { 
        const worker = new Worker( 
                './sendRotation.js', { workerData }); 
                worker.on('message', resolve); 
                worker.on('error', reject); 
                worker.on('exit', (code) => { 
            if (code !== 0) 
                reject(new Error( 
`Stopped runServiceCamRotage the Worker Thread with the exit code: ${code}`)); 
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
        var myquery = {$set: {'statusPIC': msg , 'versionSW' : apiVersion}};
        //myquery['CarID'] = car_id ;
        dbo.collection("status").updateOne({},myquery, function(err, _res) {
            if (err)
                throw err;
            db.close();
        });
      });
} 


async function mainV3() 
{ 
    await getCameraOnline();
    console.log('CAR ID : ' + carID);
    console.log('Server URL : ' + server);
    console.log('Camera Count  : ' + numCamera);
    console.log('API Version  : ' + apiVersion);
    console.log('Start Main V3');
    printAPI_DIS();

    
    
    var numCam = arrayCamOnline.length;
    console.log(arrayCamOnline);
    console.log(numCam);
    //update num cam status
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
    console.log("Loop Start");
    for (var iCount =1; iCount < 5 ; iCount++) 
    {
        var msgCam =  'CAM'+ iCount;
        //console.log(msgCam);
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

    for (var iCount = 0; iCount < 4 ; iCount++) 
    {
        timeStartResetCAM[iCount] = Date.now(); 
    }
 
    

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
            for (let cam of arrayResult) 
            {
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

                }else
                {
                    var size = sizeof(cam);
                    //console.log(size);
                    if(size > 100000)
                    {
                        sizeOfPic += size;
                        arrayCamError.push(cam.Name +' Ok')
                        arrayCamPic.push(cam);
                        arrayCamErrorCount[countCam] = 0;
                        
                        if(sendRotagetionPic[0] == 0 && cam.Name == "CAM1" )
                        {
                            sendRotagetionPic[0] = 1;
                            const result = runServiceCamRotage(cam.Name);
                            console.log('Send Rotation ' + cam.Name + ' Send ' + result);
                        }else if(sendRotagetionPic[1] == 0 && cam.Name == "CAM2" )
                        {
                            sendRotagetionPic[1] = 1;
                            const result = runServiceCamRotage(cam.Name);
                            console.log('Send Rotation ' + cam.Name + ' Send ' + result);
                        }else if(sendRotagetionPic[2] == 0 && cam.Name == "CAM3" )
                        {
                            sendRotagetionPic[2] = 1;
                            const result = runServiceCamRotage(cam.Name);
                            console.log('Send Rotation ' + cam.Name + ' Send ' + result);
                        }else if(sendRotagetionPic[3] == 0 && cam.Name == "CAM4" )
                        {
                            sendRotagetionPic[3] = 1;
                            const result = runServiceCamRotage(cam.Name);
                            console.log('Send Rotation ' + cam.Name + ' Send ' + result);
                        }

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
                //var url = server + '/api/snapshot/postAmbulanceImageUpload';
                //if(countSend%10 == 0)
                //{
                //    url = 'http://202.183.192.149:3000/fileupload';
                //}

                const r = request.post(url, function optionalCallback(err, httpResponse, body) {
                    if (err) {
                        LED.writeSync(0);
                        console.error(err);
                        arrayCamError.push('Send Error')
                        GetPicError += 1;
                    }
                    console.log('Time:'+((programEnd - Date.now())/1000  )+ ' Num:'+countCam +' Count:'+countSend + ' Size: '+ (sizeOfPic/1000) +' kb Code:', httpResponse && httpResponse.statusCode);
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

                            //IO_CAM1.writeSync(0);
                            //await wasteTime(2000);
                            //IO_CAM1.writeSync(1);           
                        }

                        if(iCount == 1)
                        {
                            console.log('-------------CAM'+ (iCount+1) + ' Reset');

                            //IO_CAM2.writeSync(0);
                            //await wasteTime(2000);
                            //IO_CAM2.writeSync(1);           
                        }

                        if(iCount == 2)
                        {
                            console.log('-------------CAM'+ (iCount+1) + ' Reset');

                            //IO_CAM3.writeSync(0);
                            //await wasteTime(2000);
                            //IO_CAM3.writeSync(1);           
                        }

                        if(iCount == 3)
                        {
                            console.log('-------------CAM'+ (iCount+1) + ' Reset');

                            //IO_CAM4.writeSync(0);
                            //await wasteTime(2000);
                            //IO_CAM4.writeSync(1);           
                        }
                        
                    }//end if((Date.now() - timeStartResetCAM[iCount]) > 180000)//4 min
                }
            }//end Reset Cam
        }//While
 
   
    console.log("Process Pic upload END...");
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


function startCAM1()
{
    console.log('CAM1 : Start');
    cameras[0].liveffmpeg = child_process.spawn("ffmpeg", [
        "-rtsp_transport", "tcp", "-i", cameras[0].rtsp,"-s", "640x360", "-vf" , "fps=1.5","-an","-sn", 
        "-f", "image2pipe" ,"-"   // output to stdout
        ]);

    cameras[0].liveStarted = true;
    cameras[0].updateTime = Date.now();

    cameras[0].liveffmpeg.on('error', function (err) {
        
        console.log('CAM1 : error '+err);
    });

    cameras[0].liveffmpeg.on('close', function (code) {
        //cameras[0].liveffmpeg.kill();
        cameras[0].liveStarted = false;
        console.log('CAM1 : ffmpeg exited with code ' + code);
    });

    cameras[0].liveffmpeg.stderr.on('data', function (data) {
        //console.log('stderr: ' + data);
        var tData = data.toString('utf8');
        var a = tData.split('[\\s\\xA0\\n]+');
        //a = a.split('\n');
        a = 'CAM1 : '+ a;
        //console.log(a);
        cameras[0].updateTime = Date.now();
    }); 

    cameras[0].liveffmpeg.stdout.on('data', function (data) 
    {
        cameras[0].data = data;
        cameras[0].dataUpdate = true;
        //var frame =  Buffer.from(data).toString('base64');
        //var base64Data = frame.replace(/^data:image\/png;base64,/, "");
        // console.log(frame);
        //cv2.imwrite('99.png', frame)
        //require("fs").writeFile("out.png", frame, 'base64', function(err) {
        //    console.log(err);
        //  });

        //console.log('CAM1 : get pic');

    });
    
}

function startCAM2()
{
    console.log('CAM2 : Start');
    cameras[1].liveffmpeg = child_process.spawn("ffmpeg", [
        "-rtsp_transport", "tcp", "-i", cameras[1].rtsp,"-s", "640x360", "-vf" , "fps=1.5", "-an", "-sn", 
        "-f", "image2pipe" , "-" // output to stdout
        ]);
    cameras[1].liveStarted = true;
    cameras[1].updateTime = Date.now();

    cameras[1].liveffmpeg.on('error', function (err) {
       
        console.log('CAM2 : error'+err);
    });

    cameras[1].liveffmpeg.on('close', function (code) {
        //cameras[0].liveffmpeg.kill();
        cameras[1].liveStarted = false;
        console.log('CAM2 : ffmpeg exited with code ' + code);
    });

    cameras[1].liveffmpeg.stderr.on('data', function (data) {
        var tData = data.toString('utf8');
        var a = tData.split('[\\s\\xA0\\n]+');
        //a = a.split('\n');
        a = 'CAM2 : '+ a;
        //console.log(a);
        cameras[1].updateTime = Date.now();
    });

    cameras[1].liveffmpeg.stdout.on('data', function (data) {
    cameras[1].data = data;
    cameras[1].dataUpdate = true;
        //console.log('CAM2 : get pic');
    });
}

async function apiV4() 
{
    //console.log('loop');
    var arrayCamError = [];
        //arrayCamError.push('APIV4')
        /*
        //console.log(cameras[0].liveStarted);
        //console.log(cameras[1].liveStarted);
        if (cameras[0].liveStarted === false)
        {
            if (typeof cameras[0].liveffmpeg !== "undefined") 
            {
                //cameras[0].liveffmpeg.kill();
            }
            await wasteTime(2000);
            console.log('CAM1 : liveStarted');
            //startCAM1();
        }

        if (cameras[1].liveStarted === false)
        {
            if (typeof cameras[1].liveffmpeg !== "undefined") 
            {
                //cameras[1].liveffmpeg.kill();
            }
            await wasteTime(2000);
            console.log('CAM2 : liveStarted');
            //startCAM2();
        } */

        var currentTime = await Date.now();

        if( (currentTime - cameras[0].updateTime) > 10000)
        {
            cameras[0].updateTime = currentTime;
            cameras[0].liveStarted = false;
            console.log('CAM1 : Live TimeOut');
            cameras[0].liveffmpeg.kill();
            startCAM1();
        }

        if( (currentTime - cameras[1].updateTime) > 10000)
        {
            cameras[1].updateTime = currentTime;
            cameras[1].liveStarted = false;
            console.log('CAM2 : Live TimeOut');
            cameras[1].liveffmpeg.kill();
            startCAM2();
        }

        var size1 = sizeof(cameras[0].data);
        var size2 = sizeof(cameras[1].data);
        var countPic = 0;

        if(cameras[0].dataUpdate == true)
        {
            arrayCamError.push('CAM1 OK')
            countPic++;
            if(sendRotagetionPic[0] == 0)
            {
                sendRotagetionPic[0] = 1;
                const result = runServiceCamRotage("CAM1");
                console.log('Send Rotation CAM1 Send ' + result);
            }

        }else{
            arrayCamError.push('CAM1 Error')
        }

        if(cameras[1].dataUpdate == true)
        {
            countPic++;
            arrayCamError.push('CAM2 OK')
            if(sendRotagetionPic[1] == 0)
            {
                sendRotagetionPic[1] = 1;
                const result = runServiceCamRotage("CAM2");
                console.log('Send Rotation CAM2 Send ' + result);
            }
        }else{
            arrayCamError.push('CAM2 Error')
        }

        var numCam = arrayCamOnline.length;


        if(countPic >= numCam)
        {
            timeRestart = currentTime;
        }

        if((currentTime - timeRestart) > 10000)
        {
            console.log('Ex with time our camnum 1');
            process.exit(1);
        }

        if(countPic == 2) 
        {
            countWaitTwoPic++;
            if(countWaitTwoPic > 10)countWaitTwoPic = 10;
            if(countWaitTwoPic < 0)countWaitTwoPic = 0; 
        }else{
            countWaitTwoPic--;
            if(countWaitTwoPic < -20)
            {
                //console.log('Ex with cam error');
                //process.exit(1);
                countWaitTwoPic = -20;  
            }

        }


        try
        {
            //if(size1 > 10000 && size2 > 10000)
            var sendPicCondition = false;
            if( countWaitTwoPic > 5)
            {
                if( cameras[0].dataUpdate == true && cameras[1].dataUpdate == true)
                {
                    sendPicCondition = true;
                }
                    
            }else{
                if(countPic > 0)
                    sendPicCondition = true;
            }
                

            if(sendPicCondition == true)
            {
               
                LED.writeSync(1);

                var url = server +':3000/fileupload'
                //var url = server + '/api/snapshot/postAmbulanceImageUpload';
                //if(countSend%10 == 0)
                //{
                //    url = 'http://202.183.192.149:3000/fileupload';
                //}
                const r = request.post(url, function optionalCallback(err, httpResponse, body) 
                {
                    if (err) 
                    {
                        console.error(err);
                        arrayCamError.push('Send Error');
                    }
                    console.log('Send : '+countSend + ' Num: '+countPic+' Size: '+ ((size1+size2)/1000) +' Kb Code:', httpResponse && httpResponse.statusCode);
                })

                const form = r.form();
                const picdata1 = cameras[0].data;
                const picdata2 = cameras[1].data;

                

                form.append('ID', carID);
                form.append('Time', countSend++);
                if(cameras[0].dataUpdate == true )
                {
                    form.append("CAM1",  Buffer.from(picdata1), {
                        filename: 'cam1.jpg',
                        contentType: 'image/jpeg'
                    });   
                }
              
                if(cameras[1].dataUpdate == true )
                {
                    form.append("CAM2",  Buffer.from(picdata2), {
                        filename: 'cam2.jpg',
                        contentType: 'image/jpeg'
                    });    
                }

                cameras[0].dataUpdate = false;
                cameras[1].dataUpdate = false;

                arrayCamError.push('Send OK');
                
                await wasteTime(50);
                
                LED.writeSync(0);
                
                //cameras[0].data = "";
                //cameras[1].data = "";
            }

        }catch(error)
        {
            console.log("UP Pic request Error");
            arrayCamError.push('Send Error');
        }

        camStatus(arrayCamError);

}

async function apiV5() 
{
    var arrayCamError = [];
    var currentTime = await Date.now();

    if( (currentTime - cameras[0].updateTime) > 10000)
    {
        cameras[0].updateTime = currentTime;
        cameras[0].liveStarted = false;
        console.log('CAM1 : Live TimeOut');
        cameras[0].liveffmpeg.kill();
        startCAM1();
    }

    if( (currentTime - cameras[1].updateTime) > 10000)
    {
        cameras[1].updateTime = currentTime;
        cameras[1].liveStarted = false;
        console.log('CAM2 : Live TimeOut');
        cameras[1].liveffmpeg.kill();
        startCAM2();
    }

    var size1 = sizeof(cameras[0].data);
    var size2 = sizeof(cameras[1].data);
    var countPic = 0;

    if(cameras[0].dataUpdate == true)
    {
        arrayCamError.push('CAM1 OK')
        countPic++;
        if(sendRotagetionPic[0] == 0)
        {
            sendRotagetionPic[0] = 1;
            const result = runServiceCamRotage("CAM1");
            console.log('Send Rotation CAM1 Send ' + result);
        }

    }else{
        arrayCamError.push('CAM1 Error')
    }

    if(cameras[1].dataUpdate == true)
    {
        countPic++;
        arrayCamError.push('CAM2 OK')
        if(sendRotagetionPic[1] == 0)
        {
            sendRotagetionPic[1] = 1;
            const result = runServiceCamRotage("CAM2");
            console.log('Send Rotation CAM2 Send ' + result);
        }
    }else{
        arrayCamError.push('CAM2 Error')
    }

    if(countPic > 0)
    {
        timeRestart = currentTime;
    }

    if((currentTime - timeRestart) > 10000)
    {
        process.exit(1);
    }


        //try
        //{
            //if(size1 > 10000 && size2 > 10000)
            if(cameras[0].dataUpdate == true || cameras[1].dataUpdate == true)
            {
               
                LED.writeSync(1);

                /*const picdata1 = cameras[0].data;
                const picdata2 = cameras[1].data;

                cameras[0].dataUpdate = false;
                cameras[1].dataUpdate = false;


                optionsToNewServer.url = server+"/api/snapshot/postAmbulanceImageUpload"
                console.log(optionsToNewServer.url);
                optionsToNewServer.formData.ambulance_id = carID;
                optionsToNewServer.formData.ambulance_box_code = carID;
                optionsToNewServer.formData.images_count = picNum;

                optionsToNewServer.formData.images_name_1.value = '';
                optionsToNewServer.formData.images_name_1.options.filename = 'cam1.jpg';
                optionsToNewServer.formData.images_name_2.value = Buffer.from(picdata1);
                optionsToNewServer.formData.images_name_2.options.filename = 'cam2.jpg';
                optionsToNewServer.formData.images_name_3.value = Buffer.from(picdata2);
                optionsToNewServer.formData.images_name_3.options.filename = 'cam3.jpg';
                optionsToNewServer.formData.images_name_4.value = '';
                optionsToNewServer.formData.images_name_4.options.filename = 'cam4.jpg';
               


                request(optionsToNewServer, function (error, response) 
                  {
                    try {
                      console.log('Send : '+countSend + ' Num: '+countPic+' Size: '+ (size2/1000) +':'+  (size2/1000) + 'Kb Code:', response.statusCode);
                    } catch (error) {
                      //console.error(error);
                    } 
                  })
               */

                var url = server + '/api/snapshot/postAmbulanceImageUpload';
                if(countSend%30 == 0)
                {
                    url = 'http://202.183.192.149:3000/fileupload';
                }

                const r = request.post(url, function optionalCallback(err, httpResponse, body) 
                {
                    if (err) 
                    {
                        console.error(err);
                        arrayCamError.push('Send Error');
                    }
                    console.log('Send : '+countSend + ' Num: '+countPic+'  Size: '+ (size1/1000) +':'+  (size2/1000) +' Kb Code:', httpResponse && httpResponse.statusCode);
                })

                const form = r.form();
                const picdata1 = cameras[0].data;
                const picdata2 = cameras[1].data;

                

                form.append('ID', carID);
                form.append('ambulance_id', carID);
                form.append('ambulance_box_code', carID);
                form.append('images_count', 2);
                form.append('Time', countSend++);

                if(cameras[0].dataUpdate == true )
                {
                    form.append("CAM1",  Buffer.from(picdata1), {
                        filename: 'cam1.jpg',
                        contentType: 'image/jpeg'
                    });   
                }
              
                if(cameras[1].dataUpdate == true )
                {
                    form.append("CAM2",  Buffer.from(picdata2), {
                        filename: 'cam2.jpg',
                        contentType: 'image/jpeg'
                    });    
                }

                cameras[0].dataUpdate = false;
                cameras[1].dataUpdate = false;



                arrayCamError.push('Send OK');
                
                await wasteTime(50);
                
                LED.writeSync(0);
                
                //cameras[0].data = "";
                //cameras[1].data = "";
            }

        //}catch(error)
        //{
        //    console.log("UP Pic request Error");
        //    arrayCamError.push('Send Error');
       // }

        camStatus(arrayCamError);

}

async function mainV4() 
{ 

    //await getCameraOnline();
    console.log('CAR ID : ' + carID);
    console.log('Server URL : ' +server);
    console.log('Camera Count  : ' + numCamera);
    var numCam = arrayCamOnline.length;
    console.log('Camera Online  : ' + numCam);
    console.log('API Version  : ' + apiVersion);
    printAPI_DIS();
   
    startCAM1();
    startCAM2();
    timeRestart = Date.now();
    cameras[0].updateTime = Date.now();
    cameras[1].updateTime = Date.now();
    if(apiVersion == 4)
    {
        setInterval(apiV4, 700);
    }
    if(apiVersion == 5)
    {
        setInterval(apiV5, 700);
    }
        


    //var ffmpeg = require('child_process').spawn('/usr/local/Cellar/ffmpeg/3.3.1/bin/ffmpeg', ['-f', 'avfoundation', '-framerate', '30', '-video_size', '640x480', '-pix_fmt', 'uyvy422', '-i', '0:1', '-f', 'mpegts', '-codec:v', 'mpeg1video', '-s', '640x480', '-b:v', '1000k', '-bf', '0', 'http://localhost:8081/test']);
    //var ffmpeg = child_process.spawn("ffmpeg", [
    //    "-rtsp_transport", "tcp", "-i" , cameras[0].rtsp, "-acodec", "copy", "-r", "10", "-s", "426x240", "-f", "flv", 
    //    "-"   // output to stdout
    //    ]);
    //ffmpeg -i rtsp://<rtsp_source_addr> -vf fps=fps=1/20 -update 1 img.jpg
    //ffmpeg1_call = "ffmpeg -rtsp_transport tcp -i rtsp://192.168.100.201/ch0_1.h264 -acodec copy -r 10 -s 426x240 -f flv "+ rtspURL +"/"+ topic +"CAM1"
    //ffmpeg -i 'rtsp://192.168.4.20/user=admin&password=&channel=1&stream=0.sdp' -f image2 -vframes 1 -pix_fmt yuvj420p /volume1/@appstore/domoticz/var/scripts/plaatje.jpg
    //var ffmpeg = child_process.spawn("ffmpeg", [
    //       "-rtsp_transport" ,"tcp" ,"-i" , cameras[0].rtsp, "-vcodec", "copy",
    //        //"-r", "10", "-s","426x240",
    //        "pipe:1"   // output to stdout
    //       ]);

    //cameras[0].liveffmpeg = child_process.spawn("ffmpeg", [
    //    "-rtsp_transport", "tcp", "-i", cameras[0].rtsp, "-vcodec", "copy", "-f", "mp4", "-movflags", "frag_keyframe+empty_moov", 
    //    "-reset_timestamps", "1", "-vsync", "1","-flags", "global_header", "-bsf:v", "dump_extra", "-y", "-"   // output to stdout
    //   ],  {detached: false});
    console.log('Start loop');
    //while(Date.now() < programLoopTimeDiff+1000 )
    //cameras[0].liveffmpeg.kill();
    //cameras[1].liveffmpeg.kill();
    console.log('Out');

}


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


setup().catch(err => console.error(err)) 
