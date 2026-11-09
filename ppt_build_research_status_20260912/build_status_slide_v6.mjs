import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { FileBlob, Presentation, PresentationFile } from "@oai/artifact-tool";

const SKILL_DIR = "C:/Users/25038/.codex/plugins/cache/openai-primary-runtime/presentations/26.904.11930/skills/presentations";
const workspaceDir = "C:/Users/25038/Desktop/git";
const buildDir = "C:/Users/25038/Desktop/git/ppt_build_research_status_20260912";
const outputDir = "C:/Users/25038/Desktop/git/outputs/research_status_slide_20260912";
const assetDir = path.join(outputDir, "assets");
const FINAL_PPTX = path.join(outputDir, "研究现状与技术需求_图示版_v6.pptx");
const RUNTIME_PYTHON = "C:/Users/25038/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";

const { resolvePresentationFont, finalizePresentation } = await import(
  pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href,
);
const family = resolvePresentationFont({ fontFamily: "Noto Sans SC" });
await fs.mkdir(buildDir, { recursive: true });
await fs.mkdir(outputDir, { recursive: true });

const [rlImage, fusionImage, transferImage] = await Promise.all([
  fs.readFile(path.join(assetDir, "fig_rl_control.png")),
  fs.readFile(path.join(assetDir, "fig_visuotactile.png")),
  fs.readFile(path.join(assetDir, "fig_sim2real_space_dualarm.png")),
]);

const deck = Presentation.create({ slideSize: { width: 1280, height: 720 } });
const slide = deck.slides.add();
slide.background.fill = "#F7F9FC";

const C = {
  navy: "#10243E",
  blue: "#2166D1",
  teal: "#1C8D91",
  orange: "#D65B2A",
  ink: "#17212B",
  muted: "#5D6A78",
  line: "#D8E0EA",
  paleOrange: "#FFF0E9",
  white: "#FFFFFF",
};

function rect(left, top, width, height, fill, radius = false, lineFill = "none") {
  return slide.shapes.add({
    geometry: radius ? "roundRect" : "rect",
    position: { left, top, width, height },
    fill,
    line: { fill: lineFill, width: lineFill === "none" ? 0 : 1 },
  });
}

function textBox(text, left, top, width, height, opts = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position: { left, top, width, height },
    fill: "none",
    line: { fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    typeface: family,
    fontSize: opts.fontSize ?? 21,
    bold: opts.bold ?? false,
    color: opts.color ?? C.ink,
    alignment: opts.alignment ?? "left",
    verticalAlignment: opts.verticalAlignment ?? "top",
    autoFit: "none",
    wrap: "square",
    insets: opts.insets ?? { left: 0, right: 0, top: 0, bottom: 0 },
  };
  return shape;
}

// Header
rect(54, 29, 7, 58, C.blue);
textBox("接触式装配研究现状与技术需求", 78, 23, 930, 52, {
  fontSize: 40,
  bold: true,
  color: C.navy,
});
textBox("研究已覆盖连续策略、多模态融合和仿真迁移，空间双臂高精度插拔仍缺少完整验证闭环", 79, 78, 1135, 30, {
  fontSize: 20,
  color: C.muted,
});

// Three distinct visual assets, each used once.
const imageY = 128;
const imageW = 360;
const imageH = 190;
const xs = [60, 460, 860];
const images = [rlImage, fusionImage, transferImage];
const alts = [
  "强化学习控制机械臂执行轴孔插入的概念示意图",
  "视觉与力觉协同感知插入接触状态的概念示意图",
  "空间双臂机器人从仿真到真实部署的概念示意图",
];
for (let i = 0; i < 3; i += 1) {
  rect(xs[i] - 3, imageY - 3, imageW + 6, imageH + 6, C.white, true, C.line);
  slide.images.add({
    blob: images[i],
    contentType: "image/png",
    alt: alts[i],
    fit: "cover",
    geometry: "roundRect",
    borderRadius: "rounded-xl",
    position: { left: xs[i], top: imageY, width: imageW, height: imageH },
  });
}

// Evidence and representative literature under each visual.
const headings = ["连续动作强化学习", "视觉—力觉与残差控制", "并行仿真与技能迁移"];
const summaries = [
  "从DQN扩展至DDPG、TD3、PPO和SAC，\n连续策略逐步用于轴孔插入与接触操作",
  "视觉承担大范围对准，力觉处理接触校正，\n残差策略学习控制器未覆盖的误差",
  "并行平台支持大规模训练，域随机化与\n元学习面向虚实迁移和新任务适应",
];
const references = [
  "Mnih[8]  Lillicrap[9]  Fujimoto[10]\nSchulman[11]  Haarnoja[12]",
  "Ahn[24]  Jin[25]  Johannink[26]",
  "Factory[17]  IndustReal[18]  AutoMate[19]\nIsaac Lab[20]  Tobin[32]  Finn[36]",
];
const accents = [C.blue, C.orange, C.teal];
for (let i = 0; i < 3; i += 1) {
  rect(xs[i], 333, 38, 4, accents[i]);
  textBox(headings[i], xs[i], 346, imageW, 31, { fontSize: 22, bold: true, color: C.ink });
  textBox(summaries[i], xs[i], 382, imageW, 55, { fontSize: 18, color: C.muted });
  textBox(references[i], xs[i], 442, imageW, 43, { fontSize: 15.5, color: accents[i] });
}

// The literature synthesis explicitly leads to the requirements.
rect(60, 492, 1160, 39, C.paleOrange, true);
textBox("现状暴露：接触动力学不连续，多模态数据不同步，空间双臂实物验证不足", 80, 498, 1120, 27, {
  fontSize: 18.5,
  bold: true,
  color: C.orange,
  alignment: "center",
});

rect(0, 546, 1280, 174, C.navy);
textBox("由现状提出的技术需求", 60, 562, 410, 32, { fontSize: 24, bold: true, color: C.white });
rect(60, 601, 1160, 1, "#40526A");

const needs = [
  ["01", "高拟真空间双臂环境", "覆盖基座运动、双臂耦合与插拔接触\n同步生成视觉及力觉反馈"],
  ["02", "连续残差柔顺策略", "基础控制器保证稳定与柔顺\n残差策略学习接触阶段连续补偿"],
  ["03", "跨环境与跨任务迁移", "联合域随机化与元训练任务\n通过独立测试验证策略泛化能力"],
];
const needX = [60, 460, 860];
for (let i = 0; i < 3; i += 1) {
  textBox(needs[i][0], needX[i], 618, 44, 27, { fontSize: 18, bold: true, color: "#64D3D0" });
  textBox(needs[i][1], needX[i] + 52, 615, 300, 30, { fontSize: 20, bold: true, color: C.white });
  textBox(needs[i][2], needX[i] + 52, 650, 310, 51, { fontSize: 17, color: "#D9E4F1" });
  if (i < 2) rect(needX[i] + 378, 618, 1, 76, "#40526A");
}
textBox("三幅图片为概念示意，文献编号与正文一致", 60, 703, 550, 13, {
  fontSize: 11,
  color: "#8FA4BD",
});

slide.speakerNotes.textFrame.setText(
  "内容依据用户提供的国内外研究现状材料归纳。文献编号沿用正文：[8] Mnih等DQN；[9] Lillicrap等DDPG；[10] Fujimoto等TD3；[11] Schulman等PPO；[12] Haarnoja等SAC；[17] Narang等Factory；[18] Tang等IndustReal；[19] AutoMate；[20] Isaac Lab；[24] Ahn等视觉—力觉策略；[25] Jin等视觉—力觉课程学习；[26] Johannink等残差强化学习；[32] Tobin等域随机化；[36] Finn等MAML。三幅插图由OpenAI图像生成工具生成，用作连续动作强化学习、视觉—力觉融合和仿真迁移的概念示意，不代表具体论文实验装置或真实实验照片。",
);

const preview = await deck.export({ slide, format: "png", scale: 1.5 });
await fs.writeFile(path.join(buildDir, "draft-slide-v6.png"), new Uint8Array(await preview.arrayBuffer()));
const layout = await slide.export({ format: "layout" });
await fs.writeFile(path.join(buildDir, "draft-slide-v6.layout.json"), await layout.text());

const stagingDir = path.join(buildDir, ".codex-finalizer-v6");
await fs.mkdir(stagingDir, { recursive: true });
const candidatePath = path.join(stagingDir, "candidate-v6.pptx");
await (await PresentationFile.exportPptx(deck)).save(candidatePath);

const result = await finalizePresentation({
  explicitTotalSlideCount: 1,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [],
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
  fontPolicy: { basis: "design", families: [family] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(stagingDir, "研究现状与技术需求_图示版_v6.validation.json"),
});

const finalDeck = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
const finalSlide = finalDeck.slides.items[0];
const finalPng = await finalDeck.export({ slide: finalSlide, format: "png", scale: 1.5 });
await fs.writeFile(path.join(buildDir, "final-slide-v6.png"), new Uint8Array(await finalPng.arrayBuffer()));
const snapshot = await finalDeck.inspect({ kind: "slide,textbox,shape,image,notes,layout", maxChars: 16000 });
await fs.writeFile(path.join(buildDir, "final-inspect-v6.ndjson"), snapshot.ndjson);

console.log(JSON.stringify({ finalPath: FINAL_PPTX, result }, null, 2));
