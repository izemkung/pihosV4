var mongo = require('mongodb');
var mongoClient = require('mongodb').MongoClient;
var urlMongo = "mongodb://127.0.0.1:27017/";//currentPicURL



mongoClient.connect(urlMongo, function(err, db) {
    if (err) 
    {
        console.log(err);
        throw err;

    }

    var dbo = db.db("pihos");
    //myquery['CarID'] = car_id ;
    dbo.collection("configs").findOne({}, function(err, _res) {
        if (err) 
        {
            console.log(err);
            throw err;

        }
        console.log(_res);
        dbo.collection("status").findOne({}, function(err, _res) {
            if (err) 
            {
                console.log(err);
                throw err;
    
            }
            console.log(_res);
            db.close();
        });
    });
    
  });
