const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const Redis = require('ioredis');
const path = require('path');

// Express 앱 생성
const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: '*',
  },
});

// Redis 설정
const redis = new Redis(); // Redis 연결
const REDIS_CHANNEL_ID = 'bbybby';

// Redis 구독
redis.subscribe(REDIS_CHANNEL_ID, (err, count) => {
  if (err) {
    console.error('Redis Subscription Error:', err);
    return;
  }
  console.log(`Subscribed to ${count} channel(s).`);
});

// Redis 메시지 수신
redis.on('message', (channel, message) => {
  console.log(`Received data from ${channel}: ${message}`);
  io.emit('new_video', message); // 클라이언트로 URL 전송
});

// Socket.IO 연결
io.on('connection', (socket) => {
  console.log('A client connected');
});

// index.html 파일 서빙
app.use(express.static(path.join(__dirname, 'public')));

// 서버 시작
const PORT = 3000;
server.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
