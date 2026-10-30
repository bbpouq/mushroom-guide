# 野菌速查手册

一个中文野生菌速查网站：食用菌识别、易混毒菌对比、按特征反查、中毒急救、采集与烹饪。可以装到手机桌面离线使用。

线上地址：https://mushroom-guide.shizyang666.workers.dev

## 目录

```
src/                    源文件（改内容和样式都在这里）
  data/                 物种、毒菌、特征标签、易混对比、指南和食谱数据
  template.html         页面模板（样式、结构、脚本）
  build_site.py         生成 public/index.html
public/                 网站本体（直接部署这些文件，index.html 由脚本生成，不要手改）
tests/test_site.py      端到端检查（手机 / 平板 / 电脑、离线、深链接等）
wrangler.jsonc          Cloudflare Workers 部署配置（只托管静态文件）
CLAUDE.md               给 Claude Code 的项目说明
```

## 修改流程

```sh
python3 src/build_site.py     # 改完 src/ 后重新生成
python3 tests/test_site.py    # 跑检查，应显示 ALL PASSED
```

检查需要先装一次：`pip install playwright pillow && python3 -m playwright install chromium`。

## 部署

仓库已连接 Cloudflare Workers Builds：推送到 `main` 分支后会自动部署，网址不变。

手动部署（需要 Node.js）：

```sh
npx wrangler deploy
```

本地预览：

```sh
cd public && python3 -m http.server 8000
# 打开 http://localhost:8000
```

修改 `public/sw.js` 里的 `CACHE` 版本号，可以让已安装的手机端尽快换上新的离线缓存。

## 内容来源与声明

- 欧洲物种部分改写自 *The Edible Mushroom Book: A Guide to Foraging and Cooking*（Anna Del Conte、Thomas Læssøe 著，Dorling Kindersley，2008）。网站不含原书图片。
- 北美补充部分整理自 UBC Beaty Museum “Mushrooms Up!”、MushroomExpert、MykoWeb、各州自然资源部门、北美真菌学会等资料，来源列在每个条目的详情里。
- 本站只是速查摘要，不能代替实物鉴定。**有任何疑问，就不要吃。**
