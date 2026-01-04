window.HELP_IMPROVE_VIDEOJS = false;

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

$(document).ready(function () {
  // Check for click events on the navbar burger icon
  $(".navbar-burger").click(function () {
    // Toggle the "is-active" class on both the "navbar-burger" and the "navbar-menu"
    $(".navbar-burger").toggleClass("is-active");
    $(".navbar-menu").toggleClass("is-active");

  });

  var options = {
    slidesToScroll: 1,
    slidesToShow: 1,
    loop: true,
    infinite: true,
    autoplay: false,
    autoplaySpeed: 3000,
  }

  // Initialize all div with carousel class
  var carousels = bulmaCarousel.attach('.carousel', options);

  // Loop on each carousel initialized
  for (var i = 0; i < carousels.length; i++) {
    // Add listener to  event
    carousels[i].on('before:show', state => {
      console.log(state);
    });
  }


  // function syncFunction() {
  //   // 将你的代码放在这里


  //     // 获取所有的video-grid元素
  //     var videoGrids = document.querySelectorAll('.video-grid');

  //     // 遍历每个video-grid
  //     for (var i = 0; i < videoGrids.length; i++) {
  //         // 获取当前video-grid中的所有video元素
  //         var videos = videoGrids[i].querySelectorAll('video');
  //         console.log(videos.id);
  //         if (videos.length > 0) {
  //             // 获取第一个视频
  //             var firstVideo = videos[0];
  //             videos[0].currentTime=firstVideo.currentTime;
  //             // 当第一个视频的播放进度改变时，将所有其他视频的播放进度设置为与第一个视频相同
  //             // firstVideo.addEventListener('timeupdate', function() {
  //                 for (var j = 1; j < videos.length; j++) {
  //                     videos[j].currentTime = firstVideo.currentTime;
                      
  //                 }
  //                 // firstVideo.play();
  //             // });
  //         }
  //     }
  //   }
    // document.addEventListener('click', syncFunction);
  
  // Access to bulmaCarousel instance of an element
  var element = document.querySelector('#my-element');
  if (element && element.bulmaCarousel) {
    // bulmaCarousel instance is available as element.bulmaCarousel
    element.bulmaCarousel.on('before-show', function (state) {
      console.log(state);
    });
  }

  bulmaSlider.attach();


  $('.zoom-container').each(function() {
    const containerElement = $(this);
    zoomWidget = new ZoomWidget(containerElement);
  });

  $('.video-comparison').each(function () {
      const containerElement = $(this);
      comparisonWidget = new VideoComparison(containerElement);
  });

  $('.tabs-widget').each(function() {
    const containerElement = $(this);
    tabsWidget = new TabsWidget(containerElement);
  });

  //playPauseVideo();




// // 获取所有的video-grid
// var videoGrids = document.querySelectorAll('.video-grid');

// // 遍历每个video-grid
// for (var i = 0; i < videoGrids.length; i++) {
//     // 获取当前video-grid中的所有video元素
//     var videos = videoGrids[i].querySelectorAll('video');

//     // 创建一个函数来播放当前video-grid中的所有视频
//     function playAll() {
//         for (var j = 0; j < videos.length; j++) {
//             videos[j].play();
//         }
//     }

//     // 创建一个函数来停止当前video-grid中的所有视频
//     function pauseAll() {
//         for (var j = 0; j < videos.length; j++) {
//             videos[j].pause();
//         }
//     }

//     // 当任何一个视频开始播放时，调用playAll函数
//     // 当任何一个视频停止时，调用pauseAll函数
//     for (var j = 0; j < videos.length; j++) {
//         videos[j].addEventListener('play', playAll);
//         videos[j].addEventListener('pause', pauseAll);
//     }
// }




// window.addEventListener('DOMContentLoaded', (event) => {
//   // 获取所有的video-grid元素
//   var videoGrids = document.querySelectorAll('.video-grid');

//   // 创建一个函数来播放所有的视频
//   function playAll(videos) {
//       for (var i = 0; i < videos.length; i++) {
//           videos[i].play();
//       }
//   }

//   // 创建一个函数来暂停所有的视频
//   function pauseAll(videos) {
//       for (var i = 0; i < videos.length; i++) {
//           videos[i].pause();
//       }
//   }

//   // 创建一个Intersection Observer
//   var observer = new IntersectionObserver((entries, observer) => {
//       entries.forEach(entry => {
//           // 获取当前video-grid中的所有video元素
//           var videos = entry.target.querySelectorAll('video');

//           if (entry.isIntersecting) {
//               // 如果video-grid元素进入视口，播放所有的视频
//               playAll(videos);
//           } else {
//               // 如果video-grid元素离开视口，暂停所有的视频
//               pauseAll(videos);
//           }
//       });
//   });

//   // 遍历每个video-grid，将其添加到Intersection Observer中
  //   for (var i = 0; i < videoGrids.length; i++) {
  //       observer.observe(videoGrids[i]);
  //   }
  // });
  
  
  
});

// 初始化 Qualitative Comparisons 区域的选项切换
function initComparisonTabs() {
  const tabs = document.querySelectorAll('.comparison-tab');
  if (!tabs.length) return;

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetId = tab.getAttribute('data-target');
      // 切换 tab 激活状态
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      
      // 切换 panel 显示
      // 处理 video-comparison-wrapper 的特殊情况
      if (targetId === 'video-comparison-wrapper') {
        const wrapper = document.querySelector('.video-comparison-wrapper');
        const motionPanel = document.getElementById('motion-comparison-panel');
        if (wrapper) wrapper.style.display = 'block';
        if (motionPanel) motionPanel.classList.remove('active');
      } else {
        const wrapper = document.querySelector('.video-comparison-wrapper');
        const targetPanel = document.getElementById(targetId);
        if (wrapper) wrapper.style.display = 'none';
        if (targetPanel) {
          document.querySelectorAll('.comparison-panel').forEach(p => p.classList.remove('active'));
          targetPanel.classList.add('active');
        }
      }
    });
  });
}

// DOM 加载完成后初始化 comparison tabs
document.addEventListener('DOMContentLoaded', initComparisonTabs);

// 初始化单个三视频对比面板
function initSingleTripleVideoCompare(panelId) {
  const container = document.getElementById(`video-triple-compare-${panelId}`);
  if (!container) return;

  const canvas = document.getElementById(`video-triple-canvas-${panelId}`);
  const v1 = document.getElementById(`video-compare-${panelId}-1`);
  const v2 = document.getElementById(`video-compare-${panelId}-2`);
  const v3 = document.getElementById(`video-compare-${panelId}-3`);
  if (!canvas || !v1 || !v2 || !v3) return;

  const ctx = canvas.getContext('2d');
  const videos = [v1, v2, v3];

  // 默认分割位置（相对宽度百分比）
  // 左侧分割线初始位置：2/3W处
  // 右侧分割线初始位置：W处（即canvas右边界）
  let s1 = 1 / 10;
  let s2 = 9 / 10;
  const minPortion = 0;

  function resizeCanvas() {
    // 如果容器不可见，延迟执行
    const rect = container.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) {
      // 容器不可见，稍后重试
      setTimeout(resizeCanvas, 100);
      return;
    }
    const baseVideo = v1;
    const vw = baseVideo.videoWidth || 16;
    const vh = baseVideo.videoHeight || 9;
    const width = rect.width;
    const height = width * (vh / vw);
    canvas.width = width;
    canvas.height = height;
  }

  function drawFrame() {
    const width = canvas.width;
    const height = canvas.height;
    if (!width || !height) {
      requestAnimationFrame(drawFrame);
      return;
    }

    const x1 = s1 * width;
    const x2 = s2 * width;

    // 清空
    ctx.clearRect(0, 0, width, height);

    // 按用户要求进行水平裁剪：
    // 在每一帧，将 video1 的 [0, s1] 区间显示在 canvas 的 [0, s1]，
    // 将 video2 的 [s1, s2] 区间显示在 canvas 的 [s1, s2]，
    // 将 video3 的 [s2, 1] 区间显示在 canvas 的 [s2, 1]。

    // 左侧区域：来自视频1的 [0, s1]
    try {
      const vw1 = v1.videoWidth;
      const vh1 = v1.videoHeight;
      if (vw1 > 0 && vh1 > 0 && s1 > 0) {
        const srcW1 = vw1 * s1;
        ctx.drawImage(
          v1,
          0, 0,                      // 源起点 x=0
          srcW1, vh1,               // 源宽度 = vw1 * s1
          0, 0,                     // 目标起点
          x1, height                // 目标宽度 = x1
        );
      }
    } catch (e) {}

    // 中间区域：来自视频2的 [s1, s2]
    try {
      const vw2 = v2.videoWidth;
      const vh2 = v2.videoHeight;
      if (vw2 > 0 && vh2 > 0 && s2 > s1) {
        const srcX2 = vw2 * s1;
        const srcW2 = vw2 * (s2 - s1);
        ctx.drawImage(
          v2,
          srcX2, 0,                  // 源起点 x = vw2 * s1
          srcW2, vh2,               // 源宽度 = vw2 * (s2 - s1)
          x1, 0,                    // 目标起点 = canvas 的 [x1, 0]
          x2 - x1, height           // 目标宽度 = x2 - x1
        );
      }
    } catch (e) {}

    // 右侧区域：来自视频3的 [s2, 1]
    try {
      const vw3 = v3.videoWidth;
      const vh3 = v3.videoHeight;
      if (vw3 > 0 && vh3 > 0 && s2 < 1) {
        const srcX3 = vw3 * s2;
        const srcW3 = vw3 * (1 - s2);
        ctx.drawImage(
          v3,
          srcX3, 0,                 // 源起点 x = vw3 * s2
          srcW3, vh3,              // 源宽度 = vw3 * (1 - s2)
          x2, 0,                   // 目标起点 = canvas 的 [x2, 0]
          width - x2, height       // 目标宽度 = width - x2
        );
      }
    } catch (e) {}

    // 画两条分割线
    ctx.save();
    ctx.strokeStyle = 'rgba(255,255,255,0.9)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x1, 0);
    ctx.lineTo(x1, height);
    ctx.moveTo(x2, 0);
    ctx.lineTo(x2, height);
    ctx.stroke();
    ctx.restore();

    requestAnimationFrame(drawFrame);
  }

  // 拖动逻辑：用户必须点击分割线才能拖动
  let activeSplitter = null; // 's1' or 's2'
  const clickThreshold = 10; // 点击分割线的容差范围（像素）

  function onPointerDown(e) {
    // 用户点击时，检查是否点击在分割线上
    const rect = canvas.getBoundingClientRect();
    const clientX = e.clientX || (e.touches && e.touches[0].clientX);
    if (clientX == null) return;
    const x = clientX - rect.left;
    const width = rect.width;
    const x1cur = s1 * width;
    const x2cur = s2 * width;

    // 检查点击位置是否在分割线附近
    if (Math.abs(x - x1cur) < clickThreshold) {
      activeSplitter = 's1';
      e.preventDefault(); // 防止默认行为
    } else if (Math.abs(x - x2cur) < clickThreshold) {
      activeSplitter = 's2';
      e.preventDefault(); // 防止默认行为
    } else {
      activeSplitter = null;
    }
  }

  function onPointerMove(e) {
    // 只有在已激活分割线的情况下才更新位置
    if (!activeSplitter) return;

    const rect = canvas.getBoundingClientRect();
    const clientX = e.clientX || (e.touches && e.touches[0].clientX);
    if (clientX == null) return;
    
    e.preventDefault();
    const x = clientX - rect.left;
    let ratio = x / rect.width;
    ratio = Math.min(Math.max(ratio, 0), 1);

    if (activeSplitter === 's1') {
      // 左侧分割线：从 canvas left (0) 到右侧分割线 (s2)，但需保持最小间距
      s1 = Math.max(Math.min(ratio, s2 - minPortion), 0);
    } else if (activeSplitter === 's2') {
      // 右侧分割线：从左侧分割线 (s1) 到 canvas right (1.0)，但需保持最小间距
      s2 = Math.min(Math.max(ratio, s1 + minPortion), 1.0);
    }
  }

  function onPointerUp() {
    // 松开鼠标时，取消激活状态
    activeSplitter = null;
  }

  // 检测鼠标是否在分割线附近，改变光标样式
  function onCanvasMouseMove(e) {
    if (activeSplitter) {
      // 如果正在拖动，保持手指光标
      canvas.style.cursor = 'pointer';
      return;
    }

    const rect = canvas.getBoundingClientRect();
    const clientX = e.clientX;
    if (clientX == null) return;
    const x = clientX - rect.left;
    const width = rect.width;
    const x1cur = s1 * width;
    const x2cur = s2 * width;

    // 检查鼠标是否在分割线附近
    if (Math.abs(x - x1cur) < clickThreshold || Math.abs(x - x2cur) < clickThreshold) {
      canvas.style.cursor = 'pointer';
    } else {
      canvas.style.cursor = 'default';
    }
  }

  // 鼠标离开 canvas 时恢复默认光标
  function onCanvasMouseLeave() {
    if (!activeSplitter) {
      canvas.style.cursor = 'default';
    }
  }

  canvas.addEventListener('mousedown', onPointerDown);
  canvas.addEventListener('mousemove', onCanvasMouseMove);
  canvas.addEventListener('mouseleave', onCanvasMouseLeave);
  window.addEventListener('mousemove', onPointerMove);
  window.addEventListener('mouseup', onPointerUp);

  canvas.addEventListener('touchstart', onPointerDown, { passive: false });
  window.addEventListener('touchmove', onPointerMove, { passive: false });
  window.addEventListener('touchend', onPointerUp);
  window.addEventListener('touchcancel', onPointerUp);

  // 同步播放三个视频（以第一个为主时钟）
  function syncFromMaster() {
    const t = v1.currentTime;
    [v2, v3].forEach(v => {
      if (Math.abs(v.currentTime - t) > 0.03) {
        try {
          v.currentTime = t;
        } catch (e) {}
      }
    });
  }

  v1.addEventListener('timeupdate', syncFromMaster);

  // 确保视频一直循环播放，移除点击暂停功能
  // 监听视频结束事件，自动重新播放（确保循环）
  videos.forEach(v => {
    v.addEventListener('ended', () => {
      v.currentTime = 0;
      v.play().catch(() => {});
    });
  });

  function startWhenReady() {
    if (v1.readyState >= 2) {
      resizeCanvas();
      videos.forEach(v => {
        v.play().catch(() => {});
      });
      requestAnimationFrame(drawFrame);
    } else {
      v1.addEventListener('loadedmetadata', () => {
        resizeCanvas();
        videos.forEach(v => {
          v.play().catch(() => {});
        });
        requestAnimationFrame(drawFrame);
      }, { once: true });
    }
  }

  window.addEventListener('resize', resizeCanvas);
  startWhenReady();
}

// 初始化所有三视频对比面板
function initAllTripleVideoCompare() {
  // 初始化每个面板
  initSingleTripleVideoCompare('1');
  initSingleTripleVideoCompare('2');
  
  // 初始化 navigation 按钮
  initVideoComparisonNavigation();
}

// 滚动视频比较面板
function scrollVideoComparisonPanels(direction) {
  const wrapper = document.getElementById('video-comparison-panels-wrapper');
  if (!wrapper) return;
  
  const panel = wrapper.querySelector('.comparison-panel');
  if (!panel) return;
  
  const scrollAmount = panel.offsetWidth;
  
  wrapper.scrollBy({
    left: direction * scrollAmount,
    behavior: 'smooth'
  });
  
  // 更新导航按钮状态
  setTimeout(() => {
    updateVideoComparisonNavigation();
  }, 300);
}

// 更新视频比较导航按钮状态
function updateVideoComparisonNavigation() {
  const wrapper = document.getElementById('video-comparison-panels-wrapper');
  const prevBtn = document.getElementById('video-comparison-prev');
  const nextBtn = document.getElementById('video-comparison-next');
  
  if (!wrapper || !prevBtn || !nextBtn) return;
  
  const scrollLeft = wrapper.scrollLeft;
  const scrollWidth = wrapper.scrollWidth;
  const clientWidth = wrapper.clientWidth;
  
  // 启用/禁用 prev 按钮
  if (scrollLeft <= 1) {
    prevBtn.classList.add('disabled');
  } else {
    prevBtn.classList.remove('disabled');
  }
  
  // 启用/禁用 next 按钮
  if (scrollLeft + clientWidth >= scrollWidth - 1) {
    nextBtn.classList.add('disabled');
  } else {
    nextBtn.classList.remove('disabled');
  }
}

// 初始化视频比较的 navigation 按钮
function initVideoComparisonNavigation() {
  const prevBtn = document.getElementById('video-comparison-prev');
  const nextBtn = document.getElementById('video-comparison-next');
  const wrapper = document.getElementById('video-comparison-panels-wrapper');
  
  if (!prevBtn || !nextBtn || !wrapper) return;

  // 添加点击事件监听器
  prevBtn.addEventListener('click', () => {
    scrollVideoComparisonPanels(-1);
  });

  nextBtn.addEventListener('click', () => {
    scrollVideoComparisonPanels(1);
  });
  
  // 添加滚动事件监听器以更新按钮状态
  wrapper.addEventListener('scroll', () => {
    updateVideoComparisonNavigation();
  });
  
  // 处理窗口大小变化
  window.addEventListener('resize', () => {
    updateVideoComparisonNavigation();
  });

  // 初始化状态
  updateVideoComparisonNavigation();
}

// DOM 加载完成后初始化所有三视频对比
document.addEventListener('DOMContentLoaded', initAllTripleVideoCompare);


class ZoomWidget {
  constructor(container) {
    this.container = container;
    this.canvas = container.find('canvas');
    this.context = this.canvas[0].getContext("2d");
    this.image = new Image();
    this.image.src = this.container.data('gt-img-src');
    this.zoomFactor = container.data('zoom-factor');
    this.defaultU = this.container.data('default-u');
    this.defaultV = this.container.data('default-v');
    let self = this;

    this.image.onload = function(){
      self.handleZoom(null, null, self.defaultU, self.defaultV);
    }

    this.canvas.mousemove(function(e) {
      let rect = self.canvas[0].getBoundingClientRect();
      let x = e.clientX - rect.left;
      let y = e.clientY - rect.top;
      self.handleZoom(x, y);
    });
    this.canvas.on('resize', function(e) {
      self.handleZoom(null, null, self.defaultU, self.defaultV);
    })
    this.canvas.mouseleave(function(e) {
      self.handleZoom(null, null, self.defaultU, self.defaultV);
    });
  }

  handleZoom(x = null, y = null, u = null, v = null) {
    const containerElement = this.container;
    const zoomLensElements = containerElement.find('.zoom-lens');
    this.context.clearRect(0, 0, this.canvas[0].width, this.canvas[0].height);

    const imageWidth = this.canvas.parent().width();
    const imageHeight = imageWidth / this.image.width * this.image.height;
    this.canvas[0].width = imageWidth;
    this.canvas[0].height = imageHeight;
    this.context.drawImage(this.image, 0, 0, imageWidth, imageHeight);
  
    if (u && v) {
      x = u * this.canvas.width();
      y = v * this.canvas.height();
    } else {
      u = x / this.canvas.width()
      v = y / this.canvas.height()
    }
    console.log('u v', u, v)
    let naturalHeight = this.image.naturalHeight;
    let naturalWidth = this.image.naturalWidth;
    let zoomFullWidth = naturalWidth * this.zoomFactor;
    let zoomFullHeight = naturalHeight * this.zoomFactor;
  
    zoomLensElements.each(function () {
      let el = $(this);
      let zoomWindowWidth = el.width();
      let zoomWindowHeight = el.height();
      let maxZoomX = zoomFullWidth - zoomWindowWidth - 1;
      let maxZoomY = zoomFullHeight - zoomWindowHeight - 1;
      let zoomX = clamp(zoomFullWidth * u - zoomWindowWidth / 2, 0, maxZoomX);
      let zoomY = clamp(zoomFullHeight * v - zoomWindowHeight / 2, 0, maxZoomY);
  
      el.css('background-size',
        zoomFullWidth + 'px ' + zoomFullHeight + 'px');
      el.css('background-position',
        (-zoomX) + 'px ' + (-zoomY) + 'px');
    })
  
    let zoomWindowWidth = $(zoomLensElements[0]).width();
    let zoomWindowHeight = $(zoomLensElements[0]).height();
    let zoomCursorWidth = zoomWindowWidth / zoomFullWidth * this.canvas.width();
    let zoomCursorHeight = zoomWindowHeight / zoomFullHeight * this.canvas.height();
    this.context.strokeStyle = '#DB4437';
    this.context.lineWidth = 2;
    this.context.strokeRect(
      x - zoomCursorWidth / 2, y - zoomCursorHeight / 2, zoomCursorWidth, zoomCursorHeight);
  }
}


class TabsWidget {
  constructor(container) {
    this.container = container;
    this.activeIndex = 0;
    this.listItems = container.children('.tabs').children('ul').children('li');
    let self = this;
    this.listItems.click(function (e) {
      let index = $(this).index();
      self.update($(this), index);
    })

    this.update(this.listItems[this.activeIndex], this.activeIndex);
  }

  update(element, targetIndex) {
    this.activeIndex = targetIndex;
    const tabs = this.container.children('.tabs');
    const tabsContent = this.container.children('.tabs-content');
    this.listItems.each(function () {
      if ($(this).index() == targetIndex) {
        $(this).addClass('is-active');
      } else {
        $(this).removeClass('is-active');
      }
    });
    tabsContent.children().each(function () {
      if ($(this).index() == targetIndex) {
        $(this).show();
        $(this).find('*').each(function () {
          if ($(this).is(':visible')) {
            $(this).trigger('tab:show');
          }
        })
      } else {
        $(this).hide();
        $(this).find('*').trigger('tab:hide');
      }
    });
  }
}

function clamp(number, min, max) {
  return Math.min(Math.max(number, min), max);
}


// From: https://benfrain.com/automatically-play-and-pause-video-as-it-enters-and-leaves-the-viewport-screen/
function playPauseVideo() {
  let videos = document.querySelectorAll("video");
  videos.forEach((video) => {
      // We can only control playback without insteraction if video is mute
      video.muted = true;
      // Play is a promise so we need to check we have it
      let playPromise = video.play();
      if (playPromise !== undefined) {
          playPromise.then((_) => {
              let observer = new IntersectionObserver(
                  (entries) => {
                      entries.forEach((entry) => {
                          if (
                              entry.intersectionRatio !== 1 &&
                              !video.paused
                          ) {
                              video.pause();
                          } else if (video.paused) {
                              video.play();
                          }
                      });
                  },
                  { threshold: 0.5 }
              );
              observer.observe(video);
          });
      }
  });
}