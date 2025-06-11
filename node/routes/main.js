const express = require('express');
const router = express.Router();

router.get('/', (req, res) => {
  res.sendFile('index.html', { root: 'public' });
});

// 추가 라우트는 여기에 작성

module.exports = router;
