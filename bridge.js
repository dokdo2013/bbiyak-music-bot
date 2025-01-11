const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const Redis = require('ioredis');
const path = require('path');
const dotenv = require('dotenv');

dotenv.config();

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
const redisPub = new Redis(); // Redis Publisher
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

// youtube url이 제공되었을 때 video 제목을 추출하는 endpoint
app.get('/video', (req, res) => {
  const { url } = req.query;
  if (!url) {
    return res.status(400).send('URL is required');
  }

  const cacheKey = `video_url:${url}`;
  redisPub.get(cacheKey, (err, cachedData) => {
    if (err) {
      console.error('Redis Error:', err);
      return res.status(500).json({ error: 'Failed to get cached data' });
    }

    if (cachedData) {
      return res.json(JSON.parse(cachedData));
    }

    const videoId = url.split('v=')[1];
    if (!videoId) {
      return res.status(400).send('Invalid URL');
    }

    const apiKey = process.env.GOOGLE_API_KEY;
    const apiUrl = `https://www.googleapis.com/youtube/v3/videos?part=snippet&id=${videoId}&key=${apiKey}`;

    fetch(apiUrl)
        .then((response) => response.json())
        .then((data) => {
          const videoTitle = data.items[0]?.snippet?.title || 'Unknown';

          const responseData = { title: videoTitle };
          redisPub.set(cacheKey, JSON.stringify(responseData));
          res.json(responseData);
        })
        .catch((error) => {
            console.error('Error:', error);
            res.status(500).json({ error: 'Failed to get video title' });
        });
  });
});