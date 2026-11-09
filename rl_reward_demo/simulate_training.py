"""生成 500 回合插接强化学习的模拟 reward 曲线。

说明：
1. 这是用于检查奖励函数和绘图流程的可复现实例，不是真实机器人实验数据。
2. 长度计算统一使用 m；图和 CSV 中的距离可按需转换成 mm。
3. 每一步奖励以题目公式为基础，加入 0.05 进度缩放，并将状态奖励
   改为前后差值，以防止智能体停在阈值附近重复获得奖励。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib

# 使用非交互式后端，脚本在终端、服务器或未开启图形界面时也能直接保存图片。
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


# --------------------------- 可修改的实验参数 ---------------------------
N_EPISODES = 500
MAX_STEPS = 200
INITIAL_AXIAL_DISTANCE = 0.170       # 初始轴向距离约 17 cm
MAX_INITIAL_RADIAL_ERROR = 0.040     # 初始径向偏差在 4 cm 内
RADIAL_ACCURACY = 0.003              # 精度阈值 3 mm（与奖励公式一致）
SUCCESS_INSERTION_DEPTH = 0.008      # 成功：插入深度大于 8 mm
MAX_INSERTION_DEPTH = 0.020          # 失败：插入深度超过 20 mm
MAX_RADIAL_ERROR = 0.060             # 失败：径向误差超过 60 mm
MAX_BACKWARD_DISTANCE = 0.050        # 失败：累计轴向后退超过 50 mm

SUCCESS_BONUS = 100.0                # 原题空缺，暂取 +100，可直接修改
OVER_INSERTION_PENALTY = -60.0
RADIAL_FAILURE_PENALTY = -40.0
BACKWARD_FAILURE_PENALTY = -40.0
TIME_LIMIT_EXTRA_PENALTY = -10.0     # 200 步时：最后一步 r_base - 10
PROGRESS_REWARD_SCALE = 0.05         # 缩放进度奖励，使 +100 成为成功回合的主要奖励
MIN_EXPLORATION_RATE = 0.03          # 后期保留 3% 探索率，仍有少量随机波动
RANDOM_SEED = 2026


@dataclass
class EpisodeResult:
    episode: int
    episode_reward: float
    steps: int
    success: int
    terminal_reason: str


def base_reward(
    rho_previous: float,
    rho: float,
    d_previous: float,
    d: float,
    insertion_depth_previous: float,
    insertion_depth: float,
) -> float:
    """计算改进后的单步奖励，只对状态的实际改善进行奖励。"""
    delta_rho = rho_previous - rho
    delta_d = d_previous - d

    if rho < RADIAL_ACCURACY:
        axial_reward = 900.0 * delta_d
    elif delta_d > 0.0:
        axial_reward = -250.0 * delta_d
    else:
        axial_reward = 50.0 * delta_d

    # 原来的径向和轴向进度项保留，但整体缩放，避免普通步奖励
    # 累计到 300～400，从而掩盖成功终止奖励 +100。
    progress_reward = PROGRESS_REWARD_SCALE * (
        2500.0 * delta_rho + axial_reward
    )

    # 使用“当前势函数 - 上一步势函数”，状态不变时不会重复获得奖励。
    align_reward = 200.0 * (
        max(0.0, RADIAL_ACCURACY - rho)
        - max(0.0, RADIAL_ACCURACY - rho_previous)
    )
    depth_reward = 20.0 * (
        min(insertion_depth, MAX_INSERTION_DEPTH)
        - min(insertion_depth_previous, MAX_INSERTION_DEPTH)
    )

    # 每步固定扣分，鼓励用更少的动作完成插接。
    return progress_reward + align_reward + depth_reward - 0.02


def policy_skill(episode: int) -> float:
    """采用较慢的 S 形学习曲线，避免前 100 回合成功率上升过快。"""
    learned = 1.0 / (1.0 + np.exp(-(episode - 150.0) / 45.0))
    return float(np.clip(0.04 + 0.95 * learned, 0.0, 0.99))


def exploration_rate(episode: int) -> float:
    """前期保持较高探索率并缓慢衰减，后期保留少量随机探索。"""
    return float(MIN_EXPLORATION_RATE + 0.62 * np.exp(-(episode - 1) / 140.0))


def run_episode(episode: int, rng: np.random.Generator) -> EpisodeResult:
    """运行一个简化的插接回合，并逐步累计附件中的奖励。"""
    skill = policy_skill(episode)
    # 整个回合以 epsilon 概率执行探索策略。后期仍有少量探索回合，
    # 因而第一次成功后不会从此全部成功。
    if rng.random() < exploration_rate(episode):
        skill *= rng.uniform(0.05, 0.38)
    rho = rng.uniform(0.0, MAX_INITIAL_RADIAL_ERROR)
    axial_position = -INITIAL_AXIAL_DISTANCE  # 孔口为 0，负值表示尚未到达孔口
    cumulative_backward = 0.0
    step_reward_sum = 0.0
    terminal_reward = 0.0
    reason = "time_limit"
    success = 0

    for step in range(1, MAX_STEPS + 1):
        rho_previous = rho
        position_previous = axial_position

        # 径向控制：训练早期噪声大，后期能稳定地把误差压到 3 mm 内。
        radial_correction = skill * (0.0012 + 0.16 * rho)
        radial_noise = rng.normal(0.0, 0.0028 * (1.0 - skill) + 0.00012)
        rho = max(0.0, rho - radial_correction + radial_noise)

        # 轴向控制：高水平策略会在径向未对准时减速，对准后再快速推进。
        if rho > RADIAL_ACCURACY:
            cautious_factor = 0.25 + 0.75 * (1.0 - skill)
        else:
            cautious_factor = 1.0

        mean_forward = (0.00045 + 0.00265 * skill) * cautious_factor
        axial_noise = rng.normal(0.0, 0.0023 * (1.0 - skill) + 0.00018)
        axial_delta = mean_forward + axial_noise

        # 训练早期偶发明显错误动作，使失败类型和 reward 波动更接近训练过程。
        if rng.random() < 0.012 * (1.0 - skill):
            axial_delta -= rng.uniform(0.003, 0.010)
        if rng.random() < 0.007 * (1.0 - skill):
            rho += rng.uniform(0.004, 0.014)

        axial_position += axial_delta
        if axial_delta < 0.0:
            cumulative_backward += -axial_delta

        insertion_depth = max(0.0, axial_position)
        insertion_depth_previous = max(0.0, position_previous)
        # d 为轴向剩余距离；越向前推进，d 越小，故 Delta d 为正。
        d_previous = -position_previous
        d = -axial_position
        r_step = base_reward(
            rho_previous,
            rho,
            d_previous,
            d,
            insertion_depth_previous,
            insertion_depth,
        )
        step_reward_sum += r_step

        # 终止判断：成功优先，避免正常成功动作被误判为过插入。
        if rho <= RADIAL_ACCURACY and insertion_depth > SUCCESS_INSERTION_DEPTH:
            terminal_reward = SUCCESS_BONUS
            reason = "success"
            success = 1
            break
        if insertion_depth > MAX_INSERTION_DEPTH:
            terminal_reward = OVER_INSERTION_PENALTY
            reason = "over_insertion"
            break
        if rho > MAX_RADIAL_ERROR:
            terminal_reward = RADIAL_FAILURE_PENALTY
            reason = "radial_error"
            break
        if cumulative_backward > MAX_BACKWARD_DISTANCE:
            terminal_reward = BACKWARD_FAILURE_PENALTY
            reason = "backward"
            break
        if step == MAX_STEPS:
            # 最后一步相当于 shaping 后的 r_base 再减 10。
            terminal_reward = TIME_LIMIT_EXTRA_PENALTY

    # 成功或失败奖励与整个回合的普通步奖励相加。
    episode_reward = terminal_reward + step_reward_sum
    return EpisodeResult(episode, episode_reward, step, success, reason)


def moving_average(values: np.ndarray, window: int) -> np.ndarray:
    """返回与原数组等长的前向滑动平均。"""
    cumulative = np.cumsum(np.insert(values, 0, 0.0))
    result = np.empty_like(values, dtype=float)
    for i in range(len(values)):
        start = max(0, i + 1 - window)
        result[i] = (cumulative[i + 1] - cumulative[start]) / (i + 1 - start)
    return result


def configure_chinese_font() -> None:
    """优先使用 Windows 常见中文字体，并保留跨平台候选。"""
    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "Arial Unicode MS",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False


def save_results(results: list[EpisodeResult], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    episodes = np.array([r.episode for r in results])
    rewards = np.array([r.episode_reward for r in results])
    reward_ma = moving_average(rewards, window=25)

    csv_path = output_dir / "training_results.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
        file.write("episode,episode_reward,steps,success,terminal_reason\n")
        for r in results:
            file.write(
                f"{r.episode},{r.episode_reward:.6f},{r.steps},"
                f"{r.success},{r.terminal_reason}\n"
            )

    configure_chinese_font()
    fig, ax = plt.subplots(figsize=(11.5, 6.3), dpi=150)
    ax.plot(
        episodes,
        rewards,
        color="#9aa9ba",
        linewidth=0.75,
        alpha=0.52,
        label="单回合 Reward",
    )
    ax.plot(
        episodes,
        reward_ma,
        color="#174f7a",
        linewidth=2.6,
        label="Reward（25 回合滑动平均）",
    )
    ax.axhline(
        SUCCESS_BONUS,
        color="#4b876d",
        linewidth=1.0,
        linestyle="--",
        alpha=0.65,
        label="成功终止奖励 +100",
    )
    ax.set_xlabel("训练回合 Episode")
    ax.set_ylabel("回合 Reward")
    ax.set_xlim(1, N_EPISODES)
    ax.set_ylim(min(-70.0, rewards.min() - 5.0), max(115.0, rewards.max() + 5.0))
    ax.grid(True, linestyle="--", alpha=0.22)
    ax.legend(loc="lower right", frameon=True)
    ax.set_title("500 回合插接强化学习模拟 Reward 曲线")
    fig.text(
        0.5,
        0.015,
        "注：本图由简化环境与给定奖励函数模拟生成，不代表真实机器人实验结果。",
        ha="center",
        fontsize=9,
        color="#666666",
    )
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(output_dir / "reward_curve_500_episodes.png", bbox_inches="tight")
    fig.savefig(output_dir / "reward_curve_500_episodes.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    rng = np.random.default_rng(RANDOM_SEED)
    results = [run_episode(episode, rng) for episode in range(1, N_EPISODES + 1)]
    output_dir = Path(__file__).resolve().parent / "outputs"
    save_results(results, output_dir)

    rewards = np.array([r.episode_reward for r in results])
    successes = np.array([r.success for r in results])
    reasons: dict[str, int] = {}
    for result in results:
        reasons[result.terminal_reason] = reasons.get(result.terminal_reason, 0) + 1

    print(f"图片已保存：{output_dir / 'reward_curve_500_episodes.png'}")
    print(f"数据已保存：{output_dir / 'training_results.csv'}")
    print(f"总成功率：{successes.mean() * 100:.1f}%")
    print(f"前 50 回合平均奖励：{rewards[:50].mean():.2f}")
    print(f"后 50 回合平均奖励：{rewards[-50:].mean():.2f}")
    print(f"终止原因统计：{reasons}")


if __name__ == "__main__":
    main()
