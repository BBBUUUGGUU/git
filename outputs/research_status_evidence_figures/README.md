# 接触式装配研究现状：论文原图支撑包

用途：为“研究现状 → 已暴露问题 → 技术需求”的一页汇报提供原论文图示。图片均保留论文图号，使用时应在图片下方标注来源，不应将论文成果图直接写成“本研究成果”。

## 最推荐的四幅主图

### 1. 高并行接触仿真已经形成

- 文件：`01_Factory_Fig1_parallel_simulation.png`
- 来源：Narang et al., *Factory: Fast Contact for Robotic Assembly*, RSS 2022, Fig. 1.
- 正式论文集：https://www.roboticsproceedings.org/rss18/p035.html
- DOI：`10.15607/RSS.2022.XVIII.035`
- 图示内容：Isaac Gym 中 128 个 Franka 机器人并行执行螺母—螺栓接触任务。
- 可支撑的现状表述：GPU 并行仿真已能为接触密集装配提供大规模训练数据。
- 可推出的不足与需求：已有平台主要针对地面固定基座与典型工业装配；空间双臂、基座漂移、动力学耦合和视觉—力觉闭环仍需专门建模。

### 2. 视觉—力觉融合已进入端到端策略学习

- 文件：`04_Jin2023_Fig1_vision_force_framework.webp`
- 来源：Jin et al., *Vision-force-fused curriculum learning for robotic contact-rich assembly tasks*, Frontiers in Neurorobotics, 2023, Fig. 1.
- 原文：https://doi.org/10.3389/fnbot.2023.1280773
- 图示内容：双腕部相机、六维力/力矩传感器、视觉—力觉特征融合、课程学习策略和笛卡尔运动/力控制器。
- 可支撑的现状表述：视觉负责较大范围定位，力觉补充接触状态，融合策略能够覆盖从对准到插入的闭环。
- 可推出的不足与需求：视觉与力觉在维度、频率和噪声上差异明显，需要阶段感知、时序表征和稳定的连续动作控制。

### 3. 控制先验与强化学习融合已证明有效

- 文件：`06_Johannink2019_Fig1_residual_RL.png`
- 来源：Johannink et al., *Residual Reinforcement Learning for Robot Control*, ICRA 2019, Fig. 1.
- 正式出版（IEEE ICRA 2019）：https://doi.org/10.1109/ICRA.2019.8794127
- 图示内容：手工控制器与残差强化学习控制量叠加，并在真实接触装配任务中执行纠偏。
- 可支撑的现状表述：残差强化学习不是从零学习全部运动，而是在基础控制器上学习接触与模型误差补偿。
- 可推出的不足与需求：面向高精度空间插拔，应把阻抗/导纳先验、残差幅值约束和视觉—力觉状态共同纳入连续残差策略。

### 4. 空间机器人研究已经关注动力学耦合，但验证仍以仿真为主

- 文件：`08_Wu2025_Fig3_space_assembly_model.jpg`
- 来源：武黎明等，《基于强化学习的空间机器人在轨装配柔顺控制方法》，《机器人》2025，图3。
- 原文：https://doi.org/10.13973/j.cnki.robot.240135
- 期刊页：https://robot.sia.cn/cn/article/doi/10.13973/j.cnki.robot.240135
- 图示内容：自由漂浮基座、机械臂、末端执行器与矩形轴孔装配模型，标示轴孔间隙 1 mm。
- 可支撑的现状表述：空间装配研究开始将基座漂移、机器人—结构耦合和紧间隙插入纳入强化学习建模。
- 可推出的不足与需求：仍需由单臂/简化仿真扩展到空间双臂分工、视觉—力觉反馈、接触参数随机化以及实物闭环验证。

> 注：上面的 DOI 正确写法为 `10.13973/j.cnki.robot.240135`；期刊网页为权威入口。

## 迁移与泛化的补充图

### IndustReal：仿真到真实的完整装配链路

- 文件：`02_IndustReal_Fig1_sim_to_real.png`
- 来源：Tang et al., *IndustReal: Transferring Contact-Rich Assembly Tasks from Simulation to Reality*, RSS 2023, Fig. 1.
- 正式论文集：https://www.roboticsproceedings.org/rss19/p039.html
- DOI：`10.15607/RSS.2023.XIX.039`
- 适合支撑：仿真学习、仿真误差抑制、课程学习、部署误差补偿和实物迁移已经形成系统路线。
- 使用边界：其成果不能直接证明空间双臂可迁移，只能说明地面固定基座装配中的 sim-to-real 路线已经可行。

### AutoMate：跨几何对象的专用/通用策略

- 文件：`03_AutoMate_Fig1_diverse_assembly.png`
- 来源：Tang et al., *AutoMate: Specialist and Generalist Assembly Policies over Diverse Geometries*, 2024, Fig. 1.
- 正式论文集（RSS 2024）：https://www.roboticsproceedings.org/rss20/p064.html
- DOI：`10.15607/RSS.2024.XX.064`
- 适合支撑：研究已由单一零件策略扩展到多对象专用策略、通用策略和零样本实物迁移。
- 使用边界：其对象多样性不等于空间工况泛化；空间动力学变化与双臂耦合仍是新的任务分布。

### 视觉—力觉课程式融合

- 文件：`05_Jin2023_Fig4_curriculum_fusion.webp`
- 来源：Jin et al., 2023, Fig. 4.
- 适合支撑：先在 0.5 mm 间隙中学习视觉策略，再在 0.1 mm 间隙中加入力觉特征，体现“由易到难、由自由空间到接触空间”的训练逻辑。

## 空间场景补充图

- `07_Wu2025_Fig1_on_orbit_scenario.jpg`：在轨装配任务阶段与自由漂浮基座场景。
- `09_Wu2025_Fig5_model_data_hybrid.jpg`：关节阻抗先验与强化学习策略结合的模型—数据混合框架。

## 一页汇报的推荐逻辑

1. 上排放 4 幅原论文图：Factory Fig.1、Jin Fig.1、Johannink Fig.1、武黎明等 Fig.3。
2. 每幅图下只写一句“已经做到什么”，避免大段算法名称。
3. 下排用箭头对应三项需求：
   - 地面并行仿真 → 空间双臂高拟真视觉—力觉接触环境；
   - 多模态融合与残差控制 → 启发式先验约束的连续残差柔顺策略；
   - 地面 sim-to-real 与跨几何泛化 → 面向环境参数和任务参数变化的跨环境、跨任务迁移。
4. 结论句建议写为：

   “现有研究已验证并行仿真、多模态感知、残差学习和虚实迁移的可行性，但这些能力尚未在空间双臂高精度插拔场景中形成统一的训练—控制—迁移闭环。”

## 引图标注模板

`图片来源：作者等，论文题目，期刊/会议，年份，Fig. X。`

论文图用于学位论文或答辩展示时建议保留原图号和来源；若公开发表或商用，应进一步核对出版社许可。

## 正式发表状态核对

- Narang et al., *Factory: Fast Contact for Robotic Assembly*: Robotics: Science and Systems XVIII, 2022, DOI `10.15607/RSS.2022.XVIII.035`.
- Tang et al., *IndustReal: Transferring Contact-Rich Assembly Tasks from Simulation to Reality*: Robotics: Science and Systems XIX, 2023, DOI `10.15607/RSS.2023.XIX.039`.
- Tang et al., *AutoMate: Specialist and Generalist Assembly Policies over Diverse Geometries*: Robotics: Science and Systems XX, 2024, DOI `10.15607/RSS.2024.XX.064`.
- Johannink et al., *Residual Reinforcement Learning for Robot Control*: IEEE ICRA 2019, pp. 6023-6029, DOI `10.1109/ICRA.2019.8794127`.
- Jin et al., *Vision-force-fused curriculum learning for robotic contact-rich assembly tasks*: Frontiers in Neurorobotics, 2023, DOI `10.3389/fnbot.2023.1280773`.
- 武黎明等，《基于强化学习的空间机器人在轨装配柔顺控制方法》：《机器人》，2025，47(2): 239-248, 258，DOI `10.13973/j.cnki.robot.240135`.

另可补充一篇正式发表且与本课题路线高度相关的论文：Zhang et al., *Efficient Sim-to-real Transfer of Contact-Rich Manipulation Skills with Online Admittance Residual Learning*, CoRL 2023, PMLR 229:1621-1639，正式论文集：https://proceedings.mlr.press/v229/zhang23e.html 。该文可用于支撑“导纳控制先验 + 在线残差学习 + 虚实迁移”的技术需求。

ArXiv 只保留为必要时的全文镜像，不作为本资料包的主要出版来源。
