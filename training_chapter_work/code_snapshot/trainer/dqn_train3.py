# from test_env import Maze
from MulBotAsm.algorithm.dqn_model import DeepQNetwork
# from MulBotAsm.envs.ur5rl2 import UR5_RL
from coppeliasim_zmqremoteapi_client import RemoteAPIClient
import matplotlib.pyplot as plt
import numpy as np
# from MulBotAsm.envs.DualSpaceArmEnv import DualSpaceArmEnv
# from MulBotAsm.envs.dual_arm_insertion_rl_linear import DualArmInsertionRL
from MulBotAsm.envs.DSAE1 import DualSpaceArmEnv
import os
import json
import csv


def save_randomization_records(save_dir, records):
    np.save(os.path.join(save_dir, 'random_offsets.npy'), np.array(records, dtype=object))
    with open(os.path.join(save_dir, 'random_offsets.json'), 'w') as f:
        json.dump(records, f, indent=2)
    if not records:
        return
    fieldnames = sorted({key for record in records for key in record.keys()})
    with open(os.path.join(save_dir, 'random_offsets.csv'), 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def get_env():
    client = RemoteAPIClient()
    sim = client.getObject('sim')
    client.setStepping(True)
    sim.startSimulation()

    client.step()

    # ControllerParams = {}
    # ControllerParams['Kp'] = np.array([[300, 0, 0, 0, 0, 0],
    #                                    [0, 300, 0, 0, 0, 0],
    #                                    [0, 0, 300, 0, 0, 0],
    #                                    [0, 0, 0, 100, 0, 0],
    #                                    [0, 0, 0, 0, 100, 0],
    #                                    [0, 0, 0, 0, 0, 100]])
    # ControllerParams['Kd'] = ControllerParams['Kp'] * 2
    # ControllerParams['Md'] = ControllerParams['Kp']
    HandlesName = {}
    HandlesName['jointHandles'] = ['/PlaneBase/robot1_joint1',
                                   '/PlaneBase/robot1_joint2',
                                   '/PlaneBase/robot1_joint3',
                                   '/PlaneBase/robot1_joint4',
                                   '/PlaneBase/robot1_joint5',
                                   '/PlaneBase/robot1_joint6',
                                   '/PlaneBase/robot1_joint7',
                                   '/PlaneBase/robot2_joint1',
                                   '/PlaneBase/robot2_joint2',
                                   '/PlaneBase/robot2_joint3',
                                   '/PlaneBase/robot2_joint4',
                                   '/PlaneBase/robot2_joint5',
                                   '/PlaneBase/robot2_joint6',
                                   '/PlaneBase/robot2_joint7']
    HandlesName['robotHandle'] = '/PlaneBase/mulit_base'
    HandlesName['baseHandle'] = '/PlaneBase/Base_joint_x'
    HandlesName['forceHandle'] = ['/PlaneBase/robot1_ee_fixed_joint', '/targetObject/robot2_ee_fixed_joint']
    # Scene check: peg is /mulit_base/object; hole is /targetObject/hole5.
    # Hole was manually enlarged from 18 mm to 22 mm and is not scaled here.
    # The peg object remains a compound shape, so it is scaled uniformly.
    HandlesName['pegSizeHandles'] = ['/mulit_base/object']

    ControllerParams = {}
    # ControllerParams['Kp'] = np.array([[5, 0, 0, 0, 0, 0],
    #                                    [0, 5, 0, 0, 0, 0],
    #                                    [0, 0, 5, 0, 0, 0],
    #                                    [0, 0, 0, 10, 0, 0],
    #                                    [0, 0, 0, 0, 10, 0],
    #                                    [0, 0, 0, 0, 0, 10]])
    # ControllerParams['Kd'] = ControllerParams['Kp'] * 4
    # ControllerParams['Md'] = ControllerParams['Kp']
    ControllerParams['dt'] = 0.005

    # 使用较柔顺的导纳参数，降低接触时的冲击。
    # ControllerParams['Kp'] = np.eye(6) * 100
    # ControllerParams['Kp'] = np.eye(6) * 500
    # ControllerParams['Kd'] = np.eye(6) * 200
    # ControllerParams['Md'] = np.eye(6) * 100  # 增大虚拟质量
    Kp_linear = 100  # 位置刚度(N/m)
    Kp_angular = 30  # 姿态刚度(Nm/rad)
    Kd_linear = 20  # 位置阻尼
    Kd_angular = 160  # 姿态阻尼

    # ControllerParams['Kp'] = np.diag([Kp_linear] * 3 + [Kp_angular] * 3)
    # ControllerParams['Kd'] = np.diag([Kd_linear] * 3 + [Kd_angular] * 3)
    # ControllerParams['Md'] = np.diag([100] * 6)
    ControllerParams['Kp'] = np.array([[180, 0, 0, 0, 0, 0],
                                       [0, 180, 0, 0, 0, 0],
                                       [0, 0, 180, 0, 0, 0],
                                       [0, 0, 0, 80, 0, 0],
                                       [0, 0, 0, 0, 80, 0],
                                       [0, 0, 0, 0, 0, 80]])
    ControllerParams['Kd'] = ControllerParams['Kp'] * 4
    ControllerParams['Md'] = ControllerParams['Kp'] * 1.2

    pinocchio_model_path = "models"
    urdf_path = '\\mulit_arm_urdf\\urdf\\mulit_arm_urdf2.urdf'
    # end_frame = ["robot1_ee_link", "robot2_ee_link"]
    end_frame = ["object_tip", "target_tip"]
    # base_pose = [0, 0, 0.21, 0, 0, 0, 1]
    base_pose = [0, 0, 0.5, 0, 0, 0, 1]
    # base_pose = None
    env = DualSpaceArmEnv(
        client=client, sim=sim, base_pose=base_pose,
        HandlesNames=HandlesName, controllerParams=ControllerParams,
        pinocchio_model_path=pinocchio_model_path, urdf_path=urdf_path,
        end_frame=end_frame,
        linear_step=0.001,
        insertion_step=0.005,
        coarse_insertion_step=0.030,
        action_steps=50,
        force_limit=80.0,
        max_steps=200,
        random_xy_min=0.010,
        random_xy_max=0.025,
        randomize_physical_reset=True,
        max_align_error=0.060,
        pre_insert_distance=0.030,
        reset_preposition_steps=500,
        adaptive_coarse_insertion=True,
        coarse_insert_alignment_gate=0.0015,
        randomize_controller_gains=True,
        kp_linear_scale_range=(0.75, 1.25),
        kp_angular_scale_range=(0.85, 1.15),
        kd_scale_range=(0.80, 1.20),
        md_scale_range=(0.80, 1.20),
        randomize_geometry=True,
        peg_diameter_range=(0.016, 0.021),
        peg_diameter_choices=(0.016, 0.017, 0.018, 0.019, 0.020, 0.021),
        nominal_peg_diameter=0.018,
        fixed_hole_diameter=0.022,
        hole_clearance_range=(0.0005, 0.0020),
        peg_length_axis='x',
        scale_peg_length=True,
        include_domain_params_in_state=True,
        verbose=True,
        debug_interval=20)
    env.action_frame = "left_ee"
    env.control_mode = "admittance"
    return env

def plotSuccess(successList):
    plt.figure()
    plt.plot(np.arange(len(successList)), successList)
    plt.show()
def trainer(env):
    successList = []
    step_rewards = []
    ep_rewards = []
    randomization_records = []
    fail_reasons = {
        'success': 0,
        'over_insertion': 0,
        'out_of_bounds': 0,
        'force_limit': 0,
        'misalignment': 0,
        'timeout': 0,
        'unknown': 0,
    }
    save_dir = 'training_logs_10actions_random_kpkdmd_peg16to21_hole22_200steps_500episodes'
    os.makedirs(save_dir, exist_ok=True)
    for episode in range(500):
        print('------------------------------------------------------------------episode:',episode)
        # initial observation
        step = 0
        ep_reward = 0
        observation = env.reset()
        episode_randomization = dict(getattr(env, 'last_randomization_info', {}))
        episode_randomization['episode'] = episode

        while True:
            # refresh env
            # env.render()

            # RL choose action based on observation
            action = RL.choose_action(observation) # 0-9, env actions 1-10
            # action = action+1
            if step == 0 or step % 20 == 0:
                print('action:', action + 1)

            # RL take action and get next observation and reward
            observation_, reward, done, success, info = env.envStep(action+1)

            step_rewards.append(reward)

            # !! restore transition
            RL.store_transition(observation, action, reward, observation_, done)
            ep_reward += reward
            if step == 0 or step % 20 == 0 or done:
                print('step', step, "reward", reward)

            if (step > 100) and (step % 5 == 0):
                RL.learn()

            # swap observation
            observation = observation_
            step += 1

            # break while loop when end of this episode
            if done:
                # 记录 episode 结果
                success_flag = info.get('success', False)
                print('success:', success_flag)
                print('episode reward:', ep_reward)
                successList.append(int(success_flag))
                ep_rewards.append(ep_reward)
                episode_randomization.update({
                    'success': bool(success_flag),
                    'episode_reward': float(ep_reward),
                    'steps': int(step),
                    'fail_reason': info.get('fail_reason', 'unknown'),
                    'final_alignment_error_m': float(info.get('alignment_error', 0.0)),
                    'final_inserted_depth_m': float(info.get('inserted_depth', 0.0)),
                    'final_approach_progress_m': float(info.get('approach_progress', 0.0)),
                    'final_remaining_x_distance_m': float(info.get('remaining_x_distance', 0.0)),
                    'final_success_alignment_limit_m': float(info.get('success_alignment_limit', 0.0)),
                    'final_peg_diameter_m': float(info.get('peg_diameter_m', 0.0)),
                    'final_hole_diameter_m': float(info.get('hole_diameter_m', 0.0)),
                    'final_hole_clearance_m': float(info.get('hole_clearance_m', 0.0)),
                })
                randomization_records.append(episode_randomization)

                # 统计失败原因
                if success_flag:
                    fail_reasons['success'] += 1
                else:
                    reason = info.get('fail_reason', 'unknown')
                    if reason not in fail_reasons:
                        fail_reasons[reason] = 0
                    fail_reasons[reason] += 1
                    print(f"失败原因: {reason}")

                break

        np.save(os.path.join(save_dir, 'step_rewards.npy'), np.array(step_rewards))
        np.save(os.path.join(save_dir, 'successList.npy'), np.array(successList))
        np.save(os.path.join(save_dir, 'ep_rewards.npy'), np.array(ep_rewards))
        save_randomization_records(save_dir, randomization_records)
        with open(os.path.join(save_dir, 'fail_reasons.json'), 'w') as f:
            json.dump(fail_reasons, f)
        print(f"[保存] 训练数据已写入 {save_dir}")

    # 训练结束后再保存一次，保证最终统计落盘。
    np.save(os.path.join(save_dir, 'step_rewards.npy'), np.array(step_rewards))
    np.save(os.path.join(save_dir, 'successList.npy'), np.array(successList))
    np.save(os.path.join(save_dir, 'ep_rewards.npy'), np.array(ep_rewards))
    save_randomization_records(save_dir, randomization_records)
    with open(os.path.join(save_dir, 'fail_reasons.json'), 'w') as f:
        json.dump(fail_reasons, f)


    print("\n===== 训练统计 =====")
    print(f"成功率: {fail_reasons['success']}/{len(successList)}")
    for reason, count in fail_reasons.items():
        print(f"{reason}: {count}")

    # 绘制每步 reward 曲线。
    plt.figure()
    plt.plot(step_rewards)
    plt.title('Step Rewards over Training')
    plt.xlabel('Step')
    plt.ylabel('Reward')
    plt.show()


    # end of game
    print("Train end")
    # env.destroy()
    return successList

if __name__ == "__main__":
    # maze game
    env = get_env()
    # action 1: fine insert; 2-9: planar moves; action 10: adaptive coarse insert.
    state_dim = getattr(env, 'state_dim', 16)
    print(f"RL state dimension: {state_dim}")
    RL = DeepQNetwork(10, state_dim,
                      learning_rate=0.0005,
                      reward_decay=0.95,
                      e_greedy=0.9,
                      replace_target_iter=300,
                      memory_size=10000,
                      batch_size=64,
                      e_greedy_increment=0.0004)
    # env.after(100, run_maze)
    # env.mainloop()
    successList=trainer(env)
    RL.save("dqn_dual_arm_insertion_random_kpkdmd_peg16to21_hole22.pth")
    plotSuccess(successList)
    RL.plot_cost()
