# 野菌速查手册

一个中文野生菌速查网站：食用菌识别、易混毒菌对比、按特征反查、中毒急救、采集与烹饪。可以装到手机桌面离线使用。

线上地址：https://bbpouq.github.io/mushroom-guide/

## 目录

```
src/                    源文件（改内容和样式都在这里）
  data/                 物种、毒菌、特征标签、易混对比、指南和食谱数据
  template.html         页面模板（样式、结构、脚本）
  build_site.py         生成 public/index.html
public/                 网站本体（直接部署这些文件，index.html 由脚本生成，不要手改）
tests/test_site.py      端到端检查（手机 / 平板 / 电脑、离线、深链接等）
.github/workflows/      GitHub Pages 自动发布
CLAUDE.md               给 Claude Code 的项目说明
```

## 修改流程

```sh
python3 src/build_site.py     # 改完 src/ 后重新生成
python3 tests/test_site.py    # 跑检查，应显示 ALL PASSED
```

检查需要先装一次：`pip install playwright pillow && python3 -m playwright install chromium`。

## 部署

用 GitHub Pages 托管：推送到 `main` 分支后，GitHub Actions（`.github/workflows/pages.yml`）会重新生成 `public/index.html`，确认它和仓库里的一致，再把 `public/` 发布出去。也可以在 Actions 页面手动运行。

仓库设置里 Pages 的来源要选 “GitHub Actions”（Settings → Pages → Source）。

本地预览：

```sh
cd public && python3 -m http.server 8000
# 打开 http://localhost:8000
```

修改 `public/sw.js` 里的 `CACHE` 版本号，可以让已安装的手机端尽快换上新的离线缓存。

## 内容来源与声明

内容分两部分，每个条目都标明来自哪里：

- **原书部分**（标有“原书 pXX”）：欧洲物种、十种常见毒菌和食谱索引，改写自 *The Edible Mushroom Book: A Guide to Foraging and Cooking*（Anna Del Conte、Thomas Læssøe 著，Dorling Kindersley，2008）。文字是我们自己的中文改写；网站不含原书图片。
- **本站原创食谱**（标有“本站原创”）：中式、日式和西式家常做法，每道都写明用哪几种菌、必须煮熟，并重复该菌的易混毒菌提醒。
- **原书以外的内容**（标有“原书未收录”“非原书”或“【编者注】”）：北美和西北太平洋的食用菌与毒菌、书中物种在当地的对应种和注意事项（例如西部绣球菌、实柄蜜环菌、北美的几类羊肚菌）、易混对比、“吃之前检查清单”和急救信息。这些都整理自公开资料，每条都在详情里列出来源链接，主要是：
  - UBC Beaty Museum “Mushrooms Up!”（BC 省和西北太平洋的食用与有毒菌）
  - MushroomExpert（Michael Kuo）、MykoWeb / California Fungi
  - 北美真菌学会（NAMA）中毒报告、州和省级政府机构
  - 同行评审论文（如 *Mycologia*、*Toxins*、*Mycological Progress*）
  - iNaturalist 上经鉴定的观察记录（只用来确认某个种在西北太平洋有没有分布）

示例照片来自 iNaturalist 上的开放许可照片（CC0、公有领域、CC BY、CC BY-SA、CC BY-NC、CC BY-NC-SA），每张都在图下注明作者、许可证和原图链接。本站免费、不商用；如果将来用于商业用途，需要换掉 NC 许可的照片。

没有找到可靠来源的说法不会写进网站。

本站只是速查摘要，不能代替实物鉴定。**有任何疑问，就不要吃。**
