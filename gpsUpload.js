

var gpsd = require('node-gpsd');
var GPS = require('gps');
var gps = new GPS;

var sentence = '$GPGGA,224900.000,4832.3762,N,00903.5393,E,1,04,7.8,498.6,M,48.0,M,,0000*5E';


var listener = new gpsd.Listener({
    port: 2947,
    hostname: 'localhost',
    logger:  {
        info: function() {},
        warn: console.warn,
        error: console.error
    },
    parse: false
});

listener.connect(function() {
    console.log('Connected');
});

//not going to happen, parse is false
listener.on('TPV', function(data) {
  console.log(data);
});

// parse is false, so raw data get emitted.
listener.on('raw', function(data) {
  //console.log(data);
  gps.update(data);
});

gps.on('data', function(parsed) {

    //console.log(parsed);

    var lat1 = gps.state.lat;
    var lon1 = gps.state.lon;

    // Find closest confluence point as destination
    var lat2 = Math.round(lat1);
    var lon2 = Math.round(lon1);

    var dist = GPS.Distance(lat1, lon1, lat2, lon2);
    var head = GPS.Heading(lat1, lon1, lat2, lon2);

    console.log("\033[2J\033[;H" + 
    "You are at (" + lat1 + ", " + lon1 + "),\n" +
    "The closest confluence point (" + lat2 + ", " + lon2 + ") is in " + dist + " km.\n" +
    "You have to go " + head + "° " );


  });


listener.watch({class: 'WATCH', nmea: true});