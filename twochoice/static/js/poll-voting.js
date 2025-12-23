function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showToast(message, type = 'error') {
    const toast = document.createElement('div');
    toast.className = `fixed top-4 right-4 z-50 px-6 py-3 rounded-lg shadow-lg text-white font-medium transition-all duration-300 transform translate-x-0 ${
        type === 'success' ? 'bg-green-600' : 'bg-red-600'
    }`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.transform = 'translateX(400px)';
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function setDisabledForNode(node, disabled) {
    if (!node) return;
    if (disabled) {
        node.setAttribute('disabled', 'disabled');
        node.classList.add('opacity-50', 'cursor-not-allowed');
    } else {
        node.removeAttribute('disabled');
        node.classList.remove('opacity-50', 'cursor-not-allowed');
    }
}

function setLoadingState(button, isLoading) {
    if (!button) return;
    
    if (isLoading) {
        button.setAttribute('data-original-text', button.textContent);
        button.innerHTML = '<span class="inline-flex items-center gap-2"><svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>Yükleniyor...</span>';
        button.setAttribute('disabled', 'disabled');
        button.classList.add('opacity-75', 'cursor-wait');
    } else {
        const originalText = button.getAttribute('data-original-text');
        if (originalText) {
            button.textContent = originalText;
            button.removeAttribute('data-original-text');
        }
        button.removeAttribute('disabled');
        button.classList.remove('opacity-75', 'cursor-wait');
    }
}

async function sendVote(voteUrl, optionIds) {
    const csrftoken = getCookie('csrftoken');
    if (!csrftoken) {
        throw new Error('CSRF token bulunamadı. Lütfen sayfayı yenileyin.');
    }

    const formData = new FormData();
    optionIds.forEach(id => formData.append('options', id));

    const response = await fetch(voteUrl, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
        },
        body: formData,
    });

    const data = await response.json();
    
    if (!response.ok) {
        if (response.status === 429) {
            throw new Error('Çok hızlı işlem yapıyorsunuz. Lütfen bekleyin.');
        } else if (response.status === 403) {
            throw new Error(data.error || 'Bu işlem için yetkiniz yok.');
        } else if (response.status === 400) {
            throw new Error(data.error || 'Geçersiz istek.');
        } else {
            throw new Error(data.error || 'Bir hata oluştu. Lütfen tekrar deneyin.');
        }
    }

    // Trigger vote-success event for animations
    document.dispatchEvent(new CustomEvent('vote-success', { detail: { optionIds, data } }));
    
    return { response, data };
}

function updatePollUI(postId, results) {
    if (!results || !Array.isArray(results)) return;

    const totalVotes = results.reduce((sum, r) => sum + (r.vote_count || 0), 0);
    
    const totalVotesEl = document.querySelector(`.js-total-votes[data-post-id="${postId}"]`);
    if (totalVotesEl) {
        totalVotesEl.textContent = `Toplam ${totalVotes} oy`;
    }

    results.forEach(result => {
        const optionId = result.option_id;
        const voteCount = result.vote_count || 0;
        const percentage = result.percentage || 0;

        const optionCard = document.querySelector(`[data-post-id="${postId}"][data-option-id="${optionId}"]`);
        if (!optionCard) return;

        const percentEl = optionCard.querySelector('.js-option-percent');
        if (percentEl) {
            percentEl.textContent = `${Math.round(percentage)}%`;
        }

        const votesEl = optionCard.querySelector('.js-option-votes');
        if (votesEl) {
            votesEl.textContent = `${voteCount} oy`;
        }

        const barEl = optionCard.querySelector('.js-option-bar');
        if (barEl) {
            barEl.style.width = `${Math.round(percentage)}%`;
        }
    });
}

function initPollVoting(options = {}) {
    const {
        isAuthenticated = false,
        loginUrl = '/login/',
        containerSelector = 'body',
    } = options;

    const container = document.querySelector(containerSelector);
    if (!container) return;

    const selectedByPost = new Map();

    container.addEventListener('click', async (e) => {
        const optionButton = e.target.closest('.poll-option-card, .poll-option');
        if (!optionButton) return;

        if (!isAuthenticated) {
            window.location.href = loginUrl;
            return;
        }

        const postId = optionButton.dataset.postId;
        const optionId = optionButton.dataset.optionId;
        const voteUrl = optionButton.dataset.voteUrl;
        const allowMultiple = (optionButton.dataset.allowMultiple === 'true');

        if (!postId || !optionId || !voteUrl) return;

        if (allowMultiple) {
            let selected = selectedByPost.get(postId);
            if (!selected) {
                selected = new Set();
                selectedByPost.set(postId, selected);
            }

            if (selected.has(optionId)) {
                selected.delete(optionId);
                optionButton.classList.remove('poll-option-selected', 'ring-2', 'ring-[#666A73]');
                optionButton.setAttribute('aria-pressed', 'false');
            } else {
                selected.add(optionId);
                optionButton.classList.add('poll-option-selected', 'ring-2', 'ring-[#666A73]');
                optionButton.setAttribute('aria-pressed', 'true');
            }
            return;
        }

        const postOptions = container.querySelectorAll(`[data-post-id="${postId}"].poll-option-card, [data-post-id="${postId}"].poll-option`);
        postOptions.forEach(b => setDisabledForNode(b, true));

        try {
            const { response, data } = await sendVote(voteUrl, [optionId]);
            if (response.ok && data.success) {
                updatePollUI(postId, data.results);
                showToast('Oyunuz kaydedildi!', 'success');
            } else {
                throw new Error(data.error || 'Bir hata oluştu.');
            }
        } catch (error) {
            showToast(error.message);
        } finally {
            postOptions.forEach(b => setDisabledForNode(b, false));
        }
    });

    container.addEventListener('click', async (e) => {
        const submitButton = e.target.closest('.js-home-multi-submit, .js-profile-multi-submit');
        if (!submitButton) return;

        if (!isAuthenticated) {
            window.location.href = loginUrl;
            return;
        }

        const postId = submitButton.dataset.postId;
        const voteUrl = submitButton.dataset.voteUrl;

        if (!postId || !voteUrl) return;

        const selected = selectedByPost.get(postId);
        if (!selected || selected.size === 0) {
            showToast('Lütfen en az bir seçenek seçin.');
            return;
        }

        setLoadingState(submitButton, true);
        const postOptions = container.querySelectorAll(`[data-post-id="${postId}"].poll-option-card, [data-post-id="${postId}"].poll-option`);
        postOptions.forEach(b => setDisabledForNode(b, true));

        try {
            const { response, data } = await sendVote(voteUrl, Array.from(selected));
            if (response.ok && data.success) {
                updatePollUI(postId, data.results);
                selectedByPost.delete(postId);
                postOptions.forEach(opt => {
                    opt.classList.remove('poll-option-selected', 'ring-2', 'ring-[#666A73]');
                    opt.setAttribute('aria-pressed', 'false');
                });
                showToast('Oylarınız kaydedildi!', 'success');
            } else {
                throw new Error(data.error || 'Bir hata oluştu.');
            }
        } catch (error) {
            showToast(error.message);
        } finally {
            setLoadingState(submitButton, false);
            postOptions.forEach(b => setDisabledForNode(b, false));
        }
    });
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        getCookie,
        showToast,
        setDisabledForNode,
        setLoadingState,
        sendVote,
        updatePollUI,
        initPollVoting,
    };
}
