/**
 * Story paylaşım butonu için JavaScript
 * Story kartı oluşturur ve sosyal medya seçenekleri sunar
 */

document.addEventListener('DOMContentLoaded', function() {
    const storyShareBtns = document.querySelectorAll('.story-share-btn');
    
    storyShareBtns.forEach(btn => {
        btn.addEventListener('click', async function() {
            const postId = this.dataset.postId;
            const storyCardUrl = `/post/${postId}/story-card/`;
            
            // Loading state
            const originalHTML = this.innerHTML;
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Hazırlanıyor...';
            
            try {
                // Story kartını fetch et
                const response = await fetch(storyCardUrl);
                if (!response.ok) throw new Error('Story kartı oluşturulamadı');
                
                const blob = await response.blob();
                const blobUrl = URL.createObjectURL(blob);
                
                // Modal göster
                showStoryShareModal(blobUrl, postId);
                
            } catch (error) {
                console.error('Story share error:', error);
                showToast('Story kartı oluşturulamadı. Lütfen tekrar deneyin.');
            } finally {
                this.disabled = false;
                this.innerHTML = originalHTML;
            }
        });
    });
});

function showStoryShareModal(imageUrl, postId) {
    // Modal oluştur
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 modal-backdrop';
    const postUrl = window.location.origin + '/post/' + postId + '/';
    
    modal.innerHTML = `
        <div class="bg-white rounded-2xl max-w-lg w-full p-6 relative modal-content">
            <button class="absolute top-4 right-4 text-gray-500 hover:text-gray-700" onclick="this.closest('.fixed').remove()">
                <i class="fas fa-times text-xl"></i>
            </button>
            
            <h3 class="text-2xl font-bold text-gray-900 mb-4">📤 Story'de Paylaş</h3>
            
            <div class="mb-6">
                <img src="${imageUrl}" alt="Story Card" class="w-full rounded-xl border border-gray-200 shadow-lg">
            </div>
            
            <div class="space-y-3">
                <p class="text-sm text-gray-600 mb-4">Paylaşmak istediğin platformu seç:</p>
                
                <!-- Sosyal Medya Butonları -->
                <div class="grid grid-cols-4 gap-2 mb-4">
                    <button onclick="shareToInstagram('${imageUrl}')" 
                            class="flex flex-col items-center justify-center gap-2 p-4 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white rounded-xl transition duration-200"
                            title="Instagram'da Paylaş">
                        <i class="fab fa-instagram text-2xl"></i>
                        <span class="text-xs">Instagram</span>
                    </button>
                    
                    <button onclick="shareToTwitter(${postId})" 
                            class="flex flex-col items-center justify-center gap-2 p-4 bg-[#1DA1F2] hover:bg-[#1a8cd8] text-white rounded-xl transition duration-200"
                            title="Twitter'da Paylaş">
                        <i class="fab fa-twitter text-2xl"></i>
                        <span class="text-xs">Twitter</span>
                    </button>
                    
                    <button onclick="shareToWhatsApp('${imageUrl}', ${postId})" 
                            class="flex flex-col items-center justify-center gap-2 p-4 bg-[#25D366] hover:bg-[#20bd5a] text-white rounded-xl transition duration-200"
                            title="WhatsApp'ta Paylaş">
                        <i class="fab fa-whatsapp text-2xl"></i>
                        <span class="text-xs">WhatsApp</span>
                    </button>
                    
                    <button onclick="copyLink('${postUrl}')" 
                            class="flex flex-col items-center justify-center gap-2 p-4 bg-gray-600 hover:bg-gray-700 text-white rounded-xl transition duration-200"
                            title="Linki Kopyala">
                        <i class="fas fa-link text-2xl"></i>
                        <span class="text-xs">Link</span>
                    </button>
                </div>
                
                <button onclick="downloadStoryCard('${imageUrl}')" 
                        class="w-full flex items-center justify-center gap-3 px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-xl font-semibold transition duration-200">
                    <i class="fas fa-download text-xl"></i>
                    Görseli İndir
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Dışarı tıklayınca kapat
    modal.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal-backdrop')) {
            modal.remove();
        }
    });
}

function copyLink(url) {
    navigator.clipboard.writeText(url).then(() => {
        showToast('Link kopyalandı! 📋');
    }).catch(() => {
        showToast('Link kopyalanamadı');
    });
}

async function shareToInstagram(imageUrl) {
    // Görseli indir ve kullanıcıya Instagram'a manuel yüklemesi için bildir
    downloadStoryCard(imageUrl);
    
    // Instagram web'e yönlendir (mobilde Instagram app açılır)
    setTimeout(() => {
        const instagramUrl = 'https://www.instagram.com/';
        window.open(instagramUrl, '_blank');
        showToast('Görsel indirildi! Instagram\'da Story olarak paylaşabilirsin.');
    }, 500);
}

function shareToWhatsApp(imageUrl, postId) {
    const postUrl = window.location.origin + '/post/' + postId + '/';
    const text = encodeURIComponent(`Bu ankete sen olsan ne seçerdin? 🤔\n\n${postUrl}`);
    
    // WhatsApp'a direkt yönlendir
    window.open(`https://wa.me/?text=${text}`, '_blank');
    showToast('WhatsApp\'a yönlendiriliyorsun...');
}

function shareToTwitter(postId) {
    const postUrl = window.location.origin + '/post/' + postId + '/';
    const text = encodeURIComponent('Bu ankete sen olsan ne seçerdin? 🤔');
    const url = encodeURIComponent(postUrl);
    
    window.open(`https://twitter.com/intent/tweet?text=${text}&url=${url}&hashtags=bilemedilema`, '_blank');
}

function shareToFacebook(postId) {
    const postUrl = window.location.origin + '/post/' + postId + '/';
    const url = encodeURIComponent(postUrl);
    
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${url}`, '_blank');
}

function downloadStoryCard(imageUrl) {
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = 'bilemedilema-story.png';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showToast('Görsel indirildi!');
}

function showToast(message) {
    // Toast notification (basit versiyon)
    const toast = document.createElement('div');
    toast.className = 'fixed bottom-4 right-4 bg-gray-900 text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-fade-in';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}
