# 实验报告正文（第 1～4 章）

本目录是《软件工程》课程实验报告第 1～4 章的正文与图表素材，数据和截图都来自本组工程 `Notes-maintain` 的实际源码与模拟器实测，可直接粘入报告模板对应章节。

## 文件对照

| 文件 | 对应报告章节 | 分值 | 状态 |
| --- | --- | --- | --- |
| `第1章-泛读开源代码.md` | 第 1 章：软件概况、包图、功能与类映射、六个核心包类图 | 18 | 正文 + 7 张图 + 3 张表 |
| `第2章-分析代码质量.md` | 第 2 章：人工优缺点各 2 条、Lint 自动分析、典型问题 | 15 | 正文 + 2 张表 |
| `第3章-标注开源代码.md` | 第 3 章：四级标注 9 处、表 3-1、标注后校验 | 15 | 标注已写入源码（+32/−8），编译通过 |
| `第4章-维护开源软件.md` | 第 4 章：四类维护、2 缺陷、3 功能、测试用例 | 25 | 正文 + 2 张表 + 2 张图，表 4-2 已回填 |

## 素材位置

| 目录 | 内容 |
| --- | --- |
| `docs/diagrams/` | 图 1-1～图 1-7、图 4-1、图 4-2 的 png 与 puml 源文件 |
| `docs/lint/` | Android Lint 原始报告（xml / html / txt） |
| `docs/shots/` | 测试截图：锁定列表、锁定编辑页、标签筛选、排序结果、基线列表 |
| `tools/gen_uml.py` | 表 1-1 与全部类图的生成脚本，数字可复现 |

## 重新生成图表

```
python tools/gen_uml.py src <输出目录> --changed Notes.java,NotesDatabaseHelper.java,NotesProvider.java,GTaskASyncTask.java,NoteEditActivity.java,NoteItemData.java,NotesListActivity.java,NotesListItem.java
```

生成的 `.puml` 用 PlantUML 渲染为 png（`java -jar plantuml.jar -charset UTF-8 -tpng *.puml`）。脚本只读源码，不修改任何文件。

## 还需要本组补的部分（不在第 1～4 章范围）

1. 第 5 章：维护前后界面对比截图、功能演示截图、mp4 录屏。`docs/shots/baseline-01-list-v4.png` 是维护前的列表，可以直接用。
2. 第 6 章：三人各自的心得，各写各的角度。
3. 封面：组号、组长、成员姓名学号、任务分工栏（按实际填）。
4. 报告定稿时删除模板中的斜体说明文字，并更新目录域。

## 数据来源声明

- 代码规模、类数、方法数：`tools/gen_uml.py` 扫描 `src/` 得出，口径见第 1 章 1.1。
- 静态分析数字：`gradlew lintDebug` 的真实输出，报告存于 `docs/lint/`。
- 缺陷与功能描述：与 `src/` 现行代码逐处对应，行号以本目录正文标注为准。
- 测试用例执行情况：九条在 AVD `Medium_Phone_API_37.0` 上实际操作得到，截图存于 `docs/shots/`；T10 因 Provider 未导出无法执行，如实记为未执行。
