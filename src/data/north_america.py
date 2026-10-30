# -*- coding: utf-8 -*-
"""North American additions (not in the book). Every entry must cite sources (see CLAUDE.md)."""

NA_GROUP = dict(key="extra", name="北美补充（原书未收录）", short="北美",
                      note="原书以欧洲物种为主。这一组整理自北美的真菌学资料（大学博物馆、真菌学会、州政府自然资源部门、同行评审论文等），每种的来源附在详情页底部。季节因地区和海拔差别很大，仅供参考。")
_MATSUTAKE = dict(
    zh="松茸", en="Matsutake / Pine mushroom", latin="Tricholoma matsutake",
    latin2="北美西部：T. murrillianum；北美东部：T. magnivelare",
    page=None, season="秋–初冬", months=[9, 10, 11, 12],
    feat="菌盖 6–20 cm，幼时白色、边缘内卷，长大后出现黄褐至褐色斑块和鳞片；菌褶白至奶油色、密，弯生或窄直生；幼时有棉絮状菌幕，破裂后在柄上留下下垂的<b>菌环</b>；<b>没有菌托</b>；菌柄粗壮致密，最宽处在菌环附近，向下渐细。<b>最关键的是气味</b>：辛香、像肉桂，常被形容为“肉桂糖混着脏袜子”。",
    hab="针叶林地面的厚落叶层中，常深埋在针叶下只顶起一个小土包。亚洲与赤松等松树共生；北美西部见于松、花旗松、西部铁杉、云杉林下",
    spore="白色",
    kitchen="上品，香气是精华。不要水洗，擦净或刮去泥土即可；适合炭烤、清汤、松茸饭等简单做法",
    warn="<b>北美西部：史密斯鹅膏</b>（Amanita smithiana）与松茸同林生长、外形相近，误食可致肾衰竭。四点区分：①松茸有辛香味，史密斯鹅膏气味淡或难闻；②松茸柄致密、用拇指用力按不碎，史密斯鹅膏的柄会碎裂；③松茸柄最宽在地面以上，史密斯鹅膏在地面或地下最宽、向下收成萝卜状；④松茸的柄摇不下来，史密斯鹅膏轻摇常整根脱落。",
    group="extra", flags=["上品", "非原书"], region="北美西部 · 亚洲",
    extra=[
        "<b>别耙地。</b>耙开落叶层找松茸会破坏菌丝，研究显示会降低之后几年的产量。",
        "<b>先查许可。</b>美国国家森林常把松茸与其他野菌分开管理：有的林区需要专门的松茸许可，有的完全不允许个人免费采集。出发前查当地林区的最新规定。",
        "<b>其他相似种：</b>假松茸 T. caligatum（可食，但常带苦味、香气弱）；Catathelasma 属（可食，柄上有不易看清的双层菌环）；T. focale（有腐败面粉味）。",
    ],
    links=[("iNaturalist：北美西部松茸", "https://www.inaturalist.org/taxa/search?q=Tricholoma+murrillianum"),
           ("iNaturalist：亚洲松茸", "https://www.inaturalist.org/taxa/search?q=Tricholoma+matsutake")],
    sources=[
        ("UBC Beaty Museum · Mushrooms Up!：Tricholoma murrillianum", "https://explore.beatymuseum.ubc.ca/mushroomsup/T_murrillianum.html"),
        ("UBC Beaty Museum · Mushrooms Up!：Amanita smithiana", "https://explore.beatymuseum.ubc.ca/mushroomsup/A_smithiana.html"),
        ("Kuo, M.（2023）MushroomExpert：Tricholoma murrillianum", "https://mushroomexpert.com/tricholoma_murrillianum.html"),
        ("Trudell et al.（2017）North American matsutake: names clarified, Mycologia 109(3)", "https://doi.org/10.1080/00275514.2017.1326780"),
        ("MykoWeb · California Fungi：Tricholoma murrillianum", "https://www.mykoweb.com/CAF/species/Tricholoma_murrillianum.html"),
        ("USDA Forest Service：Fremont-Winema 国家森林许可说明", "https://www.fs.usda.gov/main/fremont-winema/passes-permits"),
        ("Mushroom Appreciation：American Matsutake（采集与可持续）", "https://mushroom-appreciation.com/american-matsutake.html"),
    ],
)

NA_TOXIC = [dict(
    zh="史密斯鹅膏", en="Smith's amanita", latin="Amanita smithiana", level="有毒", tag="伤肾",
    feat="白至浅棕色菌盖 5–15 cm，常带白色疣；菌褶白、密；菌柄白，大部分埋在土里，在地面或地下最宽，向下收成萝卜或鱼雷状；气味起初温和，之后变得难闻（像变质的火腿）；孢子印白色。<br><b>中毒过程：</b>食后 20 分钟到 1 天内出现腹痛、腹泻、呕吐；2–6 天后可发生肾衰竭，部分患者需要住院透析。少到 2–3 朵就可能致病。",
    conf="松茸（北美西部常与松茸长在同一片林子里）",
    sources=[("UBC Beaty Museum · Mushrooms Up!", "https://explore.beatymuseum.ubc.ca/mushroomsup/A_smithiana.html"),
             ("Warden & Benjamin（1998）Acad Emerg Med 病例报告", "https://pubmed.ncbi.nlm.nih.gov/9715243/"),
             ("NAMA 北美中毒报告 2015–2016", "https://namyco.org/wp-content/uploads/2023/08/Mushroom_Poisoning_in_North_America_2015-2016.pdf")],
)]

UBC = "https://explore.beatymuseum.ubc.ca/mushroomsup/"
NA_SPECIES = [
 _MATSUTAKE,
 dict(zh="太平洋金鸡油菌", en="Pacific golden chanterelle", latin="Cantharellus formosus", region="西北太平洋",
      page=None, season="夏末–秋", months=[8, 9, 10, 11],
      feat="菌盖 2–14 cm，亮黄至黄橙色、干燥，边缘内卷，长大后呈漏斗状；下面是<b>钝圆的假褶（棱脊）</b>，厚而疏、会分叉并有横脉，延生到柄上，颜色常比菌盖浅（橙黄到带粉的橙色）；碰伤先变黄、后变赭色；菌柄与盖同色或略浅，无菌环、无菌托。气味温和",
      hab="地上，与花旗松、西部铁杉、北美云杉等针叶树共生；广泛分布于不列颠哥伦比亚和西北太平洋",
      spore="浅黄色", kitchen="上品，生尝略带果香或微辣；煎炒、配奶油，做法同欧洲鸡油菌",
      warn="<b>发光类脐菇</b>：长在木头上、密集成簇，是刀片状真菌褶（有毒）；<b>假鸡油菌</b>：褶更薄、更橙、反复分叉；<b>毛钉菇</b>（Turbinellus floccosus）：喇叭更深、盖上有鳞片，可能引起肠胃不适",
      group="extra", flags=["上品", "非原书"],
      extra=["<b>白鸡油菌</b>（C. subalbidus）：同一地区的近亲，通体奶白色，同样可食。"],
      sources=[("UBC Beaty Museum · Mushrooms Up!：Cantharellus formosus", UBC + "C_formosus.html")]),
 dict(zh="春王牛肝菌", en="Spring king bolete", latin="Boletus rex-veris", region="北美西部山地",
      page=None, season="晚春", months=[5, 6],
      feat="菌盖 9–18 cm，湿时黏；幼时近白色，之后带银色光泽的粉褐，最后变暗橄榄褐，手摸过的地方会变深；孔口幼时白→奶黄→黄橄榄，<b>碰伤不变色</b>；菌柄粗 2–6 cm，基部略膨大，<b>上半部有明显网纹</b>；肉白，切开不变色。常小簇生长",
      hab="山地针叶林（尤其松、冷杉）下，常见于土路和小径旁，有时半埋在土或落叶下。通常在 5 月底到 6 月初出现，常和羊肚菌季节的尾巴重叠",
      spore="橄榄褐", kitchen="上品，口感紧实；纽扣期最好，成熟的多拿来晒干",
      warn="与美味牛肝菌的区别：后者多在夏末秋季出、很少成簇、幼盖没有粉色调。<b>B. regius</b> 孔口亮黄、碰伤变蓝；<b>B. rubripes</b> 柄无网纹、孔口碰伤变蓝",
      group="extra", flags=["上品", "非原书"],
      sources=[("MykoWeb · California Fungi：Boletus rex-veris", "https://www.mykoweb.com/CAF/species/Boletus_rex-veris.html")]),
 dict(zh="赞美牛肝菌", en="Admirable bolete", latin="Aureoboletus mirabilis", region="西北太平洋",
      page=None, season="夏末–秋", months=[8, 9, 10, 11],
      feat="菌盖深酒红至紫褐色、<b>天鹅绒质</b>（幼时略黏）；<b>孔口亮黄</b>；菌柄与盖同色但较浅。<b>常从长满苔藓的铁杉腐木或树桩上长出</b>，这在牛肝菌里很少见（其实是与铁杉根共生）",
      hab="从北加州到阿拉斯加的太平洋沿岸铁杉林、喀斯喀特山脉；偶见花旗松、红雪松",
      spore="橄榄褐", kitchen="可食；肉多汁、很难保存，宜鲜吃。风味评价不一，有人觉得平淡",
      warn=None, group="extra", flags=["非原书"],
      sources=[("Wikipedia：Aureoboletus mirabilis", "https://en.wikipedia.org/wiki/Aureoboletus_mirabilis"),
               ("MykoWeb · California Fungi：Aureoboletus mirabilis", "https://www.mykoweb.com/CAF/species/Aureoboletus_mirabilis.html"),
               ("IUCN 红色名录评估：Aureoboletus mirabilis", "https://redlist.info/iucn/species_view/811404/")]),
 dict(zh="龙虾菌", en="Lobster mushroom", latin="Hypomyces lactifluorum", region="全北美",
      page=None, season="夏–秋", months=[7, 8, 9, 10],
      feat="不是一种独立的蘑菇：一种寄生菌把白色的红菇或乳菇整个包裹起来。外层<b>亮橙至橙红、硬、布满细小颗粒</b>，老了变紫红；形状被扭曲，看不出原来的菌褶；切开内部白色紧实",
      hab="林地地面，常在针叶林中；宿主多为短柄红菇（Russula brevipes），有时是辣乳菇类",
      spore="白色", kitchen="可食，口感紧实、带一点海鲜感；挑年轻、颜色偏浅、内部白而紧实的；切掉未被包裹、正在腐烂的部分",
      warn="宿主被完全包裹后就无法辨认。理论上它可能寄生在有毒的宿主上，目前未见确认的中毒报告；只采典型的亮橙、坚硬、表面颗粒状的个体。白色、粉色、黄色的“霉”可能是别的东西",
      group="extra", flags=["非原书"],
      sources=[("Kuo, M. MushroomExpert：Hypomyces lactifluorum", "https://www.mushroomexpert.com/hypomyces_lactifluorum.html"),
               ("UBC Beaty Museum · Mushrooms Up!：Lobster mushroom", UBC + "H_lactifluorum.html"),
               ("Tom Volk's Fungus of the Month（威斯康星大学）", "https://botit.botany.wisc.edu/toms_fungi/aug2001.html"),
               ("Missouri Department of Conservation：Lobster Mushroom", "https://mdc.mo.gov/discover-nature/field-guide/lobster-mushroom")]),
 dict(zh="灰树花（舞茸）", en="Hen of the woods / Maitake", latin="Grifola frondosa", region="北美东部",
      page=None, season="秋", months=[9, 10, 11],
      feat="一大团玫瑰花状，由许多<b>灰褐色扇形或匙形小盖</b>从一个多分枝的主干长出，小盖薄（3–6 mm）；下面是奶白色细孔，沿柄下延；肉白；<b>碰伤不变黑</b>",
      hab="栎树（偶尔枫树）基部或树桩旁，是树根的弱寄生菌，常年复一年长在同一棵树下。北美只见于落基山脉以东",
      spore="白色", kitchen="上品；烤、煎、炖都好。老的会发苦、变柴。新鲜的用纸袋保存，不要放塑料袋",
      warn="<b>黑变多孔菌</b>（Meripilus sumstinei）：小盖更厚（12–19 mm）、碰伤变黑，可食但较差；<b>伯氏邦氏孔菌</b>（Bondarzewia berkeleyi）也常被误认，同样安全",
      group="extra", flags=["上品", "非原书"],
      sources=[("Midwest Mycology：Grifola frondosa", "https://midwestmycology.org/grifola-frondosa/"),
               ("Missouri Department of Conservation：Hen of the Woods", "https://mdc.mo.gov/species/hen-woods-maitake"),
               ("AmericanMushrooms.com：Hen of the Woods", "https://americanmushrooms.com/edibles1.htm")]),
 dict(zh="猴头菇类", en="Lion's mane / Bear's head", latin="Hericium spp.", region="全北美",
      page=None, season="夏末–冬", months=[8, 9, 10, 11, 12, 1],
      feat="白色，<b>没有菌盖和菌褶，整团是下垂的柔软菌刺</b>。猴头菇（H. erinaceus）是一整团不分枝、刺长 1–5 cm；熊头（H. americanum）和针叶树珊瑚猴头（H. abietis）是分枝结构，刺成簇或成排。老了发黄",
      hab="枯木或活树伤口上。猴头菇和熊头长在阔叶树（栎、枫、山毛榉等）；H. abietis 长在针叶树（冷杉、花旗松）的枯木上",
      spore="白色", kitchen="上品，趁刺还是白色到奶油色时采；发黄后容易发酸或有怪味。撕成块煎，口感像蟹肉",
      warn=None, group="extra", flags=["上品", "非原书"],
      extra=["没有已知的有毒近似种，难点只在于分清是哪一种猴头。和所有野菌一样，第一次吃少量、彻底煮熟。"],
      links=[("iNaturalist：猴头菇属", "https://www.inaturalist.org/taxa/search?q=Hericium")],
      sources=[("MykoWeb · California Fungi：Hericium erinaceus", "https://mykoweb.com/CAF/species/Hericium_erinaceus.html"),
               ("Midwest Mycology：Hericium", "https://midwestmycology.org/hericium-erinaceus/"),
               ("Wikipedia：Hericium erinaceus", "https://en.wikipedia.org/wiki/Hericium_erinaceus")]),
]

NA_TOXIC += [
 dict(zh="北美毁灭天使", en="Destroying angels", latin="Amanita bisporigera / A. ocreata", level="致命", tag="伤肝",
      feat="<b>通体白色</b>，有菌环，基部有<b>袋状菌托</b>（常埋在土里，必须挖出来看）；孢子印白色。东部的 A. bisporigera 与栎树等阔叶树共生，夏秋出现；西部的 A. ocreata 见于加州和西北太平洋，也与栎树共生，体型通常更粗壮。含鹅膏毒素，没有特效解毒剂。北美野外指南里写作 A. virosa 或 A. verna 的，多半就是这两种",
      conf="白色蘑菇属（如野蘑菇）、马勃幼体（毁灭天使的“蛋”纵切后能看到菌盖和菌褶轮廓）",
      sources=[("Kuo, M. MushroomExpert：Amanita bisporigera", "https://www.mushroomexpert.com/amanita_bisporigera.html"),
               ("UC Irvine 自然史：Amanita ocreata", "https://nathistoc.bio.uci.edu/Fungi/Amanita%20ocreata/index.htm")]),
 dict(zh="纹缘盔孢伞", en="Deadly galerina", latin="Galerina marginata", level="致命", tag="伤肝",
      feat="小型褐色菌：菌盖 1.5–5 cm，赭褐至橙褐、边缘较浅；菌褶褐色；<b>菌柄细（通常不到 0.6 cm）</b>，上部有小菌环（老了常脱落）；<b>孢子印锈褐色</b>；长在腐木或木屑上，有时看似从地上长出（下面埋着木头）。含鹅膏毒素，<b>煮不坏</b>：6–10 小时出现肠胃症状，约 72 小时可发生肝衰竭",
      conf="蜜环菌（孢子印白色、柄更粗）、野生金针菇（孢子印白色）、长在木屑上的裸盖菇",
      sources=[("UBC Beaty Museum · Mushrooms Up!：Galerina marginata", UBC + "G_marginata.html")]),
 dict(zh="发光类脐菇", en="Jack-o'-lantern", latin="Omphalotus illudens / O. olivascens", level="有毒",
      feat="橙色，<b>大团密集簇生在木头上</b>（或埋在地下的树根上，看起来像长在地上）；<b>真菌褶，刀片状、不分叉、延生</b>；西部的 O. olivascens 常带橄榄色调。新鲜菌褶在黑暗中有时会微弱发光。吃了会严重呕吐腹泻好几天",
      conf="鸡油菌：鸡油菌长在地上、很少密集成簇，下面是钝圆的棱脊，不是刀片状真菌褶",
      sources=[("Kuo, M. MushroomExpert：Omphalotus illudens", "https://mushroomexpert.com/omphalotus_illudens.html"),
               ("Missouri Department of Conservation：Jack-o'-lantern", "https://mdc.mo.gov/node/249263"),
               ("Bay Area Mycological Society：Omphalotus olivascens", "https://bayareamushrooms.org/mushroommonth/jackolantern.html")]),
 dict(zh="大青褶伞", en="Green-spored parasol", latin="Chlorophyllum molybdites", level="有毒",
      feat="<b>北美最常被误食的毒菌</b>。大型，白色菌盖带褐色鳞片，常在草坪、公园形成蘑菇圈；菌褶成熟后变灰绿；<b>孢子印绿色</b>（唯一绿孢子印的大型菌）；柄上没有蛇皮纹。食后 1–3 小时出现剧烈呕吐腹泻。东部和南部常见，西北太平洋少见",
      conf="高大环柄菇、粗鳞青褶伞（孢子印都是白色）",
      sources=[("Wikipedia：Chlorophyllum molybdites", "https://en.wikipedia.org/wiki/Chlorophyllum_molybdites"),
               ("Bay Area Mycological Society：Other Toxic Mushrooms", "https://bayareamushrooms.org/poisonings/non_fatal.html")]),
]

# ---- Pacific Northwest toxic additions (2026-10) ----
INAT_PNW = "https://www.inaturalist.org/observations?place_id=7085,46,10&quality_grade=research&taxon_id="
NA_TOXIC += [
 dict(zh="致命小环柄菇", en="Deadly parasol", latin="Lepiota subincarnata", level="致命", tag="伤肝",
      feat="小型伞菌：菌盖 1.5–6 cm，幼时整个裹着一层粉褐色绒毛，展开后裂成<b>一圈圈粉褐色鳞片、露出白底</b>，中央仍留一团绒毛；菌褶白色、离生；菌柄细（0.15–0.7 cm），下部约四分之三有与盖同色的<b>环带状绒毛</b>，上方只有一圈不明显的绒质环痕；没有菌托；孢子印白色；气味不明显，或带甜的果香。长在城市草坪、花园、覆盖木屑上，也见于林下。不列颠哥伦比亚（大温哥华、温哥华岛南部）、华盛顿、俄勒冈都有记录。<br><b>中毒过程：</b>含鹅膏毒素。6–12 小时（最长 36 小时）后腹痛、呕吐、水样腹泻，约一天后好转；约 72 小时后肠胃症状复发，并出现肝衰竭迹象。<br><b>【编者注】</b>1988 年大温哥华地区一名男子把自家草坪上的这种菇当成仙环菇，做进早餐煎蛋卷，中毒身亡。凡是菌褶白色离生、菌盖粉褐/橙褐/褐色的小型伞菌，都可能含鹅膏毒素，一律不要吃。",
      conf="硬柄小皮伞（仙环菇）：同样长在草坪上，但仙环菇菌盖光滑、浅褐，菌柄光滑、没有环带",
      sources=[("UBC Beaty Museum · Mushrooms Up!：Lepiota subincarnata", UBC + "L_subincarnata.html"),
               ("iNaturalist：BC / 华盛顿 / 俄勒冈的研究级观察", INAT_PNW + "382931")]),
 dict(zh="皱盖锥盖伞", en="Deadly conocybe", latin="Pholiotina rugosa", level="致命", tag="伤肝",
      feat="不起眼的“小褐菇”：菌盖 1–2.5 cm，钝锥形到近平展，黄褐至暗茶褐色，湿时边缘有条纹，干后褪成浅米褐；菌褶米色→浅褐→锈褐；菌柄细（1–3 mm）、易断、中空，上部有<b>膜质菌环，环的上面有纵沟纹</b>，常被孢子染成锈褐色，老了会萎缩甚至消失；<b>孢子印锈褐色</b>。散生或小群生在土上，常靠近木屑和枯枝。旧名 Conocybe filaris。含鹅膏毒素。<br><b>【编者注】</b>iNaturalist 上不列颠哥伦比亚、华盛顿、俄勒冈都有经鉴定的记录。这类小褐菇只凭肉眼很难认到种，一律不要采来吃。",
      conf="纹缘盔孢伞等其他小褐菇（同为锈褐色孢子印，同样含鹅膏毒素）",
      sources=[("MykoWeb · California Fungi：Pholiotina rugosa", "https://www.mykoweb.com/CAF/species/Pholiotina_rugosa.html"),
               ("iNaturalist：BC / 华盛顿 / 俄勒冈的研究级观察", INAT_PNW + "877494")]),
 dict(zh="簇生垂幕菇", en="Sulphur tuft", latin="Hypholoma fasciculare", level="有毒", tag="肠胃",
      feat="菌盖 1–6 cm（偶达 10 cm），<b>硫黄色至黄橙、黄褐色</b>，中央较深，光滑不黏；幼时边缘内卷，常挂着蛛网状菌幕残片，被孢子染成紫黑色；<b>菌褶幼时黄色带绿调</b>，成熟后变暗灰褐、带紫色；菌柄 3–7 cm、细，黄至黄褐；<b>孢子印紫黑色</b>；味极苦。<b>大丛密集地长在倒木、树桩和木屑上</b>，阔叶树、针叶树都长，常铺满整根木头。北半球温带普遍，西北太平洋很常见。<br><b>中毒过程：</b>食后 5–10 小时出现恶心、呕吐和剧烈腹泻。",
      conf="蜜环菌（孢子印白色、菌盖有鳞片、幼时柄上有绵质菌环）；烟色垂幕菇 H. capnoides（只长在针叶树木头上，幼褶烟灰色，可食，但很容易与致命的纹缘盔孢伞混淆）",
      sources=[("UBC Beaty Museum · Mushrooms Up!：Hypholoma fasciculare", UBC + "H_fasciculare.html")]),
 dict(zh="毒蝇鹅膏", en="Fly agaric", latin="Amanita muscaria", level="有毒", tag="神经",
      feat="典型的“童话蘑菇”。菌盖 5–20 cm，多为鲜红或猩红、向边缘褪成橙黄，也有浅黄、橙、褐色的类型；盖上散布白至奶黄色的<b>金字塔形疣</b>（像碎奶酪，雨一冲就掉），边缘有放射状沟纹；菌褶白、密、离生；菌柄白，基部膨大，上部挂着大而下垂的<b>裙状菌环</b>；柄基的菌托<b>碎成几圈松散的棉絮状环带</b>，不是完整的袋状；孢子印白色。与栎、桦等阔叶树和针叶树共生，城市里也很常见，夏末到秋季出现。西北美洲的毒蝇鹅膏其实至少包括三个种。<br><b>中毒：</b>含神经毒素，引起醉酒样症状和谵妄；对猫狗也有毒。",
      conf="橙盖鹅膏（凯撒蘑菇，原书 p52）：凯撒蘑菇菌褶黄色，毒蝇鹅膏菌褶白色",
      sources=[("UBC Beaty Museum · Mushrooms Up!：Amanita muscaria", UBC + "A_muscaria.html")]),
 dict(zh="波地钟菌", en="Early false morel", latin="Verpa bohemica", level="有毒", tag="因人而异",
      feat="早春的“假羊肚菌”，有些地方被误叫作“早羊肚菌”：比羊肚菌出得早，又和羊肚菌季节重叠。菌帽 2–4 cm 高，钟形或近锥形，<b>表面是纵向皱褶</b>（老了也可能像有凹坑），黄褐至褐色；<b>菌帽只在顶端连着菌柄，下缘整圈悬空</b>，像套在手指上的顶针；菌柄 8–22 cm，奶白至暗黄，常有一圈圈细小鳞屑；纵切后菌柄里<b>塞着棉花糖似的白色絮状组织</b>。早春长在阔叶树下，有时在针叶树下。<br><b>毒性：</b>能不能吃一直有争议。北美很多图鉴把它列为可疑或有毒，美国 FDA 把它和鹿花菌一起归为有毒的假羊肚菌。部分人吃后出现严重肠胃不适和暂时性的协调障碍（走路不稳），吃得多或连续几天吃时更常见。2020 年的一篇毒理学综述建议把它视为不可食。",
      conf="半离羊肚菌：它的菌帽只有下半部与柄分离，上半部连在柄上；纵切后从头到柄整个中空，没有絮状组织",
      sources=[("Kuo, M.（2019）MushroomExpert：Verpa bohemica", "https://www.mushroomexpert.com/verpa_bohemica.html"),
               ("Lagrange & Vernoux（2020）Toxins 12(8):482，假羊肚菌与羊肚菌的肼类毒素综述", "https://doi.org/10.3390/toxins12080482"),
               ("iNaturalist：BC / 华盛顿 / 俄勒冈的研究级观察", INAT_PNW + "126131")]),
]

# Editor's notes appended to book toxic entries (keyed by Latin name), with their sources
NA_POISON_NOTES = {
 "Amanita phalloides": dict(
     note="<b>【编者注】在西北太平洋正在扩散。</b>原产欧洲，随引种的鹅耳枥、欧洲栎、榛等树木传入；温哥华、维多利亚、西雅图的市区和郊区都有记录，常长在草坪和行道树下，在 BC 省还在向北、向原生林扩散。BC 省自 1997 年首次发现以来已有三起严重中毒：2003 年维多利亚一名男子把前院里的幼菇当成马勃；2008 年兰里一名女子把它当成<b>草菇</b>；2016 年维多利亚市中心一名三岁儿童误食后死亡。<b>幼菇很像草菇，但西北太平洋野外基本没有草菇</b>；草菇孢子印粉红，毒鹅膏孢子印白色。马勃要纵切检查：真马勃里面是均匀的白色，毒鹅膏的“蛋”里能看到菌盖和菌褶的轮廓。",
     sources=[("UBC Beaty Museum · Mushrooms Up!：Amanita phalloides（BC 省中毒案例）", UBC + "A_phalloides.html")]),
}

# ---- Pacific Northwest edible additions (2026-10) ----
NA_SPECIES += [
 dict(zh="虾味红菇", en="Shrimp russula", latin="Russula xerampelina", region="西北太平洋 · 北温带",
      page=None, season="夏末–秋", months=[8, 9, 10, 11],
      feat="菌盖 5–15 cm（偶达 20 cm），<b>酒红至紫色</b>，也有红褐、偶尔黄褐色的，中央常凹陷、颜色最深，湿时微黏；菌褶奶油色，老了变赭黄，碰伤处变褐，质脆，少数分叉；菌柄白色常带粉红晕，<b>手摸或刮过的地方会慢慢变褐</b>，质脆、一掰就断；没有菌环和菌托；<b>有鱼或虾的气味</b>，成熟后更明显；味道温和",
      hab="针叶林或混交林地上，加州沿海尤其多见于花旗松下。广义的虾味红菇遍布北半球温带和北方林；西北太平洋的可能其实是另一个种，西部还有气味相同的近似种 R. viridofusca",
      spore="奶油色", kitchen="多数人可食。没有已知的毒素，但偶有体质特殊的人吃后不适；第一次吃先少量",
      warn="<b>辛辣的红菇</b>：味道辣的红菇可能引起肠胃中毒。<b>会变黑的红菇类</b>（菌盖灰、褐或黑，碰伤后变红或变黑）：亚洲的亚稀褶红菇（R. subnigricans）在日本已致 8 人死亡，西北太平洋虽然没有记录，但近缘种也可能有毒，一律不要吃",
      group="extra", flags=["非原书"],
      extra=["<b>【编者注】</b>红菇属很难认到种。只采同时符合这几点的：酒红紫色菌盖、奶油至黄色菌褶、菌柄碰过后慢慢变褐、有鱼虾味且味道温和。"],
      sources=[("UBC Beaty Museum · Mushrooms Up!：Russula xerampelina", UBC + "R_xerampelina.html"),
               ("MykoWeb · California Fungi：Russula xerampelina", "https://www.mykoweb.com/CAF/species/Russula_xerampelina.html"),
               ("Kuo, M. MushroomExpert：Russula xerampelina", "https://www.mushroomexpert.com/russula_xerampelina.html")]),
]

NA_TOXIC += [
 dict(zh="贝形圆孢侧耳（天使之翼）", en="Angel wings", latin="Pleurocybella porrigens", level="有毒", tag="已有致死报告",
      feat="纯白至象牙色、<b>薄而半透明</b>的扇形、舌形或耳形菌盖，1.5–10 cm，几乎没有柄，向基部渐窄；菌褶白、较密、窄，覆盖整个背面；孢子印白色；气味不明显。成群成丛长在<b>针叶树</b>（常是西部铁杉）的倒木和树桩上，见于沿海针叶林，从阿拉斯加到北加州都有。<br><b>中毒：</b>它原本在日本被当作季节美味。2004 年日本有 59 人吃后出现脑部损害症状，19 人死亡；患者平均约 69 岁，多数原本就有肾病。症状在吃后 1–31 天出现：行动困难甚至瘫痪、肌肉痉挛，之后抽搐。毒素至今不明，证据也是间接的，但 UBC 资料建议西北太平洋的天使之翼一律不要吃，有肾病的人尤其不要。",
      conf="糙皮侧耳（平菇）：平菇多长在阔叶树上，很少纯白，肉更厚；天使之翼只长在针叶树木头上",
      sources=[("UBC Beaty Museum · Mushrooms Up!：Pleurocybella porrigens", UBC + "P_porrigens.html")]),
]

# Editor's notes added to book species (keyed by Latin name): extra lines, optional warn, sources
NA_SPECIES_NOTES = {
 "Morchella esculenta": dict(
     extra=["<b>【编者注】北美的羊肚菌和欧洲的不是同一批种。</b>西北太平洋常见三类："
            "①<b>火烧迹地羊肚菌</b>（如 M. sextelata）：针叶林火灾后的第一个春夏大量出现，之后几年逐渐减少；"
            "②<b>“天然林”羊肚菌</b> M. snyderi：长在没有烧过的林子里，棱起初偏黄、后来变黑，柄成熟后常有深沟和凹坑；"
            "③<b>园林羊肚菌</b> M. importuna：长在城市花坛、树皮覆盖物上，冬末早春出现。"
            "这些种外形相近，有的只能靠 DNA 区分，做法和注意事项都一样：<b>必须彻底煮熟</b>。去火烧迹地采之前，先查当地是否需要许可、是否封林（因地区而异）。"],
     sources=[("Kuo, M. MushroomExpert：Morchella sextelata（火烧迹地）", "https://www.mushroomexpert.com/morchella_sextelata.html"),
              ("Kuo, M. MushroomExpert：Morchella snyderi", "https://www.mushroomexpert.com/morchella_snyderi.html"),
              ("Kuo, M. MushroomExpert：Morchella importuna（园林）", "https://www.mushroomexpert.com/morchella_importuna.html")]),
 "Sparassis crispa": dict(
     extra=["<b>【编者注】西北太平洋的是另一个种：西部绣球菌（S. radicata）。</b>旧图鉴常把它也叫作 S. crispa，DNA 研究显示 S. crispa 其实是欧洲种。"
            "西部绣球菌长在花旗松、北美云杉的根部或枯干基部（加州沿海也见于松树下），一丛 10–50 cm，像一盘奶油色的扁面条，可以连续几年在同一处长出。"
            "可食、口感脆，但有少数人吃后肠胃不适：彻底煮熟，第一次只吃一两勺。"
            "别和珊瑚菌混：珊瑚菌从地上长出，分枝是直立的圆柱形，很多有毒。"],
     sources=[("UBC Beaty Museum · Mushrooms Up!：Sparassis radicata", UBC + "S_radicata.html"),
              ("Hughes et al.（2014）The Sparassis crispa complex, Mycological Progress 13", "https://doi.org/10.1007/s11557-013-0927-1")]),
 "Laetiporus sulphureus": dict(
     extra=["<b>【编者注】西北太平洋针叶树上的是针叶硫磺菌（L. conifericola）</b>，常长在花旗松、北美云杉的活树或枯木上；西部阔叶树（栎、桉）上的是另一个种 L. gilbertsonii。"
            "有人吃硫磺菌后出现肠胃不适、皮疹、发烧、潮红或头痛；曾有一名女性吃了几口后 19 小时休克死亡，同桌的人都没事，可能是个人体质。"
            "只吃新鲜、嫩的边缘部分，彻底煮熟，第一次只吃一勺。"],
     sources=[("UBC Beaty Museum · Mushrooms Up!：Laetiporus conifericola", UBC + "L_conifericola.html")]),
 "Pleurotus ostreatus": dict(
     warn="<b>【编者注】贝形圆孢侧耳（天使之翼）</b>：纯白、薄、长在针叶树木头上，日本曾有致死报告",
     sources=[("UBC Beaty Museum · Mushrooms Up!：Pleurocybella porrigens", UBC + "P_porrigens.html")]),
}
