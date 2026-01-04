// Cards component for TRELLIS-style generation cards

// Sample data - replace with your actual data
const text2assetCards = [
    {
        video: "video/3cdba8.mp4",
        prompt: "A woman in blue yoga attire transitions from the Upward-Facing Dog pose to the Downward-Facing Dog pose on a grey yoga mat.",
        image: "images/results/3cdba8.jpg"
    },
    {
        video: "video/2820ff.mp4",
        prompt: "A man wearing a red and black long-sleeved shirt, black shorts, a helmet, and gloves stands next to his mountain bike in a dusty clearing and gestures while talking.",
        image: "images/results/2820ff.jpg"
    },
    {
        video: "video/3b30d9.mp4",
        prompt: "A woman in workout clothes does reverse lunges with her left leg while holding light dumbbells at her chest.",
        image: "images/results/3b30d9.jpg"
    },
    {
        video: "video/dfupki.mp4",
        prompt: "A man in a dark suit walks forward on a stage towards a bright, smoky light source.",
        image: "images/results/dfupki.jpg"
    },
    {
        video: "video/22912e.mp4",
        prompt: "A woman with her hair in a bun, wearing a black top and pants, bends over to harvest leafy greens and places them into a woven basket.",
        image: "images/results/22912e.jpg"
    },
    {
        video: "video/rhvevq.mp4",
        prompt: "A woman wearing a blue t-shirt, camouflage pants, and glasses stands in a forest and pulls back the string of a recurve bow to aim at a target.",
        image: "images/results/rhvevq.jpg"
    }
];

// Dataset results cards data - replace with your actual dataset results
const datasetResultsCards = [
    {
        video: "video/3cdba8.mp4",
        prompt: "A woman in blue yoga attire transitions from the Upward-Facing Dog pose to the Downward-Facing Dog pose on a grey yoga mat.",
        image: "images/results/3cdba8.jpg"
    },
    {
        video: "video/2820ff.mp4",
        prompt: "A man wearing a red and black long-sleeved shirt, black shorts, a helmet, and gloves stands next to his mountain bike in a dusty clearing and gestures while talking.",
        image: "images/results/2820ff.jpg"
    },
    {
        video: "video/3b30d9.mp4",
        prompt: "A woman in workout clothes does reverse lunges with her left leg while holding light dumbbells at her chest.",
        image: "images/results/3b30d9.jpg"
    },
    {
        video: "video/dfupki.mp4",
        prompt: "A man in a dark suit walks forward on a stage towards a bright, smoky light source.",
        image: "images/results/dfupki.jpg"
    },
    {
        video: "video/22912e.mp4",
        prompt: "A woman with her hair in a bun, wearing a black top and pants, bends over to harvest leafy greens and places them into a woven basket.",
        image: "images/results/22912e.jpg"
    },
    {
        video: "video/rhvevq.mp4",
        prompt: "A woman wearing a blue t-shirt, camouflage pants, and glasses stands in a forest and pulls back the string of a recurve bow to aim at a target.",
        image: "images/results/rhvevq.jpg"
    }
];

// Generate card HTML
function generateCardHTML(card, index) {
    // 将卡片数据编码为 JSON 字符串存储在 data 属性中
    const cardData = JSON.stringify(card).replace(/"/g, '&quot;');
    return `
        <div class="generation-card" data-card-index="${index}" data-card-data="${cardData}">
            <div class="generation-card-image-wrapper">
                <video autoplay muted loop playsinline>
                    <source src="${card.video}" type="video/mp4">
                </video>
            </div>
            <div class="generation-card-content">
                <div class="generation-card-description">${card.prompt}</div>
                <div class="generation-card-prompt-image">
                    <img src="${card.image}" alt="Prompt image">
                </div>
            </div>
        </div>
    `;
}

// Initialize cards
function initCards(containerId, wrapperId, cards) {
    const wrapper = document.getElementById(wrapperId);
    if (!wrapper) return;
    
    wrapper.innerHTML = cards.map((card, index) => generateCardHTML(card, index)).join('');
    
    // 为每个卡片添加点击事件监听器
    const cardElements = wrapper.querySelectorAll('.generation-card');
    cardElements.forEach((cardElement, index) => {
        cardElement.addEventListener('click', () => {
            openCardModal(cards[index]);
        });
    });
    
    updateNavigationButtons(containerId);
}

// Scroll cards
function scrollCards(containerId, direction) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const wrapper = container.querySelector('.cards-wrapper');
    if (!wrapper) return;
    
    // 计算卡片宽度（包括gap）
    const card = wrapper.querySelector('.generation-card');
    if (!card) return;
    
    const cardWidth = card.offsetWidth + 16; // card width + gap
    const scrollAmount = cardWidth * 2; // scroll 2 cards at a time
    
    wrapper.scrollBy({
        left: direction * scrollAmount,
        behavior: 'smooth'
    });
    
    // Update navigation buttons after scroll
    setTimeout(() => {
        updateNavigationButtons(containerId);
    }, 300);
}

// Update navigation button states
function updateNavigationButtons(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const wrapper = container.querySelector('.cards-wrapper');
    const prevBtn = container.querySelector('.prev');
    const nextBtn = container.querySelector('.next');
    
    if (!wrapper || !prevBtn || !nextBtn) return;
    
    const scrollLeft = wrapper.scrollLeft;
    const scrollWidth = wrapper.scrollWidth;
    const clientWidth = wrapper.clientWidth;
    
    // Enable/disable prev button
    if (scrollLeft <= 0) {
        prevBtn.classList.add('disabled');
    } else {
        prevBtn.classList.remove('disabled');
    }
    
    // Enable/disable next button
    if (scrollLeft + clientWidth >= scrollWidth - 1) {
        nextBtn.classList.add('disabled');
    } else {
        nextBtn.classList.remove('disabled');
    }
}

// Handle card click - open modal with card details
function openCardModal(card) {
    // 确保窗口系统已初始化
    if (typeof initWindow === 'function') {
        // 检查是否已经初始化
        if (!document.getElementById('fullscreen')) {
            initWindow();
        }
    }
    
    // 生成模态框内容：左侧视频，右侧文本和图片
    const modalContent = `
        <div class="card-modal-container">
            <div class="card-modal-video">
                <video autoplay muted loop playsinline controls>
                    <source src="${card.video}" type="video/mp4">
                </video>
            </div>
            <div class="card-modal-info">
                <div class="card-modal-prompt">
                    <div class="card-modal-prompt-title">Text Prompt</div>
                    <div class="card-modal-prompt-text">${card.prompt}</div>
                </div>
                <div class="card-modal-prompt-image-wrapper">
                    <div class="card-modal-prompt-title">Image Prompt</div>
                    <div class="card-modal-prompt-image">
                        <img src="${card.image}" alt="Prompt image">
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 使用全局的 openWindow 函数
    if (typeof openWindow === 'function') {
        openWindow(modalContent);
    } else {
        console.error('openWindow function not found. Make sure window.js is loaded.');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // 初始化窗口系统
    if (typeof initWindow === 'function') {
        initWindow();
    }
    
    // Initialize text to asset cards
    initCards('text2asset-cards', 'text2asset-wrapper', text2assetCards);
    
    // Add scroll event listener to update navigation buttons
    const text2assetWrapper = document.getElementById('text2asset-wrapper');
    if (text2assetWrapper) {
        text2assetWrapper.addEventListener('scroll', () => {
            updateNavigationButtons('text2asset-cards');
        });
    }
    
    // Add click event listeners to navigation buttons
    const prevBtn = document.getElementById('text2asset-prev');
    const nextBtn = document.getElementById('text2asset-next');
    
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            scrollCards('text2asset-cards', -1);
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            scrollCards('text2asset-cards', 1);
        });
    }
    
    // Initialize dataset results cards
    initCards('dataset-results-cards', 'dataset-results-wrapper', datasetResultsCards);
    
    // Add scroll event listener to update navigation buttons for dataset results
    const datasetResultsWrapper = document.getElementById('dataset-results-wrapper');
    if (datasetResultsWrapper) {
        datasetResultsWrapper.addEventListener('scroll', () => {
            updateNavigationButtons('dataset-results-cards');
        });
    }
    
    // Add click event listeners to navigation buttons for dataset results
    const datasetResultsPrevBtn = document.getElementById('dataset-results-prev');
    const datasetResultsNextBtn = document.getElementById('dataset-results-next');
    
    if (datasetResultsPrevBtn) {
        datasetResultsPrevBtn.addEventListener('click', () => {
            scrollCards('dataset-results-cards', -1);
        });
    }
    
    if (datasetResultsNextBtn) {
        datasetResultsNextBtn.addEventListener('click', () => {
            scrollCards('dataset-results-cards', 1);
        });
    }
    
    // Handle window resize
    window.addEventListener('resize', () => {
        updateNavigationButtons('text2asset-cards');
        updateNavigationButtons('dataset-results-cards');
    });
});

