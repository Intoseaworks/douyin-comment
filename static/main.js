let currentMode = 'video';
let currentCursor = 0;
let currentAwemeId = null;
let hasMore = false;
let isLoading = false;
let allComments = [];

// 模式切换
document.querySelectorAll('.mode-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentMode = btn.dataset.mode;
        
        document.querySelectorAll('.input-group').forEach(el => {
            el.classList.toggle('hidden', !el.classList.contains(currentMode + '-mode'));
        });
        
        resetState();
    });
});

// 加载用户主页视频
function loadProfile() {
    const profileUrl = document.getElementById('profileUrl').value;
    fetch('/get_user_videos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile_url: profileUrl })
    })
    .then(handleResponse)
    .then(data => {
        const select = document.getElementById('videoSelect');
        select.innerHTML = '<option value="">请选择视频</option>';
        data.videos.forEach(video => {
            const option = document.createElement('option');
            option.value = video.aweme_id;
            option.textContent = video.desc.substring(0, 50) + (video.desc.length > 50 ? '...' : '');
            select.appendChild(option);
        });
    });
}

// 加载评论
function loadComments(sourceAwemeId = null) {
    if (isLoading) return;
    
    const awemeId = sourceAwemeId || extractAwemeId();
    if (!awemeId) return alert('请输入有效链接');
    
    isLoading = true;
    toggleLoading(true);
    
    fetch('/get_comments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            [currentMode === 'video' ? 'video_url' : 'aweme_id']: awemeId,
            cursor: currentCursor
        })
    })
    .then(handleResponse)
    .then(data => {
        renderComments(data.comments);
        allComments = [...allComments, ...data.comments];
        hasMore = data.has_more;
        currentCursor = data.next_cursor;
    })
    .finally(() => {
        isLoading = false;
        toggleLoading(false);
    });
}

// 导出数据
function exportData() {
    if (allComments.length === 0) return alert('没有可导出的数据');
    
    fetch('/export_csv', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: allComments })
    })
    .then(res => res.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'douyin_comments.csv';
        a.click();
        window.URL.revokeObjectURL(url);
    });
}

// 辅助函数
function extractAwemeId() {
    const input = currentMode === 'video' ? 
        document.getElementById('videoUrl') : 
        document.getElementById('videoSelect');
    return currentMode === 'video' ? 
        input.value.match(/\/video\/(\d+)/)?.[1] : 
        input.value;
}

function renderComments(comments) {
    const container = document.getElementById('commentContainer');
    comments.forEach(comment => {
        const card = document.createElement('div');
        card.className = 'comment-card';
        card.innerHTML = `
            <div class="user-header">
                <img src="${comment.avatar}" class="user-avatar">
                <div>
                    <a href="https://www.douyin.com/user/${comment.sec_uid}" 
                       target="_blank" class="user-link">${comment.username}</a>
                    <div class="meta-info">
                        <span>${comment.region}</span>
                        <span>❤ ${comment.digg_count}</span>
                        <span>${new Date(comment.time * 1000).toLocaleString()}</span>
                    </div>
                </div>
            </div>
            <p class="comment-content">${comment.content}</p>
        `;
        container.appendChild(card);
    });
}

// 初始化滚动加载
window.addEventListener('scroll', () => {
    if (isLoading || !hasMore) return;
    
    const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
    if (scrollTop + clientHeight >= scrollHeight - 100) {
        loadComments();
    }
});