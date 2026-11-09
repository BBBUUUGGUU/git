import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { FileBlob, Presentation, PresentationFile } from "@oai/artifact-tool";

const SKILL_DIR = "C:/Users/25038/.codex/plugins/cache/openai-primary-runtime/presentations/26.904.11930/skills/presentations";
const workspaceDir = "C:/Users/25038/Desktop/git";
const buildDir = "C:/Users/25038/Desktop/git/ppt_build_research_status_20260912";
const outputDir = "C:/Users/25038/Desktop/git/outputs/research_status_slide_20260912";
const FINAL_PPTX = path.join(outputDir, "研究现状与技术需求_一页版_v5.pptx");
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
  teal: "#1C8D91",
  orange: "#D65B2A",
  ink: "#17212B",
  muted: "#5D6A78",
  line: "#D8E0EA",
  paleBlue: "#EAF2FF",
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

// Title and evidence-based takeaway
rect(54, 31, 7, 57, C.blue);
textBox("接触式装配研究现状与技术需求", 78, 25, 930, 50, {
  fontSize: 39,
  bold: true,
  color: C.navy,
});
textBox("算法、感知融合与仿真迁移已有基础，空间双臂高精度插拔仍缺少完整训练与验证闭环", 79, 79, 1125, 30, {
  fontSize: 20,
  color: C.muted,
});

// Three-stage narrative headers
rect(60, 132, 520, 5, C.blue);
rect(615, 132, 245, 5, C.orange);
rect(900, 132, 320, 5, C.teal);
textBox("已有研究进展", 60, 149, 350, 37, { fontSize: 27, bold: true, color: C.blue });
textBox("现有瓶颈", 615, 149, 210, 37, { fontSize: 27, bold: true, color: C.orange });
textBox("本研究提出的技术需求", 900, 149, 320, 37, { fontSize: 27, bold: true, color: C.teal });
rect(592, 145, 2, 394, C.line);
rect(880, 145, 2, 394, C.line);

const progress = [
  ["连续动作强化学习", "DDPG[9]、TD3[10]、PPO[11]、SAC[12]\n已用于轴孔插入和接触操作"],
  ["多模态与残差控制", "Ahn[24]、Jin[25]开展视觉—力觉协同\nJohannink[26]提出残差强化学习"],
  ["并行仿真与技能迁移", "Factory[17]、IndustReal[18]、AutoMate[19]\nIsaac Lab[20]，域随机化[32]，元学习[36,38]"],
];
const py = [202, 313, 424];
for (let i = 0; i < progress.length; i += 1) {
  rect(60, py[i] + 4, 6, 72, C.blue);
  textBox(progress[i][0], 82, py[i], 455, 29, { fontSize: 22, bold: true, color: C.ink });
  textBox(progress[i][1], 82, py[i] + 34, 478, i === 2 ? 76 : 58, { fontSize: 18.5, color: C.muted });
  if (i < 2) rect(82, py[i] + 94, 478, 1, C.line);
}

const gaps = [
  ["接触过程难建模", "碰撞、摩擦和卡阻造成\n动力学非线性与状态切换"],
  ["多模态状态难利用", "视觉与力觉的维度、频率\n及噪声特性差异明显"],
  ["空间场景验证不足", "现有成果多面向固定基座\n在轨数据与实物试验有限"],
];
const gy = [202, 319, 436];
for (let i = 0; i < gaps.length; i += 1) {
  textBox(String(i + 1).padStart(2, "0"), 615, gy[i], 41, 28, {
    fontSize: 18,
    bold: true,
    color: C.orange,
  });
  textBox(gaps[i][0], 660, gy[i], 190, 30, { fontSize: 21, bold: true, color: C.ink });
  textBox(gaps[i][1], 615, gy[i] + 37, 235, 58, { fontSize: 18.5, color: C.muted });
  if (i < 2) rect(615, gy[i] + 99, 235, 1, C.line);
}

const needs = [
  ["高拟真空间双臂环境", "覆盖基座运动与双臂耦合\n建模插拔接触及视觉—力觉反馈"],
  ["连续残差柔顺策略", "保留基础控制器的稳定性，\n学习接触阶段的连续补偿量"],
  ["跨环境与跨任务迁移", "联合域随机化与元训练任务\n采用独立测试验证泛化能力"],
];
const ny = [202, 319, 436];
for (let i = 0; i < needs.length; i += 1) {
  rect(900, ny[i] + 2, 42, 42, C.paleBlue, true);
  textBox(String(i + 1).padStart(2, "0"), 900, ny[i] + 5, 42, 33, {
    fontSize: 17,
    bold: true,
    color: C.teal,
    alignment: "center",
    verticalAlignment: "middle",
  });
  textBox(needs[i][0], 957, ny[i], 255, 31, { fontSize: 21, bold: true, color: C.ink });
  textBox(needs[i][1], 957, ny[i] + 37, 258, 58, { fontSize: 18.5, color: C.muted });
  if (i < 2) rect(957, ny[i] + 99, 258, 1, C.line);
}

// Visible reference strip, aligned with the numbering in the supplied literature review.
rect(0, 560, 1280, 160, C.navy);
textBox("代表文献（与正文编号一致）", 60, 577, 420, 31, { fontSize: 20, bold: true, color: C.white });
rect(60, 615, 1160, 1, "#40526A");
textBox(
  "算法基础：Mnih等[8] DQN，Lillicrap等[9] DDPG，Fujimoto等[10] TD3，Schulman等[11] PPO，Haarnoja等[12] SAC",
  60, 628, 1160, 27, { fontSize: 16.5, color: "#D9E4F1" },
);
textBox(
  "装配与迁移：Narang等[17] Factory，Tang等[18] IndustReal，Johannink等[26] Residual RL，Tobin等[32] 域随机化，Finn等[36] MAML，Shokry等[38] 元强化学习",
  60, 660, 1160, 50, { fontSize: 16.5, color: "#D9E4F1" },
);

slide.speakerNotes.textFrame.setText(
  "本页依据用户提供的国内外研究现状材料归纳，文献编号沿用原稿：[8] Mnih等DQN；[9] Lillicrap等DDPG；[10] Fujimoto等TD3；[11] Schulman等PPO；[12] Haarnoja等SAC；[17] Narang等Factory；[18] Tang等IndustReal；[19] AutoMate；[20] Isaac Lab；[24] Ahn等视觉—力觉策略；[25] Jin等视觉—力觉课程学习；[26] Johannink等残差强化学习；[32] Tobin等域随机化；[36] Finn等MAML；[38] Shokry等上下文元强化学习。未获得原稿参考文献表，因此页内保留正文编号，未补写可能不准确的题名、期刊和年份。",
);

const preview = await deck.export({ slide, format: "png", scale: 1.5 });
await fs.writeFile(path.join(buildDir, "draft-slide-v3.png"), new Uint8Array(await preview.arrayBuffer()));
const layout = await slide.export({ format: "layout" });
await fs.writeFile(path.join(buildDir, "draft-slide-v3.layout.json"), await layout.text());

const stagingDir = path.join(buildDir, ".codex-finalizer-v3");
await fs.mkdir(stagingDir, { recursive: true });
const candidatePath = path.join(stagingDir, "candidate-v3.pptx");
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
  receiptPath: path.join(stagingDir, "研究现状与技术需求_一页版_v5.validation.json"),
});

const finalDeck = await PresentationFile.importPptx(await FileBlob.load(FINAL_PPTX));
const finalSlide = finalDeck.slides.items[0];
const finalPng = await finalDeck.export({ slide: finalSlide, format: "png", scale: 1.5 });
await fs.writeFile(path.join(buildDir, "final-slide-v3.png"), new Uint8Array(await finalPng.arrayBuffer()));
const snapshot = await finalDeck.inspect({ kind: "slide,textbox,shape,notes,layout", maxChars: 14000 });
await fs.writeFile(path.join(buildDir, "final-inspect-v3.ndjson"), snapshot.ndjson);

console.log(JSON.stringify({ finalPath: FINAL_PPTX, result }, null, 2));
