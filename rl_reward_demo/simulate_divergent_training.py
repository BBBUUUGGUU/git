"""生成“多参数随机化导致后期不稳定”的 500 回合模拟训练曲线。

本脚本用于检查图表和训练诊断的呈现方式，输出为模拟数据，不代表真实实验。
奖励范围沿用同目录稳定训练脚本的设置：成功回合约 +100，失败回合为负值。
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


N_EPISODES = 500
WINDOW = 50
RANDOM_SEED = 904
SUCCESS_BONUS = 100.0
# 将非平稳训练的成功概率整体压低，使 500 回合成功数维持在约 60～70 次。
SUCCESS_PROBABILITY_SCALE = 0.38


def configure_chinese_font() -> None:
    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei", "SimHei", "Noto Sans SC", "DejaVu Sans"
    ]
    plt.rcParams["axes.unicode_minus"] = False


def moving_average(values: np.ndarray, window: int) -> np.ndarray:
    """计算前向滑动平均，并保留与原数组相同的长度。"""
    result = np.empty(len(values), dtype=float)
    cumulative = np.cumsum(np.insert(values, 0, 0.0))
    for index in range(len(values)):
        start = max(0, index + 1 - window)
        result[index] = (cumulative[index + 1] - cumulative[start]) / (index + 1 - start)
    return result


def scheduled_success_probability(episode: int) -> float:
    """非平稳训练过程：先学习，再受随机化扰动发生多次性能退化。"""
    # 控制点含义：第 1～180 回合先上升；之后任务参数分布变化、探索增大，
    # 成功率多次下降和恢复，末段仍不能稳定收敛。
    control_episodes = np.array(
        [1, 55, 85, 125, 155, 185, 220, 250, 285, 320, 350, 385, 420, 455, 500]
    )
    control_probabilities = np.array(
        [0.00, 0.00, 0.16, 0.62, 0.84, 0.56, 0.14, 0.04, 0.47, 0.62, 0.28, 0.14, 0.48, 0.32, 0.18]
    )
    probability = np.interp(episode, control_episodes, control_probabilities)
    return float(np.clip(SUCCESS_PROBABILITY_SCALE * probability, 0.0, 1.0))


def simulate_episode(episode: int, rng: np.random.Generator) -> tuple[float, int, str]:
    """按当前训练阶段的成功概率，模拟一次具有相同奖励尺度的回合。"""
    probability = scheduled_success_probability(episode)
    success = rng.random() < probability

    if success:
        # 成功奖励 +100，加上少量有效进度 shaping 奖励。
        reward = SUCCESS_BONUS + rng.normal(8.5, 3.2)
        return float(np.clip(reward, 101.0, 117.0)), 1, "success"

    # 失败终止条件和奖励值沿用已有设定；偶发的连续错误会产生更低的累计值。
    reason = rng.choice(
        ["backward", "radial_error", "over_insertion", "time_limit"],
        p=[0.71, 0.15, 0.09, 0.05],
    )
    failure_base = {
        "backward": -40.0,
        "radial_error": -40.0,
        "over_insertion": -60.0,
        "time_limit": -10.0,
    }[reason]
    # 普通步奖励会带来小幅浮动；少量严重探索回合出现更低负奖励。
    reward = failure_base + rng.normal(-1.0, 6.0)
    if rng.random() < 0.08:
        reward -= rng.uniform(12.0, 28.0)
    return float(reward), 0, reason


def write_summary(
    output_path: Path,
    rewards: np.ndarray,
    successes: np.ndarray,
    reasons: list[str],
) -> None:
    counts = Counter(reasons)
    failures = N_EPISODES - int(successes.sum())
    failure_text = "；".join(
        [
            f"轴向后退 {counts['backward']} 次",
            f"径向误差 {counts['radial_error']} 次",
            f"过度插入 {counts['over_insertion']} 次",
            f"步数上限 {counts['time_limit']} 次",
        ]
    )
    content = f"""# 多参数随机化模拟训练统计

| 记录组 | 回合数 | 成功数 | 训练成功比例 | 均值奖励 | 失败构成 |
| --- | ---: | ---: | ---: | ---: | --- |
| 多参数随机化（后期不稳定） | {N_EPISODES} | {int(successes.sum())} | {successes.mean() * 100:.1f}% | {rewards.mean():.2f} | {failure_text} |

说明：本表和对应曲线均为根据既定奖励规则生成的模拟数据。后期波动来自人为设定的非平稳参数扰动和探索，不应作为真实实验结果使用。
"""
    output_path.write_text(content, encoding="utf-8")


def plot_results(
    output_path: Path,
    rewards: np.ndarray,
    successes: np.ndarray,
) -> None:
    configure_chinese_font()
    episodes = np.arange(1, N_EPISODES + 1)
    reward_ma = moving_average(rewards, WINDOW)
    success_ma = 100.0 * moving_average(successes, WINDOW)

    figure, ax_reward = plt.subplots(figsize=(11.2, 3.8), dpi=160)
    ax_reward.plot(
        episodes, rewards, color="#a7b2bf", linewidth=0.65, alpha=0.65,
        label="单回合 Reward",
    )
    ax_reward.plot(
        episodes, reward_ma, color="#0b3f70", linewidth=2.25,
        label="Reward（50回合滑动平均）",
    )
    ax_reward.axhline(
        SUCCESS_BONUS, color="#709f88", linestyle="--", linewidth=0.9, alpha=0.7,
        label="成功终止奖励 +100",
    )
    ax_reward.set_title("累计奖励", loc="left", fontsize=11)
    ax_reward.set_ylabel("Reward")
    ax_reward.set_ylim(-105, 130)
    ax_reward.grid(axis="y", color="#d7dce2", linewidth=0.7, alpha=0.7)
    ax_reward.legend(loc="lower right", fontsize=8, frameon=True, framealpha=0.92)

    # 如需恢复第二幅“50回合窗口成功比例”子图，可取消下方代码注释。
    # ax_success.plot(episodes, success_ma, color="#0b3f70", linewidth=2.25)
    # ax_success.set_title("50回合窗口成功比例（%）", loc="left", fontsize=11)
    # ax_success.set_ylabel("成功比例 (%)")
    # ax_success.set_xlabel("训练回合")
    # ax_success.set_ylim(-2, 102)
    # ax_success.set_yticks([0, 25, 50, 75, 100])
    # ax_success.grid(axis="y", color="#d7dce2", linewidth=0.7, alpha=0.7)
    # ax_success.set_xlim(1, N_EPISODES)

    ax_reward.set_xlabel("训练回合")
    ax_reward.set_xlim(1, N_EPISODES)
    ax_reward.spines["top"].set_visible(False)
    ax_reward.spines["right"].set_visible(False)
    ax_reward.tick_params(axis="both", length=0, colors="#555555")

    figure.suptitle("采用常规单层神经网络的训练曲线", x=0.5, y=0.995, fontsize=13)

    figure.savefig(output_path, bbox_inches="tight")
    figure.savefig(output_path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    rng = np.random.default_rng(RANDOM_SEED)
    reward_values: list[float] = []
    success_values: list[int] = []
    terminal_reasons: list[str] = []
    for episode in range(1, N_EPISODES + 1):
        reward, success, reason = simulate_episode(episode, rng)
        reward_values.append(reward)
        success_values.append(success)
        terminal_reasons.append(reason)

    rewards = np.array(reward_values)
    successes = np.array(success_values)
    output_dir = Path(__file__).resolve().parent / "divergent_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    with (output_dir / "divergent_training_results.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["episode", "episode_reward", "success", "terminal_reason"])
        writer.writerows(zip(range(1, N_EPISODES + 1), rewards, successes, terminal_reasons))

    write_summary(output_dir / "simulation_summary.md", rewards, successes, terminal_reasons)
    plot_results(output_dir / "divergent_reward_curve_500_episodes_clean.png", rewards, successes)

    print(f"曲线：{output_dir / 'divergent_reward_curve_500_episodes_clean.png'}")
    print(f"成功：{successes.sum()} / {N_EPISODES} ({successes.mean() * 100:.1f}%)")
    print(f"均值奖励：{rewards.mean():.2f}")
    print(f"失败构成：{dict(Counter(terminal_reasons))}")


if __name__ == "__main__":
    main()
