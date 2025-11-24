
// 作品集专用交互
document.addEventListener('DOMContentLoaded', function() {
    // 项目详情模态框
    const detailButtons = document.querySelectorAll('.view-details');
    detailButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            alert('项目详情功能待实现');
        });
    });
    
    // 联系表单验证
    const contactForm = document.querySelector('.contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            alert('消息发送成功！');
            this.reset();
        });
    }
});
            