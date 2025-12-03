// 主JavaScript文件

// 自动隐藏消息提示
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
});

// 工具函数：格式化数字
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// 工具函数：获取稀有度颜色
function getRarityColor(rarity) {
    const colors = {
        'N': '#8E8E8E',
        'R': '#5C9BD1',
        'SR': '#C77DD8',
        'SSR': '#FFD700',
        'UR': '#FF1493'
    };
    return colors[rarity] || '#999';
}

console.log('🎴 成人卡牌游戏已加载');
