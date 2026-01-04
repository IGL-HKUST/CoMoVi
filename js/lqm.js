window.addEventListener('DOMContentLoaded', (event) => {
    // 获取所有的video-grid元素
    var videoGrids = document.querySelectorAll('.video-grid');

    // 遍历每个video-grid
    for (var i = 0; i < videoGrids.length; i++) {
        // 获取当前video-grid中的所有video元素
        var videos = videoGrids[i].querySelectorAll('video');

        if (videos.length > 0) {
            // 获取第一个视频
            var firstVideo = videos[0];

            // 当第一个视频的播放进度改变时，将所有其他视频的播放进度设置为与第一个视频相同
            // firstVideo.addEventListener('timeupdate', function() {
                for (var j = 1; j < videos.length; j++) {
                    videos[j].currentTime = firstVideo.currentTime;
                }
            // });
        }
    }
});