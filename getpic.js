const fs = require('fs');
const fetch = require('node-fetch');
//const base64Image1;

const url1 = "http://192.168.100.201:8080/cgi-bin/snapshot.sh?res=high&watermark=no"
const url2 = "http://192.168.100.202:8080/cgi-bin/snapshot.sh?res=high&watermark=no"
const url3 = "http://192.168.100.203:8080/cgi-bin/snapshot.sh?res=high&watermark=no"
const url4 = "http://192.168.100.204:8080/cgi-bin/snapshot.sh?res=high&watermark=no"

const pic1Ready = 0;
const pic2Ready = 0;
const pic3Ready = 0;
const pic4Ready = 0;

async function download1() 
{
  const response = await fetch(url1);
  const buffer = await response.buffer();
  const base64Image1 = await buffer.toString('base64');
  //console.log(base64Image1.size);
  //console.log('File Size in Bytes:- ' + base64Image1.size);
  //console.log(base64Image1);
  console.log("PIC1");
  pic1Ready = 1;
  return base64Image1;
  /*
  fs.writeFile('/home/pi/pic/cam1/image.jpg', buffer, function() 
  {
    console.log(buffer.size);
    console.log('finished downloading! 1');
  })*/
    
}

async function download2() {
  const response = await fetch(url2);
  const buffer = await response.buffer();
  const base64Image1 = await buffer.toString('base64'); 
  console.log("PIC2");
  pic2Ready = 1;
  return base64Image1;
}

async function download3() {
  const response = await fetch(url3);
  const buffer = await response.buffer();
  const base64Image1 = await buffer.toString('base64'); 
  console.log("PIC3");
  pic3Ready = 1;
  return base64Image1;
}

async function download4() {
  const response = await fetch(url4);
  const buffer = await response.buffer();
  const base64Image1 = await buffer.toString('base64'); 
  console.log("PIC4");
  pic4Ready = 1;
  return base64Image1;
  //console.log(buffer.size);
  //fs.writeFile('/home/pi/pic/cam4/image.jpg', buffer, () => console.log('finished downloading! 4'));
}

var image1 = download1();
var image2 = download2();
var image3 = download3();
var image4 = download4();
console.log(image1);
console.log(image2);
console.log(image3);
console.log(image4);


/*
var net = require('net');
var client;

require('dns').resolve('www.google.com', function(err) {
  if (err) {
     console.log("No connection");
  } else {
      console.log("Connected internet");

      client = new net.Socket({writeable: true}); //writeable true does not appear to help

      client.on('close', function() {
        console.log('Connection closed');
      });

      client.on('error', function(err) {
        console.error('Connection error: ' + err);
        console.error(new Error().stack);
      });

      client.connect(3000, '202.183.192.149',async function() {
        var count = 0;
        console.log('Connected');
        console.log('IP '+ client.remoteAddress +':'+client.remotePort);


          for(var i = 0; i < 100000; i++) {
            client.write('' + i + '');
            await sleep(10);
          //bufferSize does not seem to be an issue
            console.info(count++);
          }
      });
    

  }
});
*/

function sleep(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}   

/*
 void _upload() {
   if (file == null) return;
   String base64Image1 = base64Encode(file.readAsBytesSync());
   String base64Image2 = base64Encode(file.readAsBytesSync());
   String fileName = file.path.split("/").last;

   http.post(nodeEndPoint, body: {
     "image1": base64Image1,
     "image2": base64Image2,
     "name": fileName,
   }).then((res) {
     print(res.statusCode);
   }).catchError((err) {
     print(err);
   });
 }*/