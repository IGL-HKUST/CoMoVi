// Cards component for TRELLIS-style generation cards

// Sample data - replace with your actual data
const text2assetCards = [
    {
        video: "video/3cdba8.mp4",
        prompt: "A woman in blue yoga attire transitions from the Upward-Facing Dog pose to the Downward-Facing Dog pose on a grey yoga mat.",
        image: "images/results/3cdba8.jpg"
    },
    {
        video: "video/2820ff.mp4",
        prompt: "A man wearing a red and black long-sleeved shirt, black shorts, a helmet, and gloves stands next to his mountain bike in a dusty clearing and gestures while talking.",
        image: "images/results/2820ff.jpg"
    },
    {
        video: "video/3b30d9.mp4",
        prompt: "A woman in workout clothes does reverse lunges with her left leg while holding light dumbbells at her chest.",
        image: "images/results/3b30d9.jpg"
    },
    {
        video: "video/dfupki.mp4",
        prompt: "A man in a dark suit walks forward on a stage towards a bright, smoky light source.",
        image: "images/results/dfupki.jpg"
    },
    {
        video: "video/22912e.mp4",
        prompt: "A woman with her hair in a bun, wearing a black top and pants, bends over to harvest leafy greens and places them into a woven basket.",
        image: "images/results/22912e.jpg"
    },
    {
        video: "video/rhvevq.mp4",
        prompt: "A woman wearing a blue t-shirt, camouflage pants, and glasses stands in a forest and pulls back the string of a recurve bow to aim at a target.",
        image: "images/results/rhvevq.jpg"
    }
];

// Dataset results cards data - replace with your actual dataset results
const datasetResultsCards = [
    {
        video: "video/3cdba8.mp4",
        prompt: "A woman in blue yoga attire transitions from the Upward-Facing Dog pose to the Downward-Facing Dog pose on a grey yoga mat.",
        image: "images/results/3cdba8.jpg"
    },
    {
        video: "video/2820ff.mp4",
        prompt: "A man wearing a red and black long-sleeved shirt, black shorts, a helmet, and gloves stands next to his mountain bike in a dusty clearing and gestures while talking.",
        image: "images/results/2820ff.jpg"
    },
    {
        video: "video/3b30d9.mp4",
        prompt: "A woman in workout clothes does reverse lunges with her left leg while holding light dumbbells at her chest.",
        image: "images/results/3b30d9.jpg"
    },
    {
        video: "video/dfupki.mp4",
        prompt: "A man in a dark suit walks forward on a stage towards a bright, smoky light source.",
        image: "images/results/dfupki.jpg"
    },
    {
        video: "video/22912e.mp4",
        prompt: "A woman with her hair in a bun, wearing a black top and pants, bends over to harvest leafy greens and places them into a woven basket.",
        image: "images/results/22912e.jpg"
    },
    {
        video: "video/rhvevq.mp4",
        prompt: "A woman wearing a blue t-shirt, camouflage pants, and glasses stands in a forest and pulls back the string of a recurve bow to aim at a target.",
        image: "images/results/rhvevq.jpg"
    }
];

// Dataset results cards data - replace with your actual dataset results
const dailyCards = [
    {
        video: "video/dataset/daily/8dy6fC4fnOs_61_split1.mp4",
        prompt: "A man wearing a black hoodie, black pants, and orange sneakers stands between two cars on a racetrack, gesturing with his arms and walking slightly.",
        image: "video/dataset/daily/8dy6fC4fnOs_61_split1.jpg",
    },
    {
        video: "video/dataset/daily/8sHCkfrHCWs_0_split2.mp4",
        prompt: "A man in a white hat, white button-up shirt, orange t-shirt, and white pants stands at the bow of a moving blue boat, clapping his hands together, then putting them on his hips.",
        image: "video/dataset/daily/8sHCkfrHCWs_0_split2.jpg"
    },
    {
        video: "video/dataset/daily/9sBabSI-fwY_4_split1.mp4",
        prompt: "A woman in a red and black tank top and black leggings is jogging in place under a bridge.",
        image: "video/dataset/daily/9sBabSI-fwY_4_split1.jpg",
    },
    {
        video: "video/dataset/daily/hgw2_G8EAtg_5_split1.mp4",
        prompt: "A man in black sportswear performs a lay-down turnaround sprint by getting up from a lying position, turning around, and sprinting away from the camera.",
        image: "video/dataset/daily/hgw2_G8EAtg_5_split1.jpg",
    }
];

// Dataset results cards data - replace with your actual dataset results
const sportsCards = [
    {
        video: "video/dataset/sports/1EBgcTlMd-c_0_split2.mp4",
        prompt: "A man in black and red athletic wear performs a soccer trick, kicking the ball up behind his back and catching it with his left foot.",
        image: "video/dataset/sports/1EBgcTlMd-c_0_split2.jpg"
    },
    {
        video: "video/dataset/sports/AJ2_gn8V2fo_3_split2.mp4",
        prompt: "A man in a white t-shirt and black shorts stands on a basketball court, holds a basketball, and shoots a jump shot.",
        image: "video/dataset/sports/AJ2_gn8V2fo_3_split2.jpg"
    },
    {
        video: "video/dataset/sports/BeGyALmARoo_8_split1.mp4",
        prompt: "A male baseball pitcher wearing a dark blue shirt, white pants, and a cap winds up and begins to throw a pitch from the pitcher's mound.",
        image: "video/dataset/sports/BeGyALmARoo_8_split1.jpg"
    },
    {
        video: "video/dataset/sports/C7374_PQZ6k_3_split1.mp4",
        prompt: "A man in a tan t-shirt, black shorts, and a white baseball cap swings a baseball bat, hitting a ball off a tee into a large practice net.",
        image: "video/dataset/sports/C7374_PQZ6k_3_split1.jpg"
    },
    {
        video: "video/dataset/sports/hsn2CUHzUNk_1_split1.mp4",
        prompt: "A young woman in a white tennis dress and a dark cap hits a forehand volley on a green tennis court.",
        image: "video/dataset/sports/hsn2CUHzUNk_1_split1.jpg"
    },
    {
        video: "video/dataset/sports/KjODd2idBhg_18_split2.mp4",
        prompt: "A man wearing a black tank top, grey and white shorts, and turquoise sneakers performs a crossover dribble with a basketball on an indoor basketball court.",
        image: "video/dataset/sports/KjODd2idBhg_18_split2.jpg"
    },
    {
        video: "video/dataset/sports/-LWq9Npv6Ew_37_split2.mp4",
        prompt: "A man in a light green t-shirt and black shorts dribbles a soccer ball to his right before jogging forward.",
        image: "video/dataset/sports/-LWq9Npv6Ew_37_split2.jpg"
    },
    {
        video: "video/dataset/sports/uOPCpEVQaGo_48_split1.mp4",
        prompt: "A woman wearing a helmet, a black vest over a red long-sleeved shirt, and light-colored pants is sitting on a dark horse and riding it at a walking pace.",
        image: "video/dataset/sports/uOPCpEVQaGo_48_split1.jpg"
    },
    {
        video: "video/dataset/sports/xNVq9WFCIw0_25_split2.mp4",
        prompt: "A boy wearing a black t-shirt, black shorts, and a black knee pad on his legs performs a volleyball set.",
        image: "video/dataset/sports/xNVq9WFCIw0_25_split2.jpg"
    },
    {
        video: "video/dataset/sports/Zd1unCdI7R4_13_split2.mp4",
        prompt: "A man wearing a long-sleeved shirt and dark pants stands on a tennis court and performs a tennis serve.",
        image: "video/dataset/sports/Zd1unCdI7R4_13_split2.jpg"
    }
];

// Dataset results cards data - replace with your actual dataset results
const strengthCards = [
    {
        video: "video/dataset/strength/0Au9szyo-6U_0_split1.mp4",
        prompt: "A woman in blue yoga attire transitions from the Upward-Facing Dog pose to the Downward-Facing Dog pose on a grey yoga mat.",
        image: "video/dataset/strength/0Au9szyo-6U_0_split1.jpg"
    },
    {
        video: "video/dataset/strength/1ALZFijLDPY_9_split1.mp4",
        prompt: "A man wearing a red and black long-sleeved shirt, black shorts, a helmet, and gloves stands next to his mountain bike in a dusty clearing and gestures while talking.",
        image: "video/dataset/strength/1ALZFijLDPY_9_split1.jpg"
    },
    {
        video: "video/dataset/strength/1lAxCiCbfDI_7_split1.mp4",
        prompt: "A woman in workout clothes does reverse lunges with her left leg while holding light dumbbells at her chest.",
        image: "video/dataset/strength/1lAxCiCbfDI_7_split1.jpg"
    },
    {
        video: "video/dataset/strength/6bn7MRPCFlQ_6_split2.mp4",
        prompt: "A man in a dark suit walks forward on a stage towards a bright, smoky light source.",
        image: "video/dataset/strength/6bn7MRPCFlQ_6_split2.jpg"
    },
    {
        video: "video/dataset/strength/7cZyis1RAhU_33_split2.mp4",
        prompt: "A woman with her hair in a bun, wearing a black top and pants, bends over to harvest leafy greens and places them into a woven basket.",
        image: "video/dataset/strength/7cZyis1RAhU_33_split2.jpg"
    },
    {
        video: "video/dataset/strength/63BbUhXdcWc_44_split1.mp4",
        prompt: "A woman wearing a blue t-shirt, camouflage pants, and glasses stands in a forest and pulls back the string of a recurve bow to aim at a target.",
        image: "video/dataset/strength/63BbUhXdcWc_44_split1.jpg"
    },
    {
        video: "video/dataset/strength/ecxgiZY2Cr4_11_split1.mp4",
        prompt: "A woman wearing a blue t-shirt, camouflage pants, and glasses stands in a forest and pulls back the string of a recurve bow to aim at a target.",
        image: "video/dataset/strength/ecxgiZY2Cr4_11_split1.jpg"
    },
    {
        video: "video/dataset/strength/O3MP6BbtBFA_10_split1.mp4",
        prompt: "A woman wearing a blue t-shirt, camouflage pants, and glasses stands in a forest and pulls back the string of a recurve bow to aim at a target.",
        image: "video/dataset/strength/O3MP6BbtBFA_10_split1.jpg"
    },
    {
        video: "video/dataset/strength/QtP1mNhLiUw_103_split2.mp4",
        prompt: "A woman wearing a blue t-shirt, camouflage pants, and glasses stands in a forest and pulls back the string of a recurve bow to aim at a target.",
        image: "video/dataset/strength/QtP1mNhLiUw_103_split2.jpg"
    },
    {
        video: "video/dataset/strength/vetqSFC2GNA_4_split2.mp4",
        prompt: "A woman wearing a blue t-shirt, camouflage pants, and glasses stands in a forest and pulls back the string of a recurve bow to aim at a target.",
        image: "video/dataset/strength/vetqSFC2GNA_4_split2.jpg"
    }
];

// Dataset results cards data - replace with your actual dataset results
const calisthenicsCards = [
    {
        video: "video/dataset/calisthenics/_r_z7DUpjH8_26_split1.mp4",
        prompt: "A woman in a purple top and black leggings, lying on a blue yoga mat, performs leg raises by lowering and then raising her straight legs.",
        image: "video/dataset/calisthenics/_r_z7DUpjH8_26_split1.jpg"
    },
    {
        video: "video/dataset/calisthenics/4QZe_U0xZBQ_19_split1.mp4",
        prompt: "A man in a black and neon green tank top and black shorts performs L-sit pull-ups on an outdoor pull-up bar.",
        image: "video/dataset/calisthenics/4QZe_U0xZBQ_19_split1.jpg"
    },
    {
        video: "video/dataset/calisthenics/6_cSCKrFRNI_19_split1.mp4",
        prompt: "A blonde woman in a black crop top and orange shorts holds a green dumbbell in each hand and performs calf raises.",
        image: "video/dataset/calisthenics/6_cSCKrFRNI_19_split1.jpg"
    },
    {
        video: "video/dataset/calisthenics/7AhIZkvQCwk_26_split1.mp4",
        prompt: "A shirtless man in blue shorts and white shoes performs upside-down dips on gymnastic rings hanging from a tree.",
        image: "video/dataset/calisthenics/7AhIZkvQCwk_26_split1.jpg"
    },
    {
        video: "video/dataset/calisthenics/7Bi93O10vho_4_split1.mp4",
        prompt: "A blonde woman in black workout clothes is doing crunches on a green mat in a gym.",
        image: "video/dataset/calisthenics/7Bi93O10vho_4_split1.jpg"
    },
    {
        video: "video/dataset/calisthenics/9qLSYHIHp10_47_split1.mp4",
        prompt: "A woman with blonde hair, wearing a grey sports bra and leggings, performs a weighted side plank by lifting a weight plate from the floor up towards the ceiling.",
        image: "video/dataset/calisthenics/9qLSYHIHp10_47_split1.jpg"
    },
    {
        video: "video/dataset/calisthenics/-cUW9wjrSDQ_17_split1.mp4",
        prompt: "A man in a red t-shirt and black shorts performs walking push-ups on a red mat.",
        image: "video/dataset/calisthenics/-cUW9wjrSDQ_17_split1.jpg"
    },
    {
        video: "video/dataset/calisthenics/ecxgiZY2Cr4_32_split2.mp4",
        prompt: "A man in a red shirt and black shorts lies on his back on a green mat and performs a weighted sit-up, holding a kettlebell with both hands.",
        image: "video/dataset/calisthenics/ecxgiZY2Cr4_32_split2.jpg"
    },
    {
        video: "video/dataset/calisthenics/fGXMpWSJceQ_22_split1.mp4",
        prompt: "A man in a blue t-shirt and black pants performs weighted pull-ups on a pull-up bar, with dumbbells attached to a belt around his waist.",
        image: "video/dataset/calisthenics/fGXMpWSJceQ_22_split1.jpg"
    },
    {
        video: "video/dataset/calisthenics/h0HjqYRlXYg_25_split1.mp4",
        prompt: "A shirtless man with a shaved head, wearing blue shorts and white sneakers, performs handstand push-ups next to a brick wall.",
        image: "video/dataset/calisthenics/h0HjqYRlXYg_25_split1.jpg"
    }
];

// Dataset results cards data - replace with your actual dataset results
const flexibilityCards = [
    {
        video: "video/dataset/flexibility/_r_z7DUpjH8_35_split2.mp4",
        prompt: "A woman with long brown hair, wearing a purple top and black leggings, performs a Pilates roll down exercise, lowering her torso from a sitting position to lying flat on a white mat.",
        image: "video/dataset/flexibility/_r_z7DUpjH8_35_split2.jpg"
    },
    {
        video: "video/dataset/flexibility/3Mgfyi0epiE_5_split1.mp4",
        prompt: "A man in a blue jumpsuit with red stripes moves side to side, shifting his weight and swinging his arms in a fluid, dance-like motion.",
        image: "video/dataset/flexibility/3Mgfyi0epiE_5_split1.jpg"
    },
    {
        video: "video/dataset/flexibility/-Agg9sgQ_5A_33_split1.mp4",
        prompt: "A woman with brown hair, wearing a green t-shirt and blue jeans, performs a Cat-Cow pose by arching and then rounding her spine while on all fours on a yoga mat.",
        image: "video/dataset/flexibility/-Agg9sgQ_5A_33_split1.jpg"
    },
    {
        video: "video/dataset/flexibility/CPJp_I_bghQ_38_split2.mp4",
        prompt: "A woman wearing a black tank top and purple leggings performs a side-lying pilates exercise on a colorful mat, transitioning from lying on her side to sitting up.",
        image: "video/dataset/flexibility/CPJp_I_bghQ_38_split2.jpg"
    },
    {
        video: "video/dataset/flexibility/IigVQL8dabU_23_split1.mp4",
        prompt: "A man wearing a black tracksuit and yellow shoes stands on a grassy slope while holding a resistance band above his head and stretching it.",
        image: "video/dataset/flexibility/IigVQL8dabU_23_split1.jpg"
    },
    {
        video: "video/dataset/flexibility/K9lGp6DENUE_27_split1.mp4",
        prompt: "A woman with dark hair in a ponytail, wearing a sports bra and shorts, performs a plank with mountain climbers and leg kicks on a purple yoga mat.",
        image: "video/dataset/flexibility/K9lGp6DENUE_27_split1.jpg"
    },
    {
        video: "video/dataset/flexibility/QzPvbI9WSr4_9_split1.mp4",
        prompt: "A bald man in black clothing performs a series of flowing Tai Chi movements, transitioning from a one-legged stance to a low lunge while moving his arms.",
        image: "video/dataset/flexibility/QzPvbI9WSr4_9_split1.jpg"
    },
    {
        video: "video/dataset/flexibility/vPtvS_RhYhQ_42_split1.mp4",
        prompt: "A woman in an orange sports bra and blue pants performs a Reverse Warrior yoga pose, stretching her right arm forward and left arm back, then both behind her hip.",
        image: "video/dataset/flexibility/vPtvS_RhYhQ_42_split1.jpg"
    }
];

// Dataset results cards data - replace with your actual dataset results
const cardioCards = [
    {
        video: "video/dataset/cardio/_jWEsu0uSJI_4_split1.mp4",
        prompt: "A woman with dark hair in a ponytail, wearing a yellow sports bra and blue leggings, performs jump rope exercises on a wooden deck outdoors.",
        image: "video/dataset/cardio/_jWEsu0uSJI_4_split1.jpg"
    },
    {
        video: "video/dataset/cardio/1r3Fly5TsLw_98_split1.mp4",
        prompt: "A blonde woman in a purple sports bra and grey leggings performs mountain climbers on a black circular mat.",
        image: "video/dataset/cardio/1r3Fly5TsLw_98_split1.jpg"
    },
    {
        video: "video/dataset/cardio/7a0auCITZ1c_12_split1.mp4",
        prompt: "A woman with blonde hair, wearing a neon yellow sports bra and black leggings, performs jumping jacks by crossing and uncrossing her arms in front of her chest and overhead.",
        image: "video/dataset/cardio/7a0auCITZ1c_12_split1.jpg"
    },
    {
        video: "video/dataset/cardio/7IWYo4THg0M_44_split2.mp4",
        prompt: "A woman wearing a red sports bra and black capri leggings performs walkout burpees in her living room.",
        image: "video/dataset/cardio/7IWYo4THg0M_44_split2.jpg"
    },
    {
        video: "video/dataset/cardio/dB_VAT9ephA_18_split2.mp4",
        prompt: "A woman in a sports bra and patterned leggings performs jumping jacks in a white room.",
        image: "video/dataset/cardio/dB_VAT9ephA_18_split2.jpg"
    },
    {
        video: "video/dataset/cardio/jaM8xtAEk88_6_split1.mp4",
        prompt: "A woman with reddish-brown hair in a ponytail, wearing a black tank top and red leggings, performs high knees in place.",
        image: "video/dataset/cardio/jaM8xtAEk88_6_split1.jpg"
    },
    {
        video: "video/dataset/cardio/jaM8xtAEk88_47_split1.mp4",
        prompt: "A woman with red hair, wearing a black top and red leggings, performs burpees in a gym.",
        image: "video/dataset/cardio/jaM8xtAEk88_47_split1.jpg"
    },
    {
        video: "video/dataset/cardio/VUp-gK6i8lA_39_split1.mp4",
        prompt: "A tattooed, shirtless man wearing grey sweatpants performs mountain climbers in a gym.",
        image: "video/dataset/cardio/VUp-gK6i8lA_39_split1.jpg"
    },
    {
        video: "video/dataset/cardio/wdyoz11HP88_14_split1.mp4",
        prompt: "A man with blonde-tipped hair, wearing a long-sleeved shirt, shorts, and leggings, performs shadow boxing movements while holding small pink weights inside a boxing ring.",
        image: "video/dataset/cardio/wdyoz11HP88_14_split1.jpg"
    },
    {
        video: "video/dataset/cardio/y5FUG3SHI0Q_71_split2.mp4",
        prompt: "A woman in a bikini picks up a jump rope from the floor and prepares to start skipping in a living room.",
        image: "video/dataset/cardio/y5FUG3SHI0Q_71_split2.jpg"
    }
];

// Dataset results cards data - replace with your actual dataset results
const targetCards = [
    {
        video: "video/dataset/target/-JBgrlDk6wU_96_split1.mp4",
        prompt: "A man wearing a black vest, shirt, pants, and cap putts a red golf ball with a putter on a mini-golf course.",
        image: "video/dataset/target/-JBgrlDk6wU_96_split1.jpg"
    },
    {
        video: "video/dataset/target/JrL0YrFCDz0_3_split1.mp4",
        prompt: "An adult male wearing a black polo shirt, green cargo pants, and hearing protection picks up a rifle from a table, aims it forward, and prepares to fire at a target in a shooting range.",
        image: "video/dataset/target/JrL0YrFCDz0_3_split1.jpg"
    },
    {
        video: "video/dataset/target/L4orK_3fLuA_20_split1.mp4",
        prompt: "A man in desert camouflage, a tactical vest, and sunglasses stands on a gravel range and raises a rifle into a shooting stance, aiming forward.",
        image: "video/dataset/target/L4orK_3fLuA_20_split1.jpg"
    },
    {
        video: "video/dataset/target/noH5XQI5BYk_12_split1.mp4",
        prompt: "A woman in a white long-sleeved shirt, black pants, and a white hat prepares for an archery shot by lifting her bow and arrow into a shooting position.",
        image: "video/dataset/target/noH5XQI5BYk_12_split1.jpg"
    }
];

// Dataset results cards data - replace with your actual dataset results
const equipmentCards = [
    {
        video: "video/dataset/equipment/730TP6W898c_47_split1.mp4",
        prompt: "An adult male wearing cycling gear is riding a stationary bike trainer, pedaling with a consistent rhythm while looking forward and slightly to his left.",
        image: "video/dataset/equipment/730TP6W898c_47_split1.jpg"
    },
    {
        video: "video/dataset/equipment/B4PvQ76Bm8w_9_split1.mp4",
        prompt: "A blonde woman in a pink t-shirt and black shorts runs on a black treadmill in a white room.",
        image: "video/dataset/equipment/B4PvQ76Bm8w_9_split1.jpg"
    },
    {
        video: "video/dataset/equipment/PYKE-nVbE6Q_11_split1.mp4",
        prompt: "A man with long hair tied back, wearing a navy tank top and shorts, sits on a rowing machine while talking and gesturing with his hands.",
        image: "video/dataset/equipment/PYKE-nVbE6Q_11_split1.jpg"
    },
    {
        video: "video/dataset/equipment/QCEOE7oOnxg_6_split1.mp4",
        prompt: "A woman with dark hair in a black sports bra and patterned leggings walks sideways on a treadmill in a gym.",
        image: "video/dataset/equipment/QCEOE7oOnxg_6_split1.jpg"
    }
];

// Dataset results cards data - replace with your actual dataset results
const wheeledCards = [
    {
        video: "video/dataset/wheeled/Bsk44z-YvYc_26_split2.mp4",
        prompt: "A woman with blonde hair, wearing a black sweatshirt with red and white stripes and black leggings, demonstrates a jumping roller skating move in a roller rink.",
        image: "video/dataset/wheeled/Bsk44z-YvYc_26_split2.jpg"
    },
    {
        video: "video/dataset/wheeled/eKrTPfYQkRc_27_split1.mp4",
        prompt: "A man in cycling gear rides a bicycle on a paved road, pedaling steadily.",
        image: "video/dataset/wheeled/eKrTPfYQkRc_27_split1.jpg"
    },
    {
        video: "video/dataset/wheeled/ICc9cSSnMEc_19_split2.mp4",
        prompt: "A man wearing a dark long-sleeved shirt and grey pants performs a 180-degree spin on rollerblades on a paved street.",
        image: "video/dataset/wheeled/ICc9cSSnMEc_19_split2.jpg"
    },
    {
        video: "video/dataset/wheeled/izt16Y7x2Ck_0_split1.mp4",
        prompt: "A shirtless adult male in black underwear stands on a longboard and slowly rides it forward in a living room.",
        image: "video/dataset/wheeled/izt16Y7x2Ck_0_split1.jpg"
    },
    {
        video: "video/dataset/wheeled/nptzpZlo96M_20_split1.mp4",
        prompt: "A man in a grey suit rides an electric unicycle towards the camera on a sidewalk, points at the camera, and holds a bag in his left hand.",
        image: "video/dataset/wheeled/nptzpZlo96M_20_split1.jpg"
    },
    {
        video: "video/dataset/wheeled/o2s1S_GYFC0_43_split1.mp4",
        prompt: "A person in a yellow long-sleeved shirt, dark pants, and a helmet rides a BMX bike up a wooden ramp, performs an air turn, and lands back on the ramp.",
        image: "video/dataset/wheeled/o2s1S_GYFC0_43_split1.jpg"
    },
    {
        video: "video/dataset/wheeled/ZFTyz5Gdklg_91_split2.mp4",
        prompt: "A male wearing a black hoodie, black pants, and a grey cap performs a nollie backside bigspin on a skateboard in an indoor skatepark.",
        image: "video/dataset/wheeled/ZFTyz5Gdklg_91_split2.jpg"
    },
    {
        video: "video/dataset/wheeled/Zrnhd2PGSqw_24_split2.mp4",
        prompt: "A man wearing a grey long-sleeved shirt and light-colored pants rides a small, yellow, three-wheeled electric scooter across a paved parking lot.",
        image: "video/dataset/wheeled/Zrnhd2PGSqw_24_split2.jpg"
    }
];

// Dataset results cards data - replace with your actual dataset results
const winterCards = [
    {
        video: "video/dataset/winter/5X3xxCAzNSc_12_split1.mp4",
        prompt: "A woman in a pink skating outfit with a short skirt performs a jump on an ice rink.",
        image: "video/dataset/winter/5X3xxCAzNSc_12_split1.jpg"
    },
    {
        video: "video/dataset/winter/bNkXj7vDNjQ_20_split1.mp4",
        prompt: "An ice hockey player wearing a gray jersey with the number 11, black pants with white and yellow stripes, a helmet, and green gloves skates around the rink while handling a puck with a hockey stick.",
        image: "video/dataset/winter/bNkXj7vDNjQ_20_split1.jpg"
    },
    {
        video: "video/dataset/winter/cT5KpJlaSE8_35_split2.mp4",
        prompt: "A girl in a yellow figure skating dress performs a layback spin on an ice rink.",
        image: "video/dataset/winter/cT5KpJlaSE8_35_split2.jpg"
    },
    {
        video: "video/dataset/winter/QxYhK6TseTg_79_split1.mp4",
        prompt: "A person wearing a brown jacket, black pants, and a black helmet is snowboarding down a snowy slope, making S-turns.",
        image:"video/dataset/winter/QxYhK6TseTg_79_split1.jpg"
    },
    {
        video: "video/dataset/winter/s0byLL4K1j4_30_split1.mp4",
        prompt: "A person wearing a blue jacket, black pants, and a beanie is snowboarding down a snowy mountain slope.",
        image: "video/dataset/winter/s0byLL4K1j4_30_split1.jpg"
    },
    {
        video: "video/dataset/winter/sev9HpP4HCs_163_split1.mp4",
        prompt: "A man wearing black winter gear and sunglasses is cross-country skiing across a snowy landscape, pulling a red sled behind him.",
        image: "video/dataset/winter/sev9HpP4HCs_163_split1.jpg"
    },
    {
        video: "video/dataset/winter/viiVhx1phB0_23_split2.mp4",
        prompt: "A blonde woman in a red, sleeveless figure skating dress with beaded embellishments is performing on an ice rink, completing a spin and then gliding forward.",
        image: "video/dataset/winter/viiVhx1phB0_23_split2.jpg"
    },
    {
        video: "video/dataset/winter/WkO2mfocucU_12_split1.mp4",
        prompt: "A man wearing a black and red top, yellow leggings, and a red headband is cross-country skiing on a snowy field, using the skating technique.",
        image: "video/dataset/winter/WkO2mfocucU_12_split1.jpg"
    }
];

// Dataset results cards data - replace with your actual dataset results
const waterCards = [
    {
        video: "video/dataset/water/5fj7XjxKGzY_32_split2.mp4",
        prompt: "A woman in a green and black wetsuit top and bikini bottoms is freediving, raising her arms above her head as she descends.",
        image: "video/dataset/water/5fj7XjxKGzY_32_split2.jpg"
    },
    {
        video: "video/dataset/water/9skHx10Gvow_16_split1.mp4",
        prompt: "A bare-chested male wearing white shorts is stand-up paddleboarding on calm turquoise water.",
        image: "video/dataset/water/9skHx10Gvow_16_split1.jpg"
    },
    {
        video: "video/dataset/water/AGSDj41Ut3A_5_split1.mp4",
        prompt: "A man wearing a grey long-sleeved wetsuit, blue helmet, and blue harness is wind foiling across the water, holding onto the boom of a large red and blue sail.",
        image: "video/dataset/water/AGSDj41Ut3A_5_split1.jpg"
    },
    {
        video: "video/dataset/water/CcGseVYelm8_2_split2.mp4",
        prompt: "A man wearing a wetsuit and life vest stands still on a jet ski in the water.",
        image: "video/dataset/water/CcGseVYelm8_2_split2.jpg"
    },
    {
        video: "video/dataset/water/duuLUyQYWZs_13_split2.mp4",
        prompt: "A man in a black wetsuit is kitesurfing on a hydrofoil surfboard, moving from right to left across the water.",
        image: "video/dataset/water/duuLUyQYWZs_13_split2.jpg"
    },
    {
        video: "video/dataset/water/-fikrO9_aRc_44_split2.mp4",
        prompt: "A man wearing a black vest, shorts, a diving mask, and long fins is freediving horizontally underwater using a dolphin kick.",
        image: "video/dataset/water/-fikrO9_aRc_44_split2.jpg"
    },
    {
        video: "video/dataset/water/IN_24Krn4A8_51_split1.mp4",
        prompt: "A man wearing a hat and a vest stands on a kayak in the water and holds a fishing rod, preparing to cast.",
        image: "video/dataset/water/IN_24Krn4A8_51_split1.jpg"
    },
    {
        video: "video/dataset/water/Jbyt57BJ76s_30_split1.mp4",
        prompt: "A person in a black wetsuit is stand-up paddle surfing on a green wave, using a paddle for balance and steering.",
        image: "video/dataset/water/Jbyt57BJ76s_30_split1.jpg"
    },
    {
        video: "video/dataset/water/n7PHV6dSbPI_85_split2.mp4",
        prompt: "A person in a black wetsuit is stand-up paddle surfing on a small ocean wave.",
        image: "video/dataset/water/n7PHV6dSbPI_85_split2.jpg"
    },
    {
        video: "video/dataset/water/NZq1XBAit5k_53_split1.mp4",
        prompt: "A man in a white t-shirt, blue shorts, and sunglasses stands on the deck of a yacht, spreads his arms wide, and then brings them down to his sides while talking.",
        image: "video/dataset/water/NZq1XBAit5k_53_split1.jpg"
    },
    {
        video: "video/dataset/water/OxvEqxgLRIg_54_split1.mp4",
        prompt: "A man in a black wetsuit is kitesurfing, moving from left to right across the water while holding onto the control bar.",
        image: "video/dataset/water/OxvEqxgLRIg_54_split1.jpg"
    },
    {
        video: "video/dataset/water/TQ1lZors8Eo_47_split1.mp4",
        prompt: "A person in a black wetsuit is paddleboarding, riding along a small wave in the ocean.",
        image: "video/dataset/water/TQ1lZors8Eo_47_split1.jpg"
    }
];

// Dataset results cards data - replace with your actual dataset results
const airCards = [
    {
        video: "video/dataset/air/S2vQ_MbLQQM_37_split1.mp4",
        prompt: "A person wearing black skydiving gear and a helmet with a camera performs a skydive, falling in a sitting position with arms outstretched.",
        image: "video/dataset/air/S2vQ_MbLQQM_37_split1.jpg"
    },
    {
        video: "video/dataset/air/cDtNv-aHlEY_50_split1.mp4",
        prompt: "An elderly woman wearing a black skydiving suit, grey cap, and goggles is skydiving head-first in a prone position, smiling at the camera as she falls.",
        image: "video/dataset/air/cDtNv-aHlEY_50_split1.jpg"
    },
    {
        video: "video/dataset/air/iDZmBjUyf6E_27_split1.mp4",
        prompt: "A man wearing a black long-sleeved shirt, tan pants, a helmet, and a paragliding harness walks slowly forward on a sandy beach.",
        image: "video/dataset/air/iDZmBjUyf6E_27_split1.jpg"
    },
    {
        video: "video/dataset/air/qTwAjiL_2w8_28_split2.mp4",
        prompt: "A man wearing a helmet, sunglasses, and a camouflage jacket runs forward across a grassy field while pulling a large blue, green, and white paraglider wing up behind him.",
        image: "video/dataset/air/qTwAjiL_2w8_28_split2.jpg"
    }
];

// Dataset results cards data - replace with your actual dataset results
const danceCards = [
    {
        video: "video/dataset/dance/0bSKggCMbS4_1_split2.mp4",
        prompt: "A young female gymnast in a white leotard performs a dance sequence involving a passe turn and arm movements on a gymnastics floor.",
        image: "video/dataset/dance/0bSKggCMbS4_1_split2.jpg"
    },
    {
        video: "video/dataset/dance/a0azRlaQR7o_56_split2.mp4",
        prompt: "A woman in black dancewear and pink sneakers performs a fluid Latin-style dance routine, incorporating hip sways, arm movements, and spins in a dance studio.",
        image: "video/dataset/dance/a0azRlaQR7o_56_split2.jpg"
    },
    {
        video: "video/dataset/dance/Cn2LpRpGkNU_7_split2.mp4",
        prompt: "A woman in black dancewear performs a releve while holding onto a ballet barre.",
        image: "video/dataset/dance/Cn2LpRpGkNU_7_split2.jpg"
    },
    {
        video: "video/dataset/dance/Jgn1bUjvxEM_38_split1.mp4",
        prompt: "A man wearing a patterned shirt, dark pants, and a cap performs a series of dance steps on a red circular mat, including leg kicks, turns, and foot stomps.",
        image: "video/dataset/dance/Jgn1bUjvxEM_38_split1.jpg"
    },
    {
        video: "video/dataset/dance/ky53CQOPxus_64_split1.mp4",
        prompt: "A barefoot female with her hair tied back, wearing a white shirt and white shorts, performs a modern dance routine that includes spinning, kicking, and a grand jeté jump.",
        image: "video/dataset/dance/ky53CQOPxus_64_split1.jpg"
    },
    {
        video: "video/dataset/dance/RWXfpzynfbA_17_split2.mp4",
        prompt: "A barefoot man in a white hat, yellow jacket, and white pants performs a fluid and energetic dance routine on a stage.",
        image: "video/dataset/dance/RWXfpzynfbA_17_split2.jpg"
    },
    {
        video: "video/dataset/dance/tdghBf9oyeU_1_split1.mp4",
        prompt: "A man in a light blue checkered shirt and blue jeans dances while holding a black hat, swinging it around his upper body.",
        image: "video/dataset/dance/tdghBf9oyeU_1_split1.jpg"
    },
    {
        video: "video/dataset/dance/xQPoim-gw50_1_split2.mp4",
        prompt: "A female gymnast in a purple leotard begins her floor routine with a series of choreographed dance moves.",
        image: "video/dataset/dance/xQPoim-gw50_1_split2.jpg"
    },
    {
        video: "video/dataset/dance/ZN7Pmiu14QA_8_split1.mp4",
        prompt: "A woman in a brown tank top and light-colored pants performs a series of contemporary dance moves, including a high kick, a forward bend, a spin, and a jump, on a dark stage filled with smoke.",
        image: "video/dataset/dance/ZN7Pmiu14QA_8_split1.jpg"
    },
    {
        video: "video/dataset/dance/y-3sri2fsqc_10_split1.mp4",
        prompt: "A barefoot female dancer with long blonde hair, wearing a grey crop top and black leggings, performs a series of three fouette turns on pointe.",
        image: "video/dataset/dance/y-3sri2fsqc_10_split1.jpg"
    }
];

// Dataset category cards data - you can customize each category with different data
const datasetCategoryACards = dailyCards;
const datasetCategoryBCards = sportsCards;
const datasetCategoryCCards = strengthCards;
const datasetCategoryDCards = calisthenicsCards;
const datasetCategoryECards = flexibilityCards;
const datasetCategoryFCards = cardioCards;
const datasetCategoryGCards = targetCards;
const datasetCategoryHCards = equipmentCards;
const datasetCategoryICards = wheeledCards;
const datasetCategoryJCards = winterCards;
const datasetCategoryKCards = waterCards;
const datasetCategoryLCards = airCards;
const datasetCategoryMCards = danceCards;

// Generate card HTML
function generateCardHTML(card, index) {
    // 将卡片数据编码为 JSON 字符串存储在 data 属性中
    const cardData = JSON.stringify(card).replace(/"/g, '&quot;');
    return `
        <div class="generation-card" data-card-index="${index}" data-card-data="${cardData}">
            <div class="generation-card-image-wrapper">
                <video muted loop playsinline preload="none" data-video-src="${card.video}">
                    <source data-src="${card.video}" type="video/mp4">
                </video>
            </div>
            <div class="generation-card-content">
                <div class="generation-card-description">${card.prompt}</div>
                <div class="generation-card-prompt-image">
                    <img src="${card.image}" alt="Prompt image" loading="lazy">
                </div>
            </div>
        </div>
    `;
}

// 使用 Intersection Observer 来懒加载视频
function setupVideoLazyLoading(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // 检查容器是否可见
    const isContainerVisible = container.offsetParent !== null && 
                               container.style.display !== 'none' &&
                               window.getComputedStyle(container).display !== 'none';
    
    if (!isContainerVisible) {
        return; // 如果容器不可见，不设置观察器
    }
    
    const videos = container.querySelectorAll('video[data-video-src]');
    if (videos.length === 0) return;
    
    // 创建 Intersection Observer
    const videoObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            const video = entry.target;
            if (entry.isIntersecting) {
                // 视频进入视口，加载并播放
                const src = video.getAttribute('data-video-src');
                const source = video.querySelector('source[data-src]');
                if (source && source.getAttribute('data-src')) {
                    source.src = source.getAttribute('data-src');
                    source.removeAttribute('data-src');
                    video.load();
                    video.play().catch(e => {
                        // 静默处理播放错误（用户可能设置了自动播放限制）
                        console.log('Video autoplay prevented:', e);
                    });
                    video.removeAttribute('data-video-src');
                    videoObserver.unobserve(video);
                }
            } else {
                // 视频离开视口，暂停播放
                if (!video.paused) {
                    video.pause();
                }
            }
        });
    }, {
        rootMargin: '50px', // 提前50px开始加载
        threshold: 0.1
    });
    
    videos.forEach(video => {
        videoObserver.observe(video);
    });
    
    return videoObserver;
}

// 暂停容器中所有视频
function pauseAllVideosInContainer(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const videos = container.querySelectorAll('video');
    videos.forEach(video => {
        if (!video.paused) {
            video.pause();
        }
    });
}

// 恢复容器中可见视频的播放
function resumeVisibleVideosInContainer(containerId) {
    const container = document.getElementById(containerId);
    if (!container || container.style.display === 'none') return;
    
    // 重新设置未加载视频的懒加载
    setupVideoLazyLoading(containerId);
    
    // 对于已加载的视频，如果它们在视口中，恢复播放
    const loadedVideos = container.querySelectorAll('video:not([data-video-src])');
    if (loadedVideos.length > 0) {
        // 使用 Intersection Observer 来检测已加载的视频是否在视口中
        const loadedVideoObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                const video = entry.target;
                if (entry.isIntersecting) {
                    // 视频在视口中，尝试播放
                    if (video.paused && video.readyState >= 2) { // readyState >= 2 表示视频已加载足够数据
                        video.play().catch(e => {
                            // 静默处理播放错误
                            console.log('Video autoplay prevented:', e);
                        });
                    }
                } else {
                    // 视频离开视口，暂停播放
                    if (!video.paused) {
                        video.pause();
                    }
                }
            });
        }, {
            rootMargin: '50px',
            threshold: 0.1
        });
        
        loadedVideos.forEach(video => {
            loadedVideoObserver.observe(video);
            // 如果视频已经在视口中，立即尝试播放
            const rect = video.getBoundingClientRect();
            const isInViewport = rect.top < window.innerHeight + 50 && 
                                rect.bottom > -50 &&
                                rect.left < window.innerWidth + 50 && 
                                rect.right > -50;
            if (isInViewport && video.paused && video.readyState >= 2) {
                video.play().catch(e => {
                    console.log('Video autoplay prevented:', e);
                });
            }
        });
    }
}

// Initialize cards
function initCards(containerId, wrapperId, cards) {
    const wrapper = document.getElementById(wrapperId);
    if (!wrapper) return;
    
    wrapper.innerHTML = cards.map((card, index) => generateCardHTML(card, index)).join('');
    
    // 为每个卡片添加点击事件监听器
    const cardElements = wrapper.querySelectorAll('.generation-card');
    cardElements.forEach((cardElement, index) => {
        cardElement.addEventListener('click', () => {
            openCardModal(cards[index]);
        });
    });
    
    updateNavigationButtons(containerId);
    
    // 延迟设置视频懒加载，确保DOM已渲染
    setTimeout(() => {
        setupVideoLazyLoading(containerId);
    }, 100);
}

// Scroll cards
function scrollCards(containerId, direction) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const wrapper = container.querySelector('.cards-wrapper');
    if (!wrapper) return;
    
    // 计算卡片宽度（包括gap）
    const card = wrapper.querySelector('.generation-card');
    if (!card) return;
    
    const cardWidth = card.offsetWidth + 16; // card width + gap
    const scrollAmount = cardWidth * 2; // scroll 2 cards at a time
    
    wrapper.scrollBy({
        left: direction * scrollAmount,
        behavior: 'smooth'
    });
    
    // Update navigation buttons after scroll
    setTimeout(() => {
        updateNavigationButtons(containerId);
    }, 300);
}

// Update navigation button states
function updateNavigationButtons(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const wrapper = container.querySelector('.cards-wrapper');
    const prevBtn = container.querySelector('.prev');
    const nextBtn = container.querySelector('.next');
    
    if (!wrapper || !prevBtn || !nextBtn) return;
    
    const scrollLeft = wrapper.scrollLeft;
    const scrollWidth = wrapper.scrollWidth;
    const clientWidth = wrapper.clientWidth;
    
    // Enable/disable prev button
    if (scrollLeft <= 0) {
        prevBtn.classList.add('disabled');
    } else {
        prevBtn.classList.remove('disabled');
    }
    
    // Enable/disable next button
    if (scrollLeft + clientWidth >= scrollWidth - 1) {
        nextBtn.classList.add('disabled');
    } else {
        nextBtn.classList.remove('disabled');
    }
}

// Handle card click - open modal with card details
function openCardModal(card) {
    // 确保窗口系统已初始化
    if (typeof initWindow === 'function') {
        // 检查是否已经初始化
        if (!document.getElementById('fullscreen')) {
            initWindow();
        }
    }
    
    // 判断是否是 CoMoVi Dataset section 的 cards（通过 video 路径判断）
    const isDatasetCard = card.video && card.video.includes('/dataset/');
    const imagePromptTitle = isDatasetCard ? 'Inpainted Scene Image' : 'Image Prompt';
    
    // 生成模态框内容：左侧视频，右侧文本和图片
    const modalContent = `
        <div class="card-modal-container">
            <div class="card-modal-video">
                <video autoplay muted loop playsinline controls>
                    <source src="${card.video}" type="video/mp4">
                </video>
            </div>
            <div class="card-modal-info">
                <div class="card-modal-prompt">
                    <div class="card-modal-prompt-title">Text Prompt</div>
                    <div class="card-modal-prompt-text">${card.prompt}</div>
                </div>
                <div class="card-modal-prompt-image-wrapper">
                    <div class="card-modal-prompt-title">${imagePromptTitle}</div>
                    <div class="card-modal-prompt-image">
                        <img src="${card.image}" alt="Prompt image">
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 使用全局的 openWindow 函数
    if (typeof openWindow === 'function') {
        openWindow(modalContent);
    } else {
        console.error('openWindow function not found. Make sure window.js is loaded.');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // 初始化窗口系统
    if (typeof initWindow === 'function') {
        initWindow();
    }
    
    // Initialize text to asset cards
    initCards('text2asset-cards', 'text2asset-wrapper', text2assetCards);
    
    // Add scroll event listener to update navigation buttons
    const text2assetWrapper = document.getElementById('text2asset-wrapper');
    if (text2assetWrapper) {
        text2assetWrapper.addEventListener('scroll', () => {
            updateNavigationButtons('text2asset-cards');
        });
    }
    
    // Add click event listeners to navigation buttons
    const prevBtn = document.getElementById('text2asset-prev');
    const nextBtn = document.getElementById('text2asset-next');
    
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            scrollCards('text2asset-cards', -1);
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            scrollCards('text2asset-cards', 1);
        });
    }
    
    // Initialize dataset category cards
    const categories = [
        { id: 'a', containerId: 'dataset-category-a-wrapper', wrapperId: 'dataset-category-a-cards-wrapper', cards: datasetCategoryACards },
        { id: 'b', containerId: 'dataset-category-b-wrapper', wrapperId: 'dataset-category-b-cards-wrapper', cards: datasetCategoryBCards },
        { id: 'c', containerId: 'dataset-category-c-wrapper', wrapperId: 'dataset-category-c-cards-wrapper', cards: datasetCategoryCCards },
        { id: 'd', containerId: 'dataset-category-d-wrapper', wrapperId: 'dataset-category-d-cards-wrapper', cards: datasetCategoryDCards },
        { id: 'e', containerId: 'dataset-category-e-wrapper', wrapperId: 'dataset-category-e-cards-wrapper', cards: datasetCategoryECards },
        { id: 'f', containerId: 'dataset-category-f-wrapper', wrapperId: 'dataset-category-f-cards-wrapper', cards: datasetCategoryFCards },
        { id: 'g', containerId: 'dataset-category-g-wrapper', wrapperId: 'dataset-category-g-cards-wrapper', cards: datasetCategoryGCards },
        { id: 'h', containerId: 'dataset-category-h-wrapper', wrapperId: 'dataset-category-h-cards-wrapper', cards: datasetCategoryHCards },
        { id: 'i', containerId: 'dataset-category-i-wrapper', wrapperId: 'dataset-category-i-cards-wrapper', cards: datasetCategoryICards },
        { id: 'j', containerId: 'dataset-category-j-wrapper', wrapperId: 'dataset-category-j-cards-wrapper', cards: datasetCategoryJCards },
        { id: 'k', containerId: 'dataset-category-k-wrapper', wrapperId: 'dataset-category-k-cards-wrapper', cards: datasetCategoryKCards },
        { id: 'l', containerId: 'dataset-category-l-wrapper', wrapperId: 'dataset-category-l-cards-wrapper', cards: datasetCategoryLCards },
        { id: 'm', containerId: 'dataset-category-m-wrapper', wrapperId: 'dataset-category-m-cards-wrapper', cards: datasetCategoryMCards }
    ];

    categories.forEach(category => {
        // Initialize cards
        initCards(category.containerId, category.wrapperId, category.cards);
        
        // Add scroll event listener
        const wrapper = document.getElementById(category.wrapperId);
        if (wrapper) {
            wrapper.addEventListener('scroll', () => {
                updateNavigationButtons(category.containerId);
            });
        }
        
        // Add click event listeners to navigation buttons
        const prevBtn = document.getElementById(`dataset-category-${category.id}-prev`);
        const nextBtn = document.getElementById(`dataset-category-${category.id}-next`);
        
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                scrollCards(category.containerId, -1);
            });
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                scrollCards(category.containerId, 1);
            });
        }
    });
    
    // Handle window resize
    window.addEventListener('resize', () => {
        updateNavigationButtons('text2asset-cards');
        categories.forEach(category => {
            updateNavigationButtons(category.containerId);
        });
    });
});

