window.onload = function() {
    initWindow();
    make_carousel('results-txt2', txt2_carousel_item_template, txt2_items, 2, 4);
    make_carousel('results-img2', img2_carousel_item_template, img2_items, 2, 4);
    make_carousel('results-variants', variants_carousel_item_template, variants_items, 2, 1);
    make_carousel('results-manipulation', manipulation_carousel_item_template, manipulation_items, 1, 1);
    make_selection_panel('results-scene', scene_selection_panel_thumbnail_template, scene_selection_panel_item_template, scene_items);
};
