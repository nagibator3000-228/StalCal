const express = require('express');
const cors = require('cors');
const http = require('http');

const app = express();
app.use(cors({ origin: '*', methods: ['GET','POST'] }));

const server = http.createServer(app);
const io = require('socket.io')(server, {
    cors: {
        origin: '*',
        methods: ['GET','POST']
    }
});

let players = {};

io.on('connection', (socket) => {
    console.log(`Игрок подключился: ${socket.id}`);
    players[socket.id] = { x: 0, y: 0, z: 0 };
    io.emit('update_players', players);

    socket.on('move', (data) => {
        players[socket.id] = data;
        io.emit('update_players', players);
    });

    socket.on('disconnect', () => {
        console.log(`Игрок отключился: ${socket.id}`);
        delete players[socket.id];
        io.emit('update_players', players);
    });
});

server.listen(5000, () => console.log('Сервер запущен на http://localhost:5000'));
