var selection_panel_objects = {};


function make_selection_panel(selection_panel_id, thumbnail_template, item_template, items) {
    selection_panel_objects[selection_panel_id] = {};
    selection_panel_objects[selection_panel_id].thumbnail_template = thumbnail_template;
    selection_panel_objects[selection_panel_id].item_template = item_template;
    selection_panel_objects[selection_panel_id].items = items;
    selection_panel_objects[selection_panel_id].current_item = 0;
    selection_panel_init(selection_panel_id);
}


function selection_panel_init(selection_panel_id) {
    let selection_panel = document.getElementById(selection_panel_id);
    let html = "";
    html += '<div class="x-selection-panel-thumbnails">'
    for (let i = 0; i < selection_panel_objects[selection_panel_id].items.length; i++) {
        html += `<div class="x-selection-panel-thumbnail" onclick="selection_panel_page('${selection_panel_id}', ${i})">
            <div class="x-selection-panel-thumbnail-inner">
                ${selection_panel_objects[selection_panel_id].thumbnail_template(selection_panel_objects[selection_panel_id].items[i])}
            </div>
        </div>`;
    }
    html += '</div>';
    html += '<div class="x-selection_panel-content"></div>';
    selection_panel.innerHTML = html;
    selection_panel_render(selection_panel_id);
}


function selection_panel_render(selection_panel_id) {
    let selection_panel = document.getElementById(selection_panel_id);
    let thumbnails = selection_panel.querySelector('.x-selection-panel-thumbnails');
    let content = selection_panel.querySelector('.x-selection_panel-content');
    let current_item = selection_panel_objects[selection_panel_id].current_item;
    for (let i = 0; i < thumbnails.children.length; i++) {
        if (i === current_item) {
            thumbnails.children[i].classList.add('x-selection-panel-thumbnail-active');
        } else {
            thumbnails.children[i].classList.remove('x-selection-panel-thumbnail-active');
        }
    }
    content.innerHTML = selection_panel_objects[selection_panel_id].item_template(
        selection_panel_objects[selection_panel_id].items[current_item]
    );
}


function selection_panel_page(selection_panel_id, page) {
    selection_panel_objects[selection_panel_id].current_item = page;
    selection_panel_render(selection_panel_id);
}
