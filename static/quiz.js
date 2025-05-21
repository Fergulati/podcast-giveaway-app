let player;

function fetchQuestion() {
    if (!CHANNEL_ID) return;
    fetch(`/api/quiz/${CHANNEL_ID}`)
        .then((r) => r.json())
        .then((data) => {
            document.getElementById('quiz-question').textContent = data.question || '';
            const list = document.getElementById('quiz-options');
            list.innerHTML = '';
            (data.options || []).forEach((opt) => {
                const li = document.createElement('li');
                li.textContent = opt;
                list.appendChild(li);
            });
        })
        .catch((err) => console.error('Quiz fetch failed', err));
}

function onYouTubeIframeAPIReady() {
    const iframe = document.getElementById('player');
    if (!iframe) return;
    player = new YT.Player(iframe, {
        events: {
            onStateChange: onPlayerStateChange,
        },
    });
}

function onPlayerStateChange(event) {
    if (event.data === YT.PlayerState.PAUSED ||
        event.data === YT.PlayerState.PLAYING ||
        event.data === YT.PlayerState.BUFFERING ||
        event.data === YT.PlayerState.ENDED) {
        fetchQuestion();
    }
}

document.addEventListener('DOMContentLoaded', fetchQuestion);
