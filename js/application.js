var scene_items = [
    {
        title: '<span style="font-weight: 700;">T</span><span style="font-size: 0.75em; font-weight: 800;">RELLIS</span> logo',
        video: "trellis/trellis.mp4",
        poster: "trellis/trellis.jpg",
        thumbnail: "trellis/trellis.jpg",
        model: "trellis/trellis.glb",
        assets: [
            {
                name: "T", model: "trellis/glbs/T.glb", position: [0, 0, 0], 
                prompt: "trellis/images/T.png", promtp_type: "image",
            },
            {
                name: "R", model: "trellis/glbs/R.glb", position: [1, 0, 0], 
                prompt: "trellis/images/R.png", promtp_type: "image",
            },
            {
                name: "E", model: "trellis/glbs/E.glb", position: [2, 0, 0], 
                prompt: "trellis/images/E.png", promtp_type: "image",
            },
            {
                name: "L1", model: "trellis/glbs/L1.glb", position: [3, 0, 0], 
                prompt: "trellis/images/L1.png", promtp_type: "image",
            },
            {
                name: "L2", model: "trellis/glbs/L2.glb", position: [4, 0, 0], 
                prompt: "trellis/images/L2.png", promtp_type: "image",
            },
            {
                name: "I", model: "trellis/glbs/I.glb", position: [4.75, 0, 0],
                prompt: "trellis/images/I.png", promtp_type: "image",
            },
            {
                name: "S", model: "trellis/glbs/S.glb", position: [5.6, 0, 0], 
                prompt: "trellis/images/S.png", promtp_type: "image",
            },
        ],
    },
    {
        title: "Vibrant Street View",
        video: "street/street.mp4",
        poster: "street/street.jpg",
        thumbnail: "street/thumb.jpg",
        model: "street/street.glb",
        assets: [
            {
                name: "Bakery", model: "street/glbs/bakery.glb", position: [0.3012695610523224, 0.20401564240455627, -0.5472332239151001], 
                prompt: "street/images/bakery.png", promtp_type: "image",
            },
            {
                name: "Bench", model: "street/glbs/bench.glb", position: [0.05278368294239044, 0.09360522031784058, -0.2388891577720642], 
                prompt: "street/images/bench.png", promtp_type: "image",
            },
            {
                name: "Bookstore", model: "street/glbs/bookstore.glb", position: [-0.13037031888961792, 0.24797889590263367, -0.6030496954917908], 
                prompt: "street/images/bookstore.png", promtp_type: "image",
            },
            {
                name: "Bus Stop", model: "street/glbs/bus_stop.glb", position: [0.17890265583992004, 0.11868228018283844, 0.2368682473897934], 
                prompt: "street/images/bus_stop.png", promtp_type: "image",
            },
            {
                name: "Car", model: "street/glbs/car.glb", position: [0.7934836149215698, 0.09193491190671921, -0.06817339360713959], 
                prompt: "street/images/car.png", promtp_type: "image",
            },
            {
                name: "Carriage", model: "street/glbs/carriage.glb", position: [-0.9742140769958496, 0.24355348944664001, 0.41752028465270996], 
                prompt: "street/images/carriage.png", promtp_type: "image",
            },
            {
                name: "City Bus", model: "street/glbs/city_bus.glb", position: [-0.11295752227306366, 0.1206739991903305, 0.12294311821460724], 
                prompt: "street/images/city_bus.png", promtp_type: "image",
            },
            {
                name: "Convertible", model: "street/glbs/convertible.glb", position: [0.7985010147094727, 0.06392733752727509, 0.14159464836120605], 
                prompt: "Red sports car.", promtp_type: "text",
            },
            {
                name: "Flower Bed", model: "street/glbs/flower_bed.glb", position: [-0.16804663836956024, 0.06908395886421204, -0.2509487271308899],
                prompt: "street/images/flower_bed.png", promtp_type: "image",
            },
            {
                name: "Food Cart", model: "street/glbs/street_food_cart.glb", position: [0.34437891840934753, 0.12713566422462463, -0.26250723004341125], 
                prompt: "street/images/street_food_cart.png", promtp_type: "image",
            },
            {
                name: "Locomotive", model: "street/glbs/locomotive.glb", position: [-0.35538190603256226, 0.2391899973154068, 0.4138977527618408], 
                prompt: "street/images/locomotive.png", promtp_type: "image",
            },
            {
                name: "Pavement", model: "street/glbs/pavement.glb", position: [0.8523586392402649, 0, -0.28071996569633484], 
                prompt: "street/images/pavement.png", promtp_type: "image",
            },
            {
                name: "Pedestrian 1", model: "street/glbs/pedestrian1.glb", position: [0.5562798380851746, 0.11969900131225586, 0.01110604964196682], 
                prompt: "street/images/pedestrian1.png", promtp_type: "image",
            },
            {
                name: "Pedestrian 2", model: "street/glbs/pedestrian2.glb", position: [-0.018760032951831818, 0.1099017933011055, -0.3524319529533386], 
                prompt: "street/images/pedestrian2.png", promtp_type: "image",
            },
            {
                name: "Police Officer", model: "street/glbs/police_officer.glb", position: [0.5027366876602173, 0.11618942022323608, -0.19886554777622223], 
                prompt: "Police officer with a blue uniform, casual style.", promtp_type: "text",
            },
            {
                name: "Road", model: "street/glbs/road.glb", position: [-0.2199999988079071, 0, 0.03999999910593033], 
                prompt: "street/images/road.png", promtp_type: "image",
            },
            {
                name: "Small Cafe", model: "street/glbs/small_cafe.glb", position: [0.7130870819091797, 0.18770591914653778, -0.4970000386238098],
                prompt: "street/images/small_cafe.png", promtp_type: "image",
            },
            {
                name: "Street Building", model: "street/glbs/street_building.glb", position: [-1.0728062391281128, 0.37511497735977173, -0.6498621106147766], 
                prompt: "street/images/street_building.png", promtp_type: "image",
            },
            {
                name: "Street Lamp", model: "street/glbs/street_lamp.glb", position: [0.4503174424171448, 0.16712810099124908, -0.3516654074192047], 
                prompt: "Black metal streetlamp with yellow light.", promtp_type: "text",
            },
            {
                name: "Track", model: "street/glbs/track.glb", position: [-0.21750077605247498, 0, 0.41999998688697815], 
                prompt: "street/images/track.png", promtp_type: "image",
            },
            {
                name: "Traffic Light", model: "street/glbs/traffic_light_pole.glb", position: [0.6433064341545105, 0.16215699911117554, -0.16337531805038452], 
                prompt: "street/images/traffic_light_pole.png", promtp_type: "image",
            },
            {
                name: "Tree 1", model: "street/glbs/street_tree1.glb", position: [-0.8529333472251892, 0.2236703783273697, -0.26323166489601135], 
                prompt: "Street tree.", promtp_type: "text",
            },
            {
                name: "Tree 2", model: "street/glbs/street_tree2.glb", position: [-0.408209890127182, 0.19226358830928802, -0.2531917691230774], 
                prompt: "Street tree.", promtp_type: "text",
            },
            {
                name: "Tree 3", model: "street/glbs/street_tree3.glb", position: [-1.2882800102233887, 0.17525239288806915, -0.26461952924728394], 
                prompt: "Street tree.", promtp_type: "text",
            },
            {
                name: "Two-story Building", model: "street/glbs/urban_building.glb", position: [-0.5440289378166199, 0.32528433203697205, -0.6081684231758118],
                prompt: "Two-story rectangular urban building with flat orange roof, teal façade.", promtp_type: "text",
            },
        ],
    },
    {
        title: "Dwarf Blacksmith Shop",
        video: "blacksmith/blacksmith.mp4",
        poster: "blacksmith/blacksmith.jpg",
        thumbnail: "blacksmith/thumb.jpg",
        model: "blacksmith/blacksmith.glb",
        assets: [
            {
                name: "Background", model: "blacksmith/glbs/background.glb", position: [0, 0, 0], 
                prompt: "blacksmith/images/background.png", promtp_type: "image",
            },
            {
                name: "Chest", model: "blacksmith/glbs/chest.glb", position: [-0.31, -0.06, -0.28], 
                prompt: "Wooden and iron chest.", promtp_type: "text",
            },
            {
                name: "Crate", model: "blacksmith/glbs/crate.glb", position: [-0.31, -0.27, -0.27], 
                prompt: "Wooden crate.", promtp_type: "text",
            },
            {
                name: "Dwarf", model: "blacksmith/glbs/dwarf.glb", position: [0.55, -0.14, -0.29], 
                prompt: "blacksmith/images/dwarf.png", promtp_type: "image",
            },
            {
                name: "Fireplace", model: "blacksmith/glbs/fireplace.glb", position: [0.11, -0.15, -0.34], 
                prompt: "blacksmith/images/fireplace.png", promtp_type: "image",
            },
            {
                name: "Lantern", model: "blacksmith/glbs/lantern.glb", position: [0.25, -0.088, 0.36], 
                prompt: "blacksmith/images/lantern.png", promtp_type: "image",
            },
            {
                name: "Mailbox", model: "blacksmith/glbs/mailbox.glb", position: [-0.37, 0.16, 0.32], 
                prompt: "blacksmith/images/mailbox.png", promtp_type: "image",
            },
            {
                name: "Paper Machine", model: "blacksmith/glbs/paper_machine.glb", position: [-0.32, -0.056, 0.28], 
                prompt: "blacksmith/images/paper_machine.png", promtp_type: "image",
            },
            {
                name: "Phonograph", model: "blacksmith/glbs/phonograph.glb", position: [0.23, 0.158, -0.33], 
                prompt: "Phonograph.", promtp_type: "text",
            },
            {
                name: "Table", model: "blacksmith/glbs/table.glb", position: [0.33, -0.258, 0.33], 
                prompt: "Round dark wooden table.", promtp_type: "text",
            },
            {
                name: "Telephone", model: "blacksmith/glbs/telephone.glb", position: [0.34, -0.083, 0.28],
                prompt: "blacksmith/images/telephone.png", promtp_type: "image",
            },
            {
                name: "Television", model: "blacksmith/glbs/television.glb", position: [0.03, 0.155, -0.33], 
                prompt: "blacksmith/images/television.png", promtp_type: "image",
            },
            {
                name: "Toolbox", model: "blacksmith/glbs/toolbox.glb", position: [-0.3, -0.08, 0.1], 
                prompt: "blacksmith/images/toolbox.png", promtp_type: "image",
            },
            {
                name: "Workbench", model: "blacksmith/glbs/workbench.glb", position: [-0.29, -0.24, 0.17], 
                prompt: "blacksmith/images/workbench.png", promtp_type: "image",
            }
        ],
    },
];


function scene_selection_panel_thumbnail_template(item) {
    return `<img src="/assets/scenes/${item.thumbnail}" style="height: 100px;">`;
}


function scene_selection_panel_item_template(item) {
    return `<div class="x-card">
                <div class="x-row" style="margin-bottom: 16px">
                    <div style="font-size: 28px; font-weight: 700; margin-left: 8px">${item.title}</div>
                    <div class="x-flex-spacer"></div>
                    <div class="x-button" onclick=\'openWindow(scene_window_template(${JSON.stringify(item)}))\'>View GLB</div>
                </div>
                <div style="width: 100%; aspect-ratio: 16/9">
                    <video controls muted height="100%" src="/assets/scenes/${item.video}" poster="/assets/scenes/${item.poster}"></video>
                </div>
            </div>`;
}

function scene_asset_prompt_template(asset) {
    if (asset.promtp_type === "image")
        return `<div class="x-image-prompt"><img src="/assets/scenes/${asset.prompt}"></div>`;
    else 
        return `<div class="x-handwriting">${asset.prompt}</div>`;
}

function scene_window_template(item) {
    let panel = scene_panel_template(item);
    item = JSON.parse(JSON.stringify(item));
    item.model = '/assets/scenes/' + item.model
    for (let asset of item.assets) {
        asset.model = '/assets/scenes/' + asset.model;
    }
    item.prompt_template = scene_asset_prompt_template
    return modelviewer_window_template(item, panel, {viewer_size: 600, panel_size: 550, show_annotations: true});
}
