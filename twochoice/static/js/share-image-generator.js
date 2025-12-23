/**
 * Quick Share Image Generator
 * Generates beautiful poll result cards for social media sharing
 */

class ShareImageGenerator {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.init();
    }
    
    init() {
        this.attachEventListeners();
    }
    
    attachEventListeners() {
        document.addEventListener('click', (e) => {
            if (e.target.closest('.generate-share-image')) {
                e.preventDefault();
                const btn = e.target.closest('.generate-share-image');
                const postId = btn.dataset.postId;
                this.generateImage(postId);
            }
        });
    }
    
    async generateImage(postId) {
        try {
            // Get post data
            const response = await fetch(`/api/post/${postId}/share-data/`);
            const data = await response.json();
            
            if (!data.success) {
                throw new Error('Failed to fetch post data');
            }
            
            // Create canvas - Instagram Story format
            this.canvas = document.createElement('canvas');
            this.canvas.width = 1080;
            this.canvas.height = 1920; // Instagram Story format
            this.ctx = this.canvas.getContext('2d');
            
            // Draw the card
            this.drawCard(data);
            
            // Download the image
            this.downloadImage(postId);
            
        } catch (error) {
            console.error('Error generating share image:', error);
            if (typeof showToast === 'function') {
                showToast('Görsel oluşturulamadı', 'error');
            }
        }
    }
    
    drawCard(data) {
        const ctx = this.ctx;
        const width = this.canvas.width;
        const height = this.canvas.height;
        
        // Background gradient (vertical for story)
        const gradient = ctx.createLinearGradient(0, 0, 0, height);
        gradient.addColorStop(0, '#8B5CF6');
        gradient.addColorStop(0.5, '#A78BFA');
        gradient.addColorStop(1, '#EC4899');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, width, height);
        
        // White card (centered, story format)
        const cardPadding = 80;
        const cardX = cardPadding;
        const cardY = 200;
        const cardWidth = width - (cardPadding * 2);
        const cardHeight = height - 400;
        
        ctx.fillStyle = 'white';
        ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
        ctx.shadowBlur = 40;
        ctx.shadowOffsetY = 15;
        this.roundRect(ctx, cardX, cardY, cardWidth, cardHeight, 30);
        ctx.fill();
        ctx.shadowColor = 'transparent';
        
        // Logo/Brand at top
        ctx.fillStyle = 'white';
        ctx.font = 'bold 48px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('bilemedilema', width / 2, 120);
        
        // Title
        ctx.fillStyle = '#111827';
        ctx.font = 'bold 56px Arial';
        ctx.textAlign = 'center';
        const titleY = cardY + 100;
        this.wrapText(ctx, data.title, width / 2, titleY, cardWidth - 100, 70, 'center');
        
        // Poll options (centered)
        const optionsY = titleY + 200;
        const optionHeight = 140;
        const optionSpacing = 30;
        
        data.options.forEach((option, index) => {
            const y = optionsY + (index * (optionHeight + optionSpacing));
            
            // Option background
            ctx.fillStyle = '#F3F4F6';
            this.roundRect(ctx, cardX + 60, y, cardWidth - 120, optionHeight, 20);
            ctx.fill();
            
            // Progress bar
            const progressWidth = (cardWidth - 120) * (option.percentage / 100);
            const progressGradient = ctx.createLinearGradient(cardX + 60, y, cardX + 60 + progressWidth, y);
            progressGradient.addColorStop(0, '#8B5CF6');
            progressGradient.addColorStop(1, '#A78BFA');
            ctx.fillStyle = progressGradient;
            this.roundRect(ctx, cardX + 60, y, progressWidth, optionHeight, 20);
            ctx.fill();
            
            // Option text
            ctx.fillStyle = '#111827';
            ctx.font = 'bold 40px Arial';
            ctx.textAlign = 'left';
            ctx.fillText(option.text, cardX + 90, y + 55);
            
            // Percentage (large)
            ctx.fillStyle = '#8B5CF6';
            ctx.font = 'bold 52px Arial';
            ctx.textAlign = 'right';
            ctx.fillText(`${option.percentage}%`, cardX + cardWidth - 90, y + 60);
            
            // Vote count
            ctx.fillStyle = '#6B7280';
            ctx.font = '32px Arial';
            ctx.textAlign = 'left';
            ctx.fillText(`${option.votes} oy`, cardX + 90, y + 105);
            ctx.textAlign = 'left';
        });
        
        // Total votes at bottom of card
        const footerY = cardY + cardHeight - 60;
        ctx.fillStyle = '#6B7280';
        ctx.font = 'bold 36px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(`Toplam ${data.total_votes} oy`, width / 2, footerY);
        
        // URL at bottom of screen
        ctx.fillStyle = 'white';
        ctx.font = 'bold 40px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('bilemedilema.com', width / 2, height - 100);
        ctx.textAlign = 'left';
    }
    
    roundRect(ctx, x, y, width, height, radius) {
        ctx.beginPath();
        ctx.moveTo(x + radius, y);
        ctx.lineTo(x + width - radius, y);
        ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
        ctx.lineTo(x + width, y + height - radius);
        ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
        ctx.lineTo(x + radius, y + height);
        ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
        ctx.lineTo(x, y + radius);
        ctx.quadraticCurveTo(x, y, x + radius, y);
        ctx.closePath();
    }
    
    wrapText(ctx, text, x, y, maxWidth, lineHeight, align = 'left') {
        const words = text.split(' ');
        let line = '';
        let currentY = y;
        const originalAlign = ctx.textAlign;
        
        ctx.textAlign = align;
        
        for (let i = 0; i < words.length; i++) {
            const testLine = line + words[i] + ' ';
            const metrics = ctx.measureText(testLine);
            const testWidth = metrics.width;
            
            if (testWidth > maxWidth && i > 0) {
                ctx.fillText(line, x, currentY);
                line = words[i] + ' ';
                currentY += lineHeight;
            } else {
                line = testLine;
            }
        }
        ctx.fillText(line, x, currentY);
        ctx.textAlign = originalAlign;
    }
    
    downloadImage(postId) {
        const link = document.createElement('a');
        link.download = `poll-${postId}-share.png`;
        link.href = this.canvas.toDataURL('image/png');
        link.click();
        
        if (typeof showToast === 'function') {
            showToast('Görsel indirildi! 🎉', 'success');
        }
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    new ShareImageGenerator();
});
