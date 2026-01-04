var fullscreenElement = null;


function preventDefault(e) {
    e.preventDefault();
}


function stopPropagation(e) {
    e.stopPropagation();
}


function initWindow() {
    fullscreenElement = document.createElement('div');
    fullscreenElement.id = 'fullscreen';
    fullscreenElement.innerHTML = `
        <div id="window">
            <div id="close" onclick="closeWindow()">✕</div>
            <div id="content"></div>
        </div>
    `;
    document.body.appendChild(fullscreenElement);
    fullscreenElement.addEventListener('wheel', preventDefault);
    fullscreenElement.addEventListener('touchmove', preventDefault);
}


function openWindow(content) {
    let contentElement = fullscreenElement.querySelector('#content');
    contentElement.innerHTML = content;
    fullscreenElement.style.display = 'flex';
    setTimeout(() => {
        fullscreenElement.style.opacity = 1;
    }, 100);
    
    // if copntent height is greater than window height, enable scroll
    let contentHeight = contentElement.clientHeight;
    let innerHeight = contentElement.children[0].clientHeight;
    if (innerHeight > contentHeight) {
        contentElement.addEventListener('wheel', stopPropagation);
        contentElement.addEventListener('touchmove', stopPropagation);
    }
    else {
        contentElement.removeEventListener('wheel', stopPropagation);
        contentElement.removeEventListener('touchmove', stopPropagation);
    }
}


function closeWindow() {
    window_state = {};
    fullscreenElement.style.opacity = 0;
    setTimeout(() => {
        fullscreenElement.style.display = 'none';
    }, 250);
}


var window_state = {};


function hideTexture() {
    let appearanceButton = document.getElementById('appearance-button');
    let geometryButton = document.getElementById('geometry-button');
    appearanceButton.classList.remove('checked');
    geometryButton.classList.add('checked');
    let modelViewer = document.getElementById('modelviewer');
    if (modelViewer.model.materials[0].pbrMetallicRoughness.baseColorTexture.texture === null) return;
    window_state.textures = [];
    for (let i = 0; i < modelViewer.model.materials.length; i++) {
        window_state.textures.push(modelViewer.model.materials[i].pbrMetallicRoughness.baseColorTexture.texture);
    }
    window_state.exposure = modelViewer.exposure;
    modelViewer.environmentImage = '/assets/env_maps/gradient.jpg';
    for (let i = 0; i < modelViewer.model.materials.length; i++) {
        modelViewer.model.materials[i].pbrMetallicRoughness.baseColorTexture.setTexture(null);
    }
    modelViewer.exposure = 5;
}


function showTexture() {
    let appearanceButton = document.getElementById('appearance-button');
    let geometryButton = document.getElementById('geometry-button');
    appearanceButton.classList.add('checked');
    geometryButton.classList.remove('checked');
    let modelViewer = document.getElementById('modelviewer');
    if (modelViewer.model.materials[0].pbrMetallicRoughness.baseColorTexture.texture !== null) return;
    modelViewer.environmentImage = '/assets/env_maps/white.jpg';
    for (let i = 0; i < modelViewer.model.materials.length; i++) {
        modelViewer.model.materials[i].pbrMetallicRoughness.baseColorTexture.setTexture(window_state.textures[i]);
    }
    modelViewer.exposure = window_state.exposure;
}


function showAnnotations() {
    let showButton = document.getElementById('show-annotations-button');
    let hideButton = document.getElementById('hide-annotations-button');
    showButton.classList.add('checked');
    hideButton.classList.remove('checked');
    let modelViewer = document.getElementById('modelviewer');
    let annotations = modelViewer.querySelectorAll('button');
    for (let i = 0; i < annotations.length; i++) {
        annotations[i].style.display = 'block';
    }
    setTimeout(() => {
        for (let i = 0; i < annotations.length; i++) {
            annotations[i].style.opacity = 1;
        }
    }, 100);
}


function hideAnnotations() {
    let showButton = document.getElementById('show-annotations-button');
    let hideButton = document.getElementById('hide-annotations-button');
    showButton.classList.remove('checked');
    hideButton.classList.add('checked');
    let modelViewer = document.getElementById('modelviewer');
    let annotations = modelViewer.querySelectorAll('button');
    for (let i = 0; i < annotations.length; i++) {
        annotations[i].style.opacity = 0;
    }
    setTimeout(() => {
        for (let i = 0; i < annotations.length; i++) {
            annotations[i].style.display = 'none';
        }
    }, 200);
}


function lookAtAsset(index) {
    let modelViewer = document.getElementById('modelviewer');
    let viewAssetButton = document.getElementById('view-asset-button');
    let assetList = document.getElementById('asset-list');
    let hasChecked = assetList.children[index].classList.contains('checked');
    if (hasChecked) {
        for (let i = 0; i < window_state.assets.length; i++) {
            assetList.children[i].classList.remove('checked');
        }
        modelViewer.cameraTarget = 'none';
        viewAssetButton.classList.remove('enabled');
        viewAssetButton.classList.add('disabled');
        viewAssetButton.onclick = null;
    }
    else {
        for (let i = 0; i < window_state.assets.length; i++) {
            if (i === index) {
                assetList.children[i].classList.add('checked');
            }
            else {
                assetList.children[i].classList.remove('checked');
            }
        }
        modelViewer.cameraTarget = window_state.assets[index].position.map(p => p + 'm').join(' ');
        viewAssetButton.classList.remove('disabled');
        viewAssetButton.classList.add('enabled');
        viewAssetButton.onclick = () => viewAsset(index);
    }
}


function viewAsset(index) {
    hideAnnotations();
    showTexture();

    let modelViewer = document.getElementById('modelviewer');
    let viewAssetButton = document.getElementById('view-asset-button');
    let assetList = document.getElementById('asset-list');

    document.getElementById('scene-mode-desc').style.display = 'none';
    document.getElementById('asset-mode-desc').style.display = 'block';
    document.getElementById('prompt-group').style.display = 'block';
    document.querySelector('.modelviewer-panel-prompt').innerHTML = window_state.prompt_template(window_state.assets[index]);
    document.getElementById('annotations-group').style.display = 'none';

    if (!window_state.scene_src) {
        window_state.scene_src = modelViewer.src;
    }
    modelViewer.cameraTarget = 'none';
    modelViewer.src = window_state.assets[index].model;

    for (let i = 0; i < window_state.assets.length; i++) {
        if (i === index) {
            assetList.children[i].classList.add('checked');
        }
        else {
            assetList.children[i].classList.remove('checked');
        }
        assetList.children[i].onclick = () => viewAsset(i);
    }

    viewAssetButton.innerHTML = 'Back to Scene';
    viewAssetButton.onclick = backToScene;
}


function backToScene() {
    showTexture();

    let modelViewer = document.getElementById('modelviewer');
    let viewAssetButton = document.getElementById('view-asset-button');
    let assetList = document.getElementById('asset-list');

    document.getElementById('scene-mode-desc').style.display = 'block';
    document.getElementById('asset-mode-desc').style.display = 'none';
    document.getElementById('prompt-group').style.display = 'none';
    document.getElementById('annotations-group').style.display = 'block';

    modelViewer.cameraTarget = 'none';
    modelViewer.src = window_state.scene_src;
    window_state.scene_src = null;

    for (let i = 0; i < window_state.assets.length; i++) {
        assetList.children[i].classList.remove('checked');
        assetList.children[i].onclick = () => lookAtAsset(i);
    }

    viewAssetButton.innerHTML = 'View Asset';
    viewAssetButton.classList.remove('enabled');
    viewAssetButton.classList.add('disabled');
    viewAssetButton.onclick = null;
}


function downloadGLB() {
    let modelViewer = document.getElementById('modelviewer');
    window.open(modelViewer.src);
}


function asset_panel_template(prompt) {
    return `
        <div class="x-section-title small"><div class="x-gradient-font">Prompt</div></div>
        <div class="modelviewer-panel-prompt">
            ${prompt}
        </div>
        <div class="x-section-title small"><div class="x-gradient-font">Display Mode</div></div>
        <div class="x-left-align">
            <div id="appearance-button" class="modelviewer-panel-button small checked" onclick="showTexture()">Appearance</div>
            <div id="geometry-button" class="modelviewer-panel-button small" onclick="hideTexture()">Geometry</div>
        </div>
        <div class="x-flex-spacer"></div>
        <div class="x-row">
            <div id="download-button" class="modelviewer-panel-button enabled" onclick="downloadGLB()">Download GLB</div>
        </div>
    `;
}


function scene_panel_template(item) {
    html = `
        <div style="font-size: 28px; font-weight: 700; margin: 8px 0px 0px 4px">${item.title}</div>
        <div class="modelviewer-panel-desc" id="scene-mode-desc">
            <div>Click on an asset to focus the camera on it. Click again to unfocus.</div>
            <div>The meshes and textures are compressed for web viewing. Focus on specific assets and click <b>View Asset</b> to view individual assets.</div>
        </div>
        <div class="modelviewer-panel-desc" id="asset-mode-desc" style="display: none">
            <div>Click on an asset to view it in detail.</div>
            <div>Click on <b>Back to Scene</b> to return to the scene view.</div>
        </div>
        <div id="prompt-group" style="width: 100%; display: none">
            <div class="x-section-title small"><div class="x-gradient-font">Prompt</div></div>
            <div class="modelviewer-panel-prompt"></div>
        </div>
        <div class="x-section-title small"><div class="x-gradient-font">Display Mode</div></div>
        <div class="x-left-align">
            <div id="appearance-button" class="modelviewer-panel-button small checked" onclick="showTexture()">Appearance</div>
            <div id="geometry-button" class="modelviewer-panel-button small" onclick="hideTexture()">Geometry</div>
        </div>
        <div id="annotations-group" style="width: 100%;">
            <div class="x-section-title small"><div class="x-gradient-font">Annotations</div></div>
            <div class="x-left-align">
                <div id="show-annotations-button" class="modelviewer-panel-button small" onclick="showAnnotations()">Show</div>
                <div id="hide-annotations-button" class="modelviewer-panel-button small checked" onclick="hideAnnotations()">Hide</div>
            </div>
        </div>
        <div class="x-section-title small"><div class="x-gradient-font">Assets</div></div>
        <div class="x-left-align" id="asset-list" style="flex-wrap: wrap">`
    for (let i = 0; i < item.assets.length; i++) {
        html += `<div class="modelviewer-panel-button tiny" onclick="lookAtAsset(${i})">${item.assets[i].name}</div>`;
    }
    html += `</div>
        <div class="x-flex-spacer"></div>
        <div class="x-row" style="justify-content: space-around">
            <div id="view-asset-button" class="modelviewer-panel-button disabled" style="width: 125px">View Asset</div>
            <div id="download-button" class="modelviewer-panel-button enabled" style="width: 125px" onclick="downloadGLB()">Download GLB</div>
        </div>
    `;
    return html;
}


function modelviewer_window_template(item, panel, config) {
    let viewer_size = config && config.viewer_size || 500;
    let panel_size = config && config.panel_size || 300;
    let show_annotations = config && config.show_annotations || false;
    html = `<div class="x-row" style="align-items: stretch; flex-wrap: wrap; width: ${viewer_size + panel_size + 32}px; max-width: calc(100vw - 32px);">
                <div class="modelviewer-container" style="width: ${viewer_size}px;">
                    <model-viewer
                        id="modelviewer"
                        src="${item.model}"
                        camera-controls
                        tone-mapping="natural"
                        shadow-intensity="1"
                        environment-image="/assets/env_maps/white.jpg"
                        exposure="${item.exposure || 5}"
                        >`
    if (show_annotations) {
        window_state.assets = item.assets;
        window_state.prompt_template = item.prompt_template;
        for (let i = 0; i < item.assets.length; i++) {
            html += `<button slot="hotspot-${i}" data-position="${item.assets[i].position.join(' ')}">${item.assets[i].name}</button>`;
        }
    }
    html += `        </model-viewer>
                </div>
                <div class="modelviewer-panel" style="flex: 1 1 ${panel_size}px;">
                    ${panel}
                </div>
            </div>`;
    return html;
}
