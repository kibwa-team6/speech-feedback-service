let recognition;
let isRecording = false;
let startTime;
let wordCount = 0;
let fillerWords = new Set(['음', '어', '그', '저', '이제', '뭐', '아니']);
let fillerWordCount = 0;

if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'ko-KR';

    const startButton = document.getElementById('startButton');
    const stopButton = document.getElementById('stopButton');
    const status = document.getElementById('status');
    const transcript = document.getElementById('transcript');
    const wpmDisplay = document.getElementById('wpm');
    const fillerWordsDisplay = document.getElementById('fillerWords');

    startButton.addEventListener('click', async () => {
        try {
            // 마이크 권한 요청
            await navigator.mediaDevices.getUserMedia({ audio: true });
            isRecording = true;
            startTime = Date.now();
            wordCount = 0;
            fillerWordCount = 0;
            
            recognition.start();
            startButton.disabled = true;
            stopButton.disabled = false;
            status.textContent = '녹음 중...';
            transcript.textContent = '';
        } catch (err) {
            console.error('마이크 권한 요청 실패:', err);
            status.textContent = '마이크 권한이 필요합니다.';
        }
    });

    stopButton.addEventListener('click', () => {
        isRecording = false;
        recognition.stop();
        startButton.disabled = false;
        stopButton.disabled = true;
        status.textContent = '준비됨';
    });

    recognition.onresult = (event) => {
        let interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const result = event.results[i];
            const transcript = result[0].transcript;
            
            if (result.isFinal) {
                processText(transcript);
            } else {
                interimTranscript += transcript;
            }
        }
        
        document.getElementById('transcript').textContent = interimTranscript;
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        status.textContent = '오류 발생: ' + event.error;
    };
} else {
    alert('이 브라우저는 음성 인식을 지원하지 않습니다.');
}

function processText(text) {
    // 단어 수 계산
    const words = text.trim().split(/\s+/);
    wordCount += words.length;

    // Filler words 카운트
    words.forEach(word => {
        if (fillerWords.has(word)) {
            fillerWordCount++;
        }
    });

    // WPM 계산
    const minutes = (Date.now() - startTime) / 60000;
    const wpm = Math.round(wordCount / minutes);

    // 화면 업데이트
    document.getElementById('wpm').textContent = `WPM: ${wpm}`;
    document.getElementById('fillerWords').textContent = `Filler Words: ${fillerWordCount}`;

    // 서버로 데이터 전송
    sendToServer({
        text: text,
        wpm: wpm,
        fillerWordCount: fillerWordCount
    });
}

async function sendToServer(data) {
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error('서버 응답 오류');
        }
        
        const result = await response.json();
        console.log('서버 응답:', result);
    } catch (error) {
        console.error('서버 전송 오류:', error);
    }
}
