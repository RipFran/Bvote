const mysql = require('mysql2');
const express = require('express');
const session = require('express-session');
const path = require('path');
const res = require('express/lib/response');
const keypar = require('keypair');
const forge = require('node-forge');
const {PythonShell} = require('python-shell');
const puertos =[4000,4001,4002,4003];
const router = express.Router();
var request = require('request');
var bodyParser = require('body-parser');
var parche1 = ""

function getRandomInt(min, max) {
    min = Math.ceil(min);
    max = Math.floor(max);
    return Math.floor(Math.random() * (max - min) + min); //The maximum is exclusive and the minimum is inclusive
  }

const connection = mysql.createConnection({
	host     : 'localhost',
	user     : 'alumne',
	password : 'alumne',
	database : 'usuaris'
});

const app = express();
app.set("view engine", "ejs");
app.set('views', path.join(__dirname, 'views'));

app.use(session({
	secret: 'secret',
	resave: true,
	saveUninitialized: true
}));

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'static')));



// http://localhost:3000/
app.get('/', function(request, response) {
	// Render login template
	response.render(__dirname + '/views/login', function(err,html){
		response.send(html);
	})
});

app.get('/menu', function(request, response) {
    //I'm server side
	connection.query('SELECT canVote FROM usuaris WHERE dni= ?', request.session.username, function(error, results, fields) {
		if (error) throw error;
		if (results.length > 0){
			response.render(__dirname + '/views/menu', {varToPass:results[0].canVote},  function (err, html){
				response.send(html);
				response.end();
			})
		}
	});
});

//TODO: varToPass: response.body
app.get('/chain', (req, res) => {
    var puerto=puertos[getRandomInt(0,4)];
    var url = 'http://127.0.0.1:'+puerto+'/chain';
	//var json= "{\"chain\":[{\"previous_hash\":\"1\",\"proof\":100,\"timestamp\":0,\"transactions\":[]},{\"previous_hash\":\"6e01bd90a968f62958ab315ab53283dcd6150676a9a2ec468797186940fd4a65\",\"proof\":78085,\"timestamp\":1654014635.0092134,\"transactions\":[{\"recipient\":\"1\",\"sender\":\"-----BEGIN PUBLIC KEY-----\nMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCtgYMkE/iONJZ2T1JVB5xy9TBBYHRnpqTEI2y/h0suFPKMENXyHulEX9lKphvJr0EccyeuWvKTRvjJdOAv7OPdcKPkuvzTHfzHHAy/Jss0UQScNmNqr+jW9h3+Kzud7LK3FIBA032PjLzMgWtdpNkn4Yj+vsjP1yYvtc3qpShVnQIDAQAB\n-----END PUBLIC KEY-----\",\"signature\":\"96,124,138,188,3,23,59,22,223,244,138,123,9,101,66,46,60,255,145,5,231,25,101,72,141,247,207,200,160,195,90,86,218,134,195,219,136,238,42,14,159,165,249,151,139,71,107,13,156,110,84,137,41,11,16,201,193,172,202,224,57,110,50,108,59,204,124,180,23,176,184,65,119,237,44,197,119,213,231,73,12,38,45,251,40,169,238,100,152,138,84,74,166,64,98,177,212,62,174,151,248,220,41,149,137,234,88,165,64,240,173,176,203,130,159,4,43,214,228,90,168,28,39,180,64,20,218,47\"}]}],\"length\":2}"
	request.get({
		url:     url

	}, function(error, response, body){
		res.render(__dirname + '/views/chain', {varToPass: response.body}, function (err, html){
			res.setHeader("Content-Type","text/html")
			res.status(200).send(html);
			res.end();
		})	
	});
});


app.get('/results', (req, res) => {
    var puerto=puertos[getRandomInt(0,4)];
    var url = 'http://127.0.0.1:'+puerto+'/results';
    
	request.get({
		url:     url

	}, function(error, response, body){
		res.render(__dirname + '/views/results', {varToPass:response.body}, function (err, html){
			res.setHeader("Content-Type","text/html")
			res.status(200).send(html);
			res.end();
		})	
	});
});


var string_partidos = "";
var votacio = "";
var string_isGenerated = "";

var privateKey;
var publicKey;

app.post('/updateDB',function(request,response){
	publicKey = JSON.parse(JSON.stringify(request.body)).a;

	const connection3 = mysql.createConnection({
		host     : 'localhost',
		user     : 'alumne',
		password : 'alumne',
		database : votacio
	});

	//INSERTA DENTRO DE SENDERS LA PUBLIC KEY
	connection3.query('INSERT into sendersPK values(?)' , [publicKey], function(error, results, fields) {
	})

	let myArray = string_isGenerated.split(',');
	const index = myArray.indexOf(votacio);
	myArray.splice(index,1);
	
	string_isGenerated = "";
	for (let i = 0; i < myArray.length; ++i){
		if (myArray[i] != "") string_isGenerated += myArray[i] + ',';
	}

	//S'HA DE DESCOMENTAR
	//MODIFICA EL CAMPO DE LA DB 
	connection.query('UPDATE usuaris SET isGenerated = ? where dni = ?', [string_isGenerated, request.session.username], function(error, results, fields) {
	}) 

	response.status(200).send(); 
});

app.post('/isGenerated', function(request, response) {
	
	votacio = JSON.parse(JSON.stringify(request.body)).a;	

	//BUSCA SI SE HA GENERADO UNA CLAVE PUBLICA O PRIVADA
	connection.query('SELECT isGenerated from usuaris where dni = ?', [request.session.username], function(error, results, fields) {
		var resultado = results[0].isGenerated;
		string_isGenerated = results[0].isGenerated;

		resultado=resultado.split(',')
		if (resultado.includes(votacio)){

			response.status(200).send(); 
		}

		else{
			response.status(400).send(); 
		}

	})
	
});

app.post('/sign', function(req, res) {

	publicKey=req.body.c;
    firma = req.body.a;
	whoimvoting = req.body.b;
	string_firma = "";

	for (var clave in firma){
		if (firma.hasOwnProperty(clave)){
			string_firma += firma[clave] + ',';
		}
	}

	string_firma2 = string_firma.substring(0,string_firma.length - 1);

	var jsonString = {
		"sender": publicKey,
		"recipient": whoimvoting,
		"signature": string_firma2
	  };

	  var jsonObj = JSON.parse(JSON.stringify(jsonString));
		
        var puerto=puertos[getRandomInt(0,3)];
        var url = 'http://127.0.0.1:'+puerto+'/transactions/new';
        var headers={"content-type": "application/json"};

        request.post({
            headers: headers,
            url:     url,
            json:   true,
            body:    jsonObj

        }, function(error, response, body){
        });

	
    res.end();
    //response.send(200);

})


app.get('/partits', function(request, response){
	
	const connection2 = mysql.createConnection({
		host     : 'localhost',
		user     : 'alumne',
		password : 'alumne',
		database : votacio
	});

	connection2.query('SELECT entidad from recipientsPK' , function(error, results, fields) {
		if (results.length > 0) {
			let resultado = results[0].entidad + ',';

			for (let i = 1; i < results.length; ++i){
				resultado += results[i].entidad + ',';
			}
			response.render(__dirname + '/views/partidos', { varToPass2: resultado});
		}
	});  
	
});



// http://localhost:3000/auth
app.post('/auth', function(request, response) {
	// Capture the input fields
	let username = request.body.username;
	let password = request.body.password;
	// Ensure the input fields exists and are not empty
	if (username && password) {
		// Execute SQL query that'll select the account from the database based on the specified username and password
		connection.query('SELECT * FROM usuaris WHERE dni = ? AND passwd = ?', [username, password], function(error, results, fields) {
			// If there is an issue with the query, output the error
			if (error) throw error;
			// If the account exists
			if (results.length > 0) {
				// Authenticate the user
				request.session.loggedin = true;
				request.session.username = username;
				// Redirect to home page
				response.redirect('home');
			} else {
				response.send('Incorrect Username and/or Password!');
			}			
			response.end();
		});
	} else {
		response.send('Please enter Username and Password!');
		response.end();
	}
});

// http://localhost:3000/home
app.get('/home', function(request, response) {
	// If the user is loggedin
	if (request.session.loggedin) {
		// Output username
		response.redirect('/menu');
	} else {
		// Not logged in
		response.send('Please login to view this page!');
	}
	response.end();
});

app.post('/canIvote', function(request, response) {
	connection.query('SELECT hasVoted from usuaris where dni = ?', [request.session.username], function(error, results, fields) {
		var resultado = results[0].hasVoted;
		var string_hasVoted="";
		resultado=resultado.split(',')
		if (resultado.includes(votacio)){
			const index = resultado.indexOf(votacio);
			resultado.splice(index,1);
			for (let i = 0; i < resultado.length; ++i){
				if (resultado[i] != "") string_hasVoted += resultado[i] + ',';
			}
			connection.query('UPDATE usuaris SET hasVoted = ? where dni = ?', [string_hasVoted, request.session.username], function(error, results, fields) {
			}) 
			response.status(200).send(); 

		}

		else{
			response.status(400).send(); 
		}

	})

});



app.listen(3000);
