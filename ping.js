var ping = require('ping');
 
var hosts = ['192.168.100.201', '192.168.100.202', '192.168.100.203', '192.168.100.204'];
var count = 1;
hosts.forEach(function(host){
    ping.sys.probe(host, function(isAlive){

        var msg = isAlive ? 'host ' + host + ' CAM'+ count + ' is alive' : 'host ' + host + ' CAM'+ count + ' is dead';
        count++;
        console.log(msg);
    });
});
//exec("ping -c 3 192.168.100.203", puts);