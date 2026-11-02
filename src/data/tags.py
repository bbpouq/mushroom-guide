# -*- coding: utf-8 -*-
"""Identification tags used by the feature finder. Keyed by the Chinese name (zh) of each edible and toxic species."""

# ---------- identification tags for the feature finder ----------
# Schema v2 (2026-11 audit, docs/SPECIES_AUDIT.md):
# hym: the fertile surface: gills | pores | spines | ridges | other (no cap underside: honeycomb, ball, jelly, coral...)
# alt: other answers a careful observer may give for this species, with why (kept as 冲突, never dropped), e.g. very fine
#      pores read as "near smooth", an amanita egg read as a puffball
# spore: list of white yellow pink brown choc olive black green, or unknown (not documented) / na (no print possible)
# sub: ground | grass | wood | under ; ring / volva: True = present when intact; ringvar: the ring is often lost or faint
T = lambda hym, spore, sub, ring=False, volva=False, alt=None, why="", ringvar=False: dict(
    hym=hym, spore=spore if isinstance(spore, list) else [spore], sub=sub if isinstance(sub, list) else [sub],
    ring=ring, volva=volva, hymAlt=alt or [], hymWhy=why, ringVar=ringvar)
EGG = dict(alt=["other"], why="幼时整朵包在白色的蛋形外膜里，看起来像马勃")  # amanitas with a volva, at the egg stage
TAGS = {
 "羊肚菌": T("other", "white", ["ground", "wood"]), "半离羊肚菌": T("other", "white", "ground"),
 "美味牛肝菌（Porcini）": T("pores", "olive", "ground"), "网盖牛肝菌": T("pores", "olive", "ground"),
 "褐黄牛肝菌": T("pores", "olive", "ground"), "栗色圆孔牛肝菌": T("pores", "yellow", "ground"),
 "橙黄疣柄牛肝菌": T("pores", "brown", "ground"), "异色疣柄牛肝菌": T("pores", "brown", "ground"),
 "褐疣柄牛肝菌": T("pores", "brown", "ground"), "褐环乳牛肝菌": T("pores", "brown", "ground", ring=True),
 "乳牛肝菌": T("pores", "olive", "ground"), "厚环乳牛肝菌": T("pores", "brown", "ground", ring=True),
 "鸡油菌": T("ridges", "white", "ground"), "管形鸡油菌": T("ridges", "white", ["ground", "wood"]),
 "灰喇叭菌（黑喇叭菌）": T("ridges", "white", "ground"), "美味齿菌（羊蹄菇）": T("spines", "white", "ground"),
 "硫磺菌（林中鸡）": T("pores", "white", "wood", alt=["other", "ridges"], why="菌孔极细，看上去近乎光滑；层叠的檐状子实体也常被当成“其他形态”"), "牛排菌": T("pores", "white", "wood", alt=["other"], why="菌孔是一根根分开的细管，很细；舌头状的子实体也常被当成“其他形态”"),
 "绣球菌": T("other", "white", "wood"), "木耳": T("other", "white", "wood"),
 "大秃马勃": T("other", "olive", ["grass", "ground"]), "草地横膜马勃": T("other", "olive", "grass"),
 "网纹马勃": T("other", "olive", ["ground", "grass"]), "梨形马勃": T("other", "olive", "wood"),
 "四孢蘑菇（田野蘑菇）": T("gills", "choc", "grass", ring=True), "野蘑菇": T("gills", "choc", "grass", ring=True),
 "白林地蘑菇": T("gills", "choc", "ground", ring=True), "林生蘑菇": T("gills", "choc", ["ground", "wood"], ring=True),
 "大紫蘑菇（王子菇）": T("gills", "choc", ["ground", "grass"], ring=True),
 "赭盖鹅膏": T("gills", "white", "ground", volva=True, **EGG), "橙黄鹅膏": T("gills", "white", "ground", volva=True, **EGG),
 "橙盖鹅膏（凯撒蘑菇）": T("gills", "white", "ground", ring=True, volva=True, **EGG),
 "高大环柄菇": T("gills", ["white", "pink"], ["grass", "ground"], ring=True), "粗鳞青褶伞": T("gills", "white", ["ground", "grass"], ring=True),
 "香杏丽蘑（圣乔治口蘑）": T("gills", "white", "grass"), "硬柄小皮伞（仙环菇）": T("gills", "white", "grass"),
 "斜盖伞": T("gills", "pink", ["ground", "grass"]), "皱盖罗鳞伞": T("gills", "brown", "ground", ring=True),
 "蓝黄红菇": T("gills", "white", "ground"), "红蜡蘑": T("gills", "white", "ground"),
 "肉色杯伞": T("gills", "white", "ground"), "蜜环菌": T("gills", "white", ["wood", "ground"], ring=True),
 "紫丁香蘑": T("gills", "pink", "ground"), "粉紫香蘑": T("gills", "pink", "grass"),
 "荷叶离褶伞（炸鸡菇）": T("gills", "white", "ground"), "毛头鬼伞（鸡腿菇）": T("gills", "black", ["grass", "wood", "ground"], ring=True),
 "松乳菇": T("gills", "white", "ground"), "糙皮侧耳（平菇）": T("gills", "white", "wood"),
 "野生金针菇（冬菇）": T("gills", "white", ["wood", "ground"]),
 "夏块菌（夏松露）": T("other", "na", "under"), "白松露": T("other", "na", "under"),
 "黑孢块菌（佩里戈尔黑松露）": T("other", "na", "under"),
 "松茸": T("gills", "white", "ground", ring=True), "太平洋金鸡油菌": T("ridges", ["white", "yellow"], "ground"),
 "春王牛肝菌": T("pores", "olive", "ground"), "赞美牛肝菌": T("pores", "olive", ["wood", "ground"]),
 "龙虾菌": T("other", "white", "ground", alt=["ridges"], why="寄生菌让宿主的菌褶退化成钝圆的褶皱，看上去像棱脊"), "灰树花（舞茸）": T("pores", "white", ["wood", "ground"], alt=["other", "ridges"], why="菌孔细小，看上去近乎光滑；一大丛叶片状的子实体常被当成“其他形态”"),
 "猴头菇类": T("spines", "white", "wood", alt=["other"], why="没有菌盖，整团菌刺或珊瑚状的分枝常被当成“其他形态”"),
 # toxic
 "毒鹅膏（死帽蕈）": T("gills", "white", "ground", ring=True, volva=True, **EGG),
 "鳞柄白鹅膏（致命白毒伞）": T("gills", "white", "ground", ring=True, volva=True, **EGG),
 "豹斑鹅膏": T("gills", "white", "ground", ring=True, volva=True, **EGG),
 "变红丝盖伞": T("gills", "brown", "ground"), "细鳞丝膜菌": T("gills", "brown", "ground"),
 "白霜杯伞类": T("gills", "white", "grass"), "鹿花菌（假羊肚菌）": T("other", "unknown", "ground"),
 "卷边桩菇": T("gills", "brown", ["ground", "wood"]), "黄斑蘑菇": T("gills", "choc", "grass", ring=True),
 "半裸盖菇": T("gills", "choc", "grass"),
 "史密斯鹅膏": T("gills", "white", "ground", ring=True),
 "北美毁灭天使": T("gills", "white", "ground", ring=True, volva=True, **EGG),
 "纹缘盔孢伞": T("gills", "brown", ["wood", "ground"], ring=True, ringvar=True),
 "发光类脐菇": T("gills", ["white", "yellow"], ["wood", "ground"], alt=["ridges"], why="真菌褶厚而延生，常被当成鸡油菌的钝脊"),
 "大青褶伞": T("gills", "green", "grass", ring=True),
 # ring=True on the small deadly species keeps them listed whichever ring answer is given
 "致命小环柄菇": T("gills", "white", ["grass", "ground", "wood"], ring=True, ringvar=True),
 "皱盖锥盖伞": T("gills", "brown", ["ground", "wood"], ring=True),
 "簇生垂幕菇": T("gills", ["black", "choc"], "wood", ring=True),
 "毒蝇鹅膏": T("gills", "white", "ground", ring=True, volva=True, **EGG),
 "波地钟菌": T("other", "unknown", "ground"),
 "虾味红菇": T("gills", "white", "ground"),
 "贝形圆孢侧耳（天使之翼）": T("gills", "white", "wood"),
 "毛钉菇": T("ridges", "unknown", "ground"),
 "花旗松乳牛肝菌（胖杰克）": T("pores", "brown", "ground", ring=True),
 "糖果乳菇": T("gills", ["white", "yellow"], ["ground", "wood"]),
 "紫陀螺菌（猪耳）": T("ridges", ["yellow", "brown"], "ground"),
 "西部大马勃": T("other", "olive", ["grass", "ground"]),
}
