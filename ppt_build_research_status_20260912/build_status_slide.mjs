import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { FileBlob, Presentation, PresentationFile } from "@oai/artifact-tool";

const SKILL_DIR = "C:/Users/25038/.codex/plugins/cache/openai-primary-runtime/presentations/26.904.11930/skills/presentations";
const workspaceDir = "C:/Users/25038/Desktop/git";
const buildDir = "C:/Users/25038/Desktop/git/ppt_build_research_status_20260912";
const outputDir = "C:/Users/25038/Desktop/git/outputs/research_status_slide_20260912";
const FINAL_PPTX = path.join(outputDir, "国内外研究现状_一页版_v2.pptx");
const RUNTIME_PYTHON = "C:/Users/25038/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";

const { resolvePresentationFont, finalizePresentation } = await import(
  pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href,
);
const family = resolvePresentationFont({ fontFamily: "Noto Sans SC" });

await fs.mkdir(buildDir, { recursive: true });
await fs.mkdir(outputDir, { recursive: true });

const deck = Presentation.create({ slideSize: { width: 1280, height: 720 } });
const slide = deck.slides.add();
slide.background.fill = "#F7F9FC";

const C = {
  navy: "#10243E",
  blue: "#2166D1",
  blueLight: "#E7F0FF",
  orange: "#D65B2A",
  orangeLight: "#FCECE5",
  ink: "#17212B",
  muted: "#5D6A78",
  line: "#D8E0EA",
  white: "#FFFFFF",
  aqua: "#58C4C2",
};

function addRect(left, top, width, height, fill, radius = false, lineFill = "none") {
  return slide.shapes.add({
    geometry: radius ? "roundRect" : "rect",
    position: { left, top, width, height },
    fill,
    line: { fill: lineFill, width: lineFill === "none" ? 0 : 1 },
  });
}

function addText(text, left, top, width, height, opts = {}) {
  const box = slide.shapes.add({
    geometry: "textbox",
    position: { left, top, width, height },
    fill: "none",
    line: { fill: "none", width: 0 },
  });
  box.text = text;
  box.text.style = {
    typeface: family,
    fontSize: opts.fontSize ?? 22,
    bold: opts.bold ?? false,
    color: opts.color ?? C.ink,
    alignment: opts.alignment ?? "left",
    verticalAlignment: opts.verticalAlignment ?? "top",
    autoFit: "none",
    wrap: "square",
    insets: opts.insets ?? { left: 0, right: 0, top: 0, bottom: 0 },
  };
  return box;
}

// Header
addRect(54, 34, 7, 55, C.blue);
addText("国内外机器人高精度插拔研究现状", 78, 27, 950, 52, {
  fontSize: 39,
  bold: true,
  color: C.navy,
});
addText("国外已形成算法、平台与迁移的完整链路，国内正推进融合控制及空间场景适配", 79, 80, 1100, 31, {
  fontSize: 20,
  color: C.muted,
});

// Section labels and center divider
addRect(62, 132, 552, 5, C.blue);
addRect(666, 132, 552, 5, C.orange);
addText("国外研究", 62, 148, 260, 38, { fontSize: 29, bold: true, color: C.blue });
addText("国内研究", 666, 148, 260, 38, { fontSize: 29, bold: true, color: C.orange });
addRect(638, 143, 2, 365, C.line);

const rows = [194, 302, 410];
const leftItems = [
  ["连续控制算法", "DDPG、TD3、PPO、SAC成为接触操作的主要方法\n研究从单一运动控制扩展到视觉、力觉和控制先验融合"],
  ["并行仿真平台", "Factory、IndustReal、AutoMate覆盖多类接触装配\nIsaac Lab支持GPU并行、多模态感知与域随机化"],
  ["迁移与快速适应", "域随机化增强动力学和传感误差鲁棒性\n元强化学习利用少量交互适应新几何与新任务"],
];
const rightItems = [
  ["控制与学习融合", "关节阻抗、导纳控制提供基本柔顺性\nPPO及残差策略补偿位姿误差与接触扰动"],
  ["视觉—力觉协同", "视觉负责大范围接近与初步对准，力觉处理接触校正\n示教与运动基元减少长时序随机探索"],
  ["空间装配拓展", "多模态阻抗型虚实迁移已开展验证\n空间机器人高精度插拔研究仍处于拓展阶段"],
];

function addResearchItem(x, y, number, accent, pale, heading, body) {
  addRect(x, y + 3, 44, 44, pale, true);
  addText(String(number).padStart(2, "0"), x, y + 5, 44, 38, {
    fontSize: 18,
    bold: true,
    color: accent,
    alignment: "center",
    verticalAlignment: "middle",
  });
  addText(heading, x + 62, y, 410, 31, { fontSize: 22, bold: true, color: C.ink });
  addText(body, x + 62, y + 34, 472, 61, { fontSize: 18, color: C.muted });
}

for (let i = 0; i < 3; i += 1) {
  addResearchItem(62, rows[i], i + 1, C.blue, C.blueLight, leftItems[i][0], leftItems[i][1]);
  addResearchItem(666, rows[i], i + 1, C.orange, C.orangeLight, rightItems[i][0], rightItems[i][1]);
  if (i < 2) {
    addRect(124, rows[i] + 94, 472, 1, C.line);
    addRect(728, rows[i] + 94, 472, 1, C.line);
  }
}

// Bottom synthesis band
addRect(0, 535, 1280, 185, C.navy);
addText("关键差距与研究切入", 62, 553, 430, 37, { fontSize: 25, bold: true, color: C.white });
addRect(62, 594, 1156, 1, "#40526A");

const synth = [
  ["空间场景缺口", "现有成果主要面向地面固定基座\n基座运动与动力学耦合研究不足"],
  ["训练与验证瓶颈", "接触动力学不连续，在轨交互数据稀缺\n仿真策略难以直接迁移"],
  ["本文切入", "高拟真视觉—力觉环境与残差策略\n协同域随机化和元学习"],
];
const sx = [62, 458, 854];
for (let i = 0; i < 3; i += 1) {
  addText(synth[i][0], sx[i], 610, 320, 28, {
    fontSize: 19,
    bold: true,
    color: i === 2 ? C.aqua : "#B7C8DD",
  });
  addText(synth[i][1], sx[i], 641, 330, 53, { fontSize: 17, color: C.white });
  if (i < 2) addRect(sx[i] + 365, 612, 1, 77, "#40526A");
}

slide.speakerNotes.textFrame.setText(
  "内容依据用户提供的《国内外研究现状》原文归纳，涉及文献编号[3]、[5]、[8]—[40]。本页仅总结用户材料中的技术路线、代表性平台与研究缺口，未新增外部事实。",
);

const preview = await deck.export({ slide, format: "png", scale: 1.5 });
await fs.writeFile(path.join(buildDir, "draft-slide-1.png"), new Uint8Array(await preview.arrayBuffer()));
const layout = await slide.export({ format: "layout" });
await fs.writeFile(path.join(buildDir, "draft-slide-1.layout.json"), await layout.text());

const requirements = {
  explicitTotalSlideCount: 1,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [],
};
const fontPolicy = { basis: "design", families: [family] };
const stagingDir = path.join(buildDir, ".codex-finalizer");
await fs.mkdir(stagingDir, { recursive: true });
const candidatePath = path.join(stagingDir, "candidate.pptx");
await (await PresentationFile.exportPptx(deck)).save(candidatePath);

const result = await finalizePresentation({
  ...requirements,
  workspaceDir,
  candidatePath,
  finalPath: FINAL_PPTX,
  pythonExecutable: RUNTIME_PYTHON,
  integrityValidatorPath: path.join(SKILL_DIR, "container_tools/inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(SKILL_DIR, "container_tools/inspect_presentation_layout_geometry.py"),
  layoutArgs: [
    "--expected-slide-size-emu", "12192000,6858000",
    "--validate-bullet-geometry",
    "--validate-heading-fit",
  ],
  requiredNativeTableOwnerSlides: [],
  fontPolicy,
  verifyArtifactToolImport: true,
  receiptPath: path.join(stagingDir, "国内外研究现状_一页版_v2.validation.json"),
});

const finalDeck = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
const finalSlide = finalDeck.slides.items[0];
const finalPng = await finalDeck.export({ slide: finalSlide, format: "png", scale: 1.5 });
await fs.writeFile(path.join(buildDir, "final-slide-1.png"), new Uint8Array(await finalPng.arrayBuffer()));
const snapshot = await finalDeck.inspect({ kind: "slide,textbox,shape,notes,layout", maxChars: 12000 });
await fs.writeFile(path.join(buildDir, "final-inspect.ndjson"), snapshot.ndjson);

console.log(JSON.stringify({ finalPath: FINAL_PPTX, result }, null, 2));
