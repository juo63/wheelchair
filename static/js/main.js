// 추천 결과를 화면에 표시하는 함수
function displayRecommendations(recommendations) {
    const resultSection = document.getElementById('results');
    const recommendationList = document.getElementById('recommendationList');
    recommendationList.innerHTML = '';

    recommendations.forEach(item => {
        const card = document.createElement('div');
        card.className = 'recommendation-card';

        let imageHtml = '';
        if (item.image) {
            imageHtml = `<img src="${item.image}" alt="${item.name}" class="product-image" onerror="this.style.display='none'; this.parentElement.classList.add('no-image');">`;
        }

        // 키워드를 HTML로 변환
        const keywordsHtml = item.keywords
            .map(keyword => `<span class="feature">${keyword}</span>`)
            .join('');

        card.innerHTML = `
            ${imageHtml}
            <div class="product-info">
                <h3>${item.name}</h3>
                <p class="manufacturer">제조사: ${item.manufacturer}</p>
                <p class="weight">무게: ${item.weight}kg</p>
                <p class="seat-width">좌폭: ${item.seatWidth}cm</p>
                <div class="features">
                    ${keywordsHtml}
                </div>
            </div>
        `;

        recommendationList.appendChild(card);
    });

    resultSection.style.display = 'block';
    resultSection.scrollIntoView({ behavior: 'smooth' });
}

// 로딩 표시 함수
function toggleLoading(show) {
    const loading = document.getElementById('loading');
    loading.style.display = show ? 'flex' : 'none';
}

// 예시 텍스트 설정 함수
function setExample(text) {
    document.getElementById('userInput').value = text;
}

// 일반 추천 함수
async function getRecommendations() {
    const userInput = document.getElementById('userInput').value.trim();
    
    if (!userInput) {
        alert('추천을 원하시는 내용을 입력해주세요.');
        return;
    }

    toggleLoading(true);

    try {
        const response = await fetch('/api/recommend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: userInput })
        });

        const data = await response.json();

        if (data.success) {
            displayRecommendations(data.recommendations);
        } else {
            alert(data.message || '추천 과정에서 오류가 발생했습니다.');
        }
    } catch (error) {
        alert('서버와의 통신 중 오류가 발생했습니다.');
        console.error('Error:', error);
    } finally {
        toggleLoading(false);
    }
}

// 빠른 추천 함수
async function quickRecommend(type) {
    toggleLoading(true);

    try {
        const response = await fetch('/api/quick-recommend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ type: type })
        });

        const data = await response.json();

        if (data.success) {
            displayRecommendations(data.recommendations);
        } else {
            alert(data.message || '추천 과정에서 오류가 발생했습니다.');
        }
    } catch (error) {
        alert('서버와의 통신 중 오류가 발생했습니다.');
        console.error('Error:', error);
    } finally {
        toggleLoading(false);
    }
}

// Enter 키 이벤트 처리
document.getElementById('userInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        getRecommendations();
    }
}); 