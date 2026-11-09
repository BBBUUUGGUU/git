# -*- coding:utf-8 -*-

import os
os.environ['SSL_CERT_FILE'] = ''
# import cv2
import sys
import math
import time
import random
import string
# import pygame
import MulBotAsm.sim
import numpy as np
import matplotlib.pyplot as plt
# import scipy
from sympy import Matrix, zeros

from coppeliasim_zmqremoteapi_client import RemoteAPIClient
# from pyquaternion import Quaternion
# import numpy_quaternion as quat
# import quaternion
from scipy.spatial.transform import Rotation as R
from MulBotAsm.envs.DualSpaceArmController import DualSpaceArmController
from scipy import signal
import pinocchio as pin
# from coppeliasim_zmqremoteapi_client import RemoteAPIClient
# env = DualSpaceArmEnv(
#     client=client, sim=sim, base_pose=base_pose,
#     HandlesNames=HandlesName, controllerParams=ControllerParams,
#     pinocchio_model_path=pinocchio_model_path, urdf_path=urdf_path,
#     end_frame=end_frame,
#     insertion_depth=0.05,  # 需要插入的深度
#     max_steps=1000,  # 每个回合最大步数
#     success_radial_tol=0.002,  # 径向成功阈值 (2mm)
#     success_angle_tol=0.05,  # 角度成功阈值 (约2.8°)
#     force_limit=80.0  # 力/力矩上限
# )
class DualSpaceArmEnv:
    # communication and read the handles
    def __init__(self, client=None, sim=None, base_pose=None, HandlesNames=None,
                 controllerParams=None, pinocchio_model_path=None, urdf_path=None,
                 end_frame=None, end_joint=None,
                 linear_step=0.001, insertion_step=0.002, coarse_insertion_step=0.030,
                 action_steps=20, force_limit=80.0, max_steps=200,
                 random_xy_min=0.010, random_xy_max=0.025,
                 randomize_physical_reset=False, max_align_error=0.050,
                 pre_insert_distance=0.030, reset_preposition_steps=300,
                 adaptive_coarse_insertion=True, coarse_insert_alignment_gate=0.0015,
                 randomize_controller_gains=False,
                 kp_linear_scale_range=(1.0, 1.0), kp_angular_scale_range=(1.0, 1.0),
                 kd_scale_range=(1.0, 1.0), md_scale_range=(1.0, 1.0),
                 randomize_geometry=False, peg_diameter_range=(0.018, 0.018),
                 peg_diameter_choices=None,
                 nominal_peg_diameter=None,
                 fixed_hole_diameter=0.021,
                 hole_clearance_range=(0.0010, 0.0010),
                 peg_length_axis='x', scale_peg_length=False,
                 include_domain_params_in_state=False,
                 verbose=True, debug_interval=20):
        self.client = client
        self.sim = sim
        self.dt = controllerParams['dt']
        # self.simIK = self.client.getObject('simIK')
        # self.simOMPL = self.client.getObject('simOMPL')
        self.controller = DualSpaceArmController(controllerParams['Kp'],controllerParams['Kd'],
                                        controllerParams['Md'],self.dt,
                                        pinocchio_model_path, urdf_path,
                                        end_frame=end_frame,end_joint=end_joint)
        self.nominal_Kp = np.array(controllerParams['Kp'], dtype=float).copy()
        self.nominal_Kd = np.array(controllerParams['Kd'], dtype=float).copy()
        self.nominal_Md = np.array(controllerParams['Md'], dtype=float).copy()
        print('Simulation started')
        self.HandlesName = HandlesNames
        self.base_pose = base_pose
        self.jointNum = 6
        self.RAD2DEG=180 / math.pi
        self.robotNum = 2
        self.gravity = 0
        self.getHandles()

        ###0706新增
        self.current_step = 0
        self.linear_step = linear_step
        self.insertion_step = insertion_step
        self.coarse_insertion_step = coarse_insertion_step
        self.adaptive_coarse_insertion = adaptive_coarse_insertion
        self.coarse_insert_alignment_gate = coarse_insert_alignment_gate
        self.coarse_linear_scale = 10.0
        self.action_steps = action_steps
        self.force_limit = force_limit
        self.max_steps = max_steps
        self.action_frame = "left_ee"
        self.control_mode = "admittance"
        self.random_xy_min = random_xy_min
        self.random_xy_max = random_xy_max
        self.randomize_physical_reset = randomize_physical_reset
        self.max_align_error = max_align_error
        self.pre_insert_distance = pre_insert_distance
        self.reset_preposition_steps = reset_preposition_steps
        self.randomize_controller_gains = randomize_controller_gains
        self.kp_linear_scale_range = kp_linear_scale_range
        self.kp_angular_scale_range = kp_angular_scale_range
        self.kd_scale_range = kd_scale_range
        self.md_scale_range = md_scale_range
        self.randomize_geometry = randomize_geometry
        self.peg_diameter_range = peg_diameter_range
        self.peg_diameter_choices = peg_diameter_choices
        self.fixed_hole_diameter = fixed_hole_diameter
        self.hole_clearance_range = hole_clearance_range
        self.peg_length_axis = peg_length_axis
        self.scale_peg_length = scale_peg_length
        self.include_domain_params_in_state = include_domain_params_in_state
        if nominal_peg_diameter is None:
            nominal_peg_diameter = np.mean(peg_diameter_range)
        self.nominal_peg_diameter = float(nominal_peg_diameter)
        self.current_domain_params = {}
        self.success_alignment_limit = 0.0005
        self.state_dim = 16 + (6 if self.include_domain_params_in_state else 0)
        self.peg_geometry_scale = 1.0
        self.hole_geometry_scale = 1.0
        self.verbose = verbose
        self.debug_interval = debug_interval

        # 初始轴孔相对位姿
        self.init_peg_pos = np.array([-1.95461612e-05, -7.59770266e-07, -1.67794560e-01])
        self.target_peg_pos_in_hole = self.init_peg_pos.copy()
        self.target_peg_quat_in_hole = np.array([-2.51612004e-11, 1.00000000e+00, -4.33366912e-06, -2.17118061e-06])

        # 右臂固定 PD 目标角度初始化：实时抓取仿真开始时的右臂角度
        obs_init = self.getObs()
        self.right_joint_target = np.array(obs_init[0])[7:14].copy()

    def _sample_range(self, value_range):
        low, high = value_range
        if low == high:
            return float(low)
        return float(np.random.uniform(low, high))

    def _sample_peg_diameter(self):
        if self.peg_diameter_choices:
            return float(np.random.choice(self.peg_diameter_choices))
        return self._sample_range(self.peg_diameter_range)

    def _scale_matrix(self, matrix, linear_scale, angular_scale):
        scaled = np.array(matrix, dtype=float).copy()
        scaled[:3, :3] *= linear_scale
        scaled[3:, 3:] *= angular_scale
        return scaled

    def _normalize_range(self, value, value_range):
        low, high = value_range
        if high == low:
            return 0.0
        return float(2.0 * (value - low) / (high - low) - 1.0)

    def _domain_state(self):
        if not self.include_domain_params_in_state:
            return np.array([], dtype=float)
        params = self.current_domain_params
        return np.array([
            self._normalize_range(params.get('kp_linear_scale', 1.0), self.kp_linear_scale_range),
            self._normalize_range(params.get('kp_angular_scale', 1.0), self.kp_angular_scale_range),
            self._normalize_range(params.get('kd_scale', 1.0), self.kd_scale_range),
            self._normalize_range(params.get('md_scale', 1.0), self.md_scale_range),
            self._normalize_range(params.get('peg_diameter_m', self.nominal_peg_diameter), self.peg_diameter_range),
            self._normalize_range(params.get('hole_clearance_m', np.mean(self.hole_clearance_range)),
                                  self.hole_clearance_range),
        ], dtype=float)

    def _apply_geometry_scale(self, handles, current_scale_attr, target_scale, radial_only=False, length_axis='x'):
        if not handles:
            return False
        current_scale = getattr(self, current_scale_attr, 1.0)
        relative_scale = target_scale / max(current_scale, 1e-9)
        scale_xyz = [relative_scale, relative_scale, relative_scale]
        if radial_only:
            axis_index = {'x': 0, 'y': 1, 'z': 2}.get(str(length_axis).lower(), 0)
            scale_xyz[axis_index] = 1.0
        applied = False
        for handle in handles:
            try:
                self.sim.scaleObject(int(handle), scale_xyz[0], scale_xyz[1], scale_xyz[2], 0)
                applied = True
            except Exception as exc:
                print(f"[尺寸随机化] 缩放对象失败 handle={handle}: {exc}")
        if applied:
            setattr(self, current_scale_attr, target_scale)
        return applied

    def _sample_and_apply_domain_randomization(self):
        kp_linear_scale = self._sample_range(self.kp_linear_scale_range) if self.randomize_controller_gains else 1.0
        kp_angular_scale = self._sample_range(self.kp_angular_scale_range) if self.randomize_controller_gains else 1.0
        kd_scale = self._sample_range(self.kd_scale_range) if self.randomize_controller_gains else 1.0
        md_scale = self._sample_range(self.md_scale_range) if self.randomize_controller_gains else 1.0

        self.controller.Kp = self._scale_matrix(self.nominal_Kp, kp_linear_scale, kp_angular_scale)
        self.controller.Kd = self.nominal_Kd * kd_scale
        self.controller.Md = self.nominal_Md * md_scale

        peg_diameter = self._sample_peg_diameter() if self.randomize_geometry else self.nominal_peg_diameter
        hole_diameter = self.fixed_hole_diameter
        hole_clearance = max((hole_diameter - peg_diameter) * 0.5, 0.0001)
        peg_scale = peg_diameter / max(self.nominal_peg_diameter, 1e-9)
        peg_scaled = self._apply_geometry_scale(
            getattr(self, 'pegSizeHandles', []),
            'peg_geometry_scale',
            peg_scale,
            radial_only=not self.scale_peg_length,
            length_axis=self.peg_length_axis)

        self.success_alignment_limit = float(np.clip(hole_clearance * 0.75, 0.00035, 0.0012))
        self.current_domain_params = {
            'kp_linear_scale': kp_linear_scale,
            'kp_angular_scale': kp_angular_scale,
            'kd_scale': kd_scale,
            'md_scale': md_scale,
            'peg_diameter_m': float(peg_diameter),
            'hole_diameter_m': float(hole_diameter),
            'hole_clearance_m': float(hole_clearance),
            'success_alignment_limit_m': float(self.success_alignment_limit),
            'peg_geometry_scale': float(peg_scale),
            'hole_geometry_scale': 1.0,
            'physical_peg_scaled': bool(peg_scaled),
            'physical_hole_scaled': False,
            'peg_length_axis': self.peg_length_axis,
            'scale_peg_length': bool(self.scale_peg_length),
            'peg_diameter_choices_m': list(self.peg_diameter_choices) if self.peg_diameter_choices else [],
        }
        if self.verbose:
            print(
                f"[域随机化] Kp(linear/angular)=({kp_linear_scale:.2f}, {kp_angular_scale:.2f}), "
                f"Kd={kd_scale:.2f}, Md={md_scale:.2f}, "
                f"peg={peg_diameter * 1000:.2f}mm, hole={hole_diameter * 1000:.2f}mm, "
                f"clearance={hole_clearance * 1000:.2f}mm, "
                f"peg_scale={peg_scale:.3f}, physical_peg_scaled={bool(peg_scaled)}")
            if self.randomize_geometry and not peg_scaled:
                print("[尺寸随机化] 警告：本回合只记录了轴径参数，未成功缩放 CoppeliaSim 里的轴对象。")

        # 2. 标准重置函数：现在它属于类本身的方法了
    def reset(self):
        self.sim.stopSimulation()
        while self.sim.getSimulationState() != self.sim.simulation_stopped:
            time.sleep(0.005)
        self.sim.startSimulation()
        self.client.step()
        self._sample_and_apply_domain_randomization()

        # 重置环境内部计数与目标
        self.current_step = 0
        self.target_peg_pos_in_hole = self.init_peg_pos.copy()

        # 重新同步锁死右臂当前角度
        obs = self.getObs()
        self.right_joint_target = np.array(obs[0])[7:14].copy()

        baseObs = self.getBaseObs()

        # 【0717新增：动态感知初始偏差】
        left_pose_m, right_pose_m = self._get_pinocchio_poses(obs, baseObs)
        self.initial_left_yz = left_pose_m[1:3, 3].copy()
        self.initial_hole_yz_offset = left_pose_m[1:3, 3] - right_pose_m[1:3, 3]
        initial_left_x = left_pose_m[0, 3]
        initial_right_x = right_pose_m[0, 3]
        #0806添加两行
        right_pose = np.array(obs[16]).reshape(3, 4)
        self.T_hole_world_fixed = self._pose_to_transform(right_pose)
        print('initial_left_x',initial_left_x)
        print('initial_right_x',initial_right_x)

        sample_angle = np.random.uniform(0.0, 2.0 * np.pi)
        sample_radius = np.random.uniform(self.random_xy_min, self.random_xy_max)
        xySample = sample_radius * np.array([np.cos(sample_angle), np.sin(sample_angle)])

        print(f"🎲 [域随机化] 初始径向偏差 X: {xySample[0] * 1000:.2f}mm, Y: {xySample[1] * 1000:.2f}mm")
        actual_relative_offset = np.zeros(2)
        actual_hole_offset = self.initial_hole_yz_offset.copy()

        # 3. 将随机偏置应用到动作或控制器的目标位姿上
        # (假设你用 target_peg_pos_in_hole 追踪目标位姿)
        self.target_peg_pos_in_hole = self.init_peg_pos.copy()
        self.target_peg_pos_in_hole[0] += xySample[0]  # 注入孔坐标 X 轴初始径向偏差
        self.target_peg_pos_in_hole[1] += xySample[1]  # 注入孔坐标 Y 轴初始径向偏差
        self.target_peg_pos_in_hole[2] = self.init_peg_pos[2]  # 孔坐标 Z 轴为插入方向，保持初始安全距离

        if self.randomize_physical_reset:
            relative_world_offset = np.array([0.0, xySample[0], xySample[1]])
            requested_offset_norm = np.linalg.norm(relative_world_offset[1:3])
            obs, baseObs, left_pose_m, right_pose_m = self._preposition_left_relative_offset(
                obs, baseObs, relative_world_offset)
            initial_left_x = left_pose_m[0, 3]
            initial_right_x = right_pose_m[0, 3]
            actual_hole_offset = left_pose_m[1:3, 3] - right_pose_m[1:3, 3]
            actual_relative_offset = actual_hole_offset - self.initial_hole_yz_offset
            actual_relative_offset_norm = np.linalg.norm(actual_relative_offset)
            print(
                f" [物理随机化] 左臂相对初始漂移目标 worldY/worldZ: "
                f"{relative_world_offset[1] * 1000:.2f}mm, {relative_world_offset[2] * 1000:.2f}mm | "
                f"实际: {actual_relative_offset[0] * 1000:.2f}mm, {actual_relative_offset[1] * 1000:.2f}mm | "
                f"最终轴孔偏差: {actual_hole_offset[0] * 1000:.2f}mm, {actual_hole_offset[1] * 1000:.2f}mm")
            if actual_relative_offset_norm < requested_offset_norm * 0.7:
                print(
                    f"⚠️ [物理随机化] 实际漂移只有目标的 "
                    f"{actual_relative_offset_norm / max(requested_offset_norm, 1e-9) * 100:.1f}%，可增加 reset_preposition_steps。")

        self.initial_x_distance = abs(initial_left_x - initial_right_x)
        print(f"🔄 [环境重置] 动态感知初始轴孔 X 轴物理距离: {self.initial_x_distance * 1000:.2f} mm")
        self.last_randomization_info = {
            'target_offset_y_m': float(xySample[0]),
            'target_offset_z_m': float(xySample[1]),
            'target_offset_norm_m': float(np.linalg.norm(xySample)),
            'actual_offset_y_m': float(actual_relative_offset[0]),
            'actual_offset_z_m': float(actual_relative_offset[1]),
            'actual_offset_norm_m': float(np.linalg.norm(actual_relative_offset)),
            'final_hole_offset_y_m': float(actual_hole_offset[0]),
            'final_hole_offset_z_m': float(actual_hole_offset[1]),
            'final_hole_offset_norm_m': float(np.linalg.norm(actual_hole_offset)),
            'initial_x_distance_m': float(self.initial_x_distance),
            'randomize_physical_reset': bool(self.randomize_physical_reset),
        }
        self.last_randomization_info.update(self.current_domain_params)
        self.initial_rel_pos = self.target_peg_pos_in_hole.copy()
        self.prev_x_distance = self.initial_x_distance
        self.prev_alignment_error = np.linalg.norm(left_pose_m[1:3, 3] - right_pose_m[1:3, 3])
        # 重置环境内部的时间步计数
        self.current_step = 0

        return self._get_state(obs, baseObs)


    # 3. 内部状态拼接函数
    def _get_state(self, obs, baseObs):
        left_pose_m, right_pose_m = self._get_pinocchio_poses(obs, baseObs)
        dx = left_pose_m[0, 3] - right_pose_m[0, 3]
        dy = left_pose_m[1, 3] - right_pose_m[1, 3]
        dz = left_pose_m[2, 3] - right_pose_m[2, 3]
        pos_err = np.array([abs(dx), dy, dz])
        force_raw = np.array(obs[4])
        force_lin = force_raw[0:3]
        force_ang = force_raw[3:6]
        joint_pos_left = np.array(obs[0])[0:7]
        return np.concatenate((pos_err, force_lin, force_ang, joint_pos_left, self._domain_state()))

    def _preposition_left_relative_offset(self, obs, baseObs, relative_world_offset):
        left_pose_m, right_pose_m = self._get_pinocchio_poses(obs, baseObs)
        target_pos_left = left_pose_m[:3, 3].copy() + relative_world_offset
        target_rot_left = left_pose_m[:3, :3].copy()
        target_pos_right = right_pose_m[:3, 3].copy()
        target_rot_right = right_pose_m[:3, :3].copy()

        for _ in range(self.reset_preposition_steps):
            obs_loop = self.getObs()
            self._control_both_arms(
                [target_pos_left, target_pos_right],
                [target_rot_left, target_rot_right],
                obs_loop)
            self.client.step()

        obs = self.getObs()
        baseObs = self.getBaseObs()
        left_pose_m, right_pose_m = self._get_pinocchio_poses(obs, baseObs)
        self.right_joint_target = np.array(obs[0])[7:14].copy()
        return obs, baseObs, left_pose_m, right_pose_m

    def _solve_left_reset_config(self, obs, baseObs, world_offset):
        ctrl = self.controller
        current_config = np.array(obs[0]).copy()
        sim_config = current_config.copy()
        current_config[2] = -current_config[2]
        current_config[9] = -current_config[9]

        q = np.concatenate((self.base_pose, current_config))
        left_pose_m, right_pose_m = self._get_pinocchio_poses(obs, baseObs)
        initial_left_yz = left_pose_m[1:3, 3].copy()
        initial_hole_offset = initial_left_yz - right_pose_m[1:3, 3]
        target_yz = initial_left_yz + world_offset[1:3]
        desired_hole_offset = initial_hole_offset + world_offset[1:3]
        start_left_pin = current_config[:7].copy()
        damp = 1e-2
        max_joint_delta = 0.35
        max_iter_step = 0.025
        frame_id = ctrl.frame_ide[0]

        for _ in range(160):
            pin.forwardKinematics(ctrl.model, ctrl.data, q)
            pin.updateFramePlacements(ctrl.model, ctrl.data)
            current_pos = ctrl.data.oMf[frame_id].translation.copy()
            err = target_yz - current_pos[1:3]
            if np.linalg.norm(err) < 5e-4:
                break
            jacobian = pin.computeFrameJacobian(ctrl.model, ctrl.data, q, frame_id, pin.WORLD)[1:3, 6:13]
            dq_left = jacobian.T @ np.linalg.solve(jacobian @ jacobian.T + damp * np.eye(2), err)
            dq_left = np.clip(0.35 * dq_left, -max_iter_step, max_iter_step)
            v = np.zeros(ctrl.model.nv)
            v[6:13] = dq_left
            q = pin.integrate(ctrl.model, q, v)
            q[7:14] = start_left_pin + np.clip(q[7:14] - start_left_pin, -max_joint_delta, max_joint_delta)

        target_config = q[7:].copy()
        target_config[2] = -target_config[2]
        target_config[9] = -target_config[9]
        target_config[7:14] = sim_config[7:14]

        verify_config = target_config.copy()
        verify_config[2] = -verify_config[2]
        verify_config[9] = -verify_config[9]
        verify_q = np.concatenate((self.base_pose, verify_config))
        pin.forwardKinematics(ctrl.model, ctrl.data, verify_q)
        pin.updateFramePlacements(ctrl.model, ctrl.data)
        predicted_left = ctrl.data.oMf[ctrl.frame_ide[0]].translation.copy()
        predicted_relative_offset = predicted_left[1:3] - initial_left_yz
        predicted_hole_offset = predicted_left[1:3] - right_pose_m[1:3, 3]
        err_offset = np.linalg.norm(predicted_hole_offset - desired_hole_offset)
        predicted_norm = np.linalg.norm(predicted_relative_offset)
        desired_norm = np.linalg.norm(world_offset[1:3])
        x_drift = abs(predicted_left[0] - left_pose_m[0, 3])
        ik_ok = err_offset < 0.020 and x_drift < 0.020 and predicted_norm < max(desired_norm * 1.8, 0.080)
        return target_config, predicted_relative_offset, predicted_hole_offset, ik_ok

    def _set_left_joint_positions_instant(self, target_config):
        for i in range(7):
            handle = int(self.jointHandles[i])
            value = float(target_config[i])
            self.sim.setJointPosition(handle, value)
            try:
                self.sim.setJointTargetPosition(handle, value)
            except Exception:
                pass

    # 4. 内部奖励计算函数
    def _compute_reward_done(self, obs, baseObs):
        left_pose_m, right_pose_m = self._get_pinocchio_poses(obs, baseObs)
        current_left_xyz = left_pose_m[:3, 3].copy()
        current_right_xyz = right_pose_m[:3, 3].copy()
        T_world_hole = self._pose_to_transform(right_pose_m)
        T_world_peg = self._pose_to_transform(left_pose_m)
        #基座修正
        current_left_xyz[2] += 0.5
        current_right_xyz[2] += 0.5

        # 计算轴在孔局部坐标系下的相对位置
        T_hole_peg = np.linalg.inv(T_world_hole) @ T_world_peg
        current_rel_pos = T_hole_peg[:3, 3]

        # 世界 X 轴为插入方向，世界 Y、·Z 轴为径向开口对齐面
        dx = current_left_xyz[0] - current_right_xyz[0]  # X 轴（插入方向的相对位置）
        dy = current_left_xyz[1] - current_right_xyz[1]  # Y 轴（侧向水平对齐误差）
        dz = current_left_xyz[2] - current_right_xyz[2]  # Z 轴（垂直上下对齐误差）
        # print("dx",dx)
        # print("dy",dy)
        # print("dz",dz)
        alignment_error = np.sqrt(dy ** 2 + dz ** 2)
        current_x_distance = abs(dx)
        travel_distance = self.initial_x_distance - current_x_distance
        PRE_INSERT_DISTANCE = self.pre_insert_distance  # 轴端距离孔端 30mm 以内才认为进入插入阶段
        inserted_depth = max(PRE_INSERT_DISTANCE - current_x_distance, 0.0)
        success = False
        fail_reason = 'running'
        done = False

        MAX_DEPTH = 0.020  # 最大允许插入深度 (20mm)
        MAX_ALIGN_ERROR = self.max_align_error  # 最大允许对齐误差
        MIN_INSERT_DEPTH = -0.050  # 最大允许后退距离 (往反方向退了 50mm)
        MAX_STEPS = self.max_steps  # 每一回合的最大步数限制 (防止无限死循环)
        bounded_depth = min(inserted_depth, MAX_DEPTH)
        prev_x_distance = getattr(self, 'prev_x_distance', current_x_distance)
        prev_alignment_error = getattr(self, 'prev_alignment_error', alignment_error)
        approach_delta = prev_x_distance - current_x_distance
        alignment_delta = prev_alignment_error - alignment_error

        alignment_reward = alignment_delta * 2500.0
        if alignment_error < 0.003:
            approach_reward = approach_delta * 900.0
        elif approach_delta > 0:
            approach_reward = -approach_delta * 250.0
        else:
            approach_reward = approach_delta * 50.0
        center_bonus = max(0.0, 0.003 - alignment_error) * 200.0
        depth_reward = bounded_depth * 20.0
        steady_penalty = -0.02
        base_reward = (
            alignment_reward +
            approach_reward +
            center_bonus +
            depth_reward -
            alignment_error * 8.0 +
            steady_penalty
        )

        self.prev_x_distance = current_x_distance
        self.prev_alignment_error = alignment_error

        if inserted_depth > MAX_DEPTH:
            done = True
            fail_reason = 'over_insertion'
            reward = -60.0
            print(f"💥 [失败] 插入过深 ({inserted_depth * 1000:.1f}mm)！")

        elif alignment_error > MAX_ALIGN_ERROR or travel_distance < MIN_INSERT_DEPTH:
            done = True
            fail_reason = 'out_of_bounds'
            reward = -40.0
            print(f"❌ [失败] 机械臂脱离安全工作区 (误差: {alignment_error * 1000:.1f}mm)！")

        elif self.current_step >= MAX_STEPS:
            done = True
            fail_reason = 'timeout'
            reward = base_reward - 10.0  # 超时按当前状态给分
            print(f"⏳ [失败] 达到最大步数 ({MAX_STEPS}步) 未完成任务，强制终止。")

            # 🌟 你的高精度物理成功判定：孔隙随机化后，对齐阈值跟随当前孔隙变化。
        elif alignment_error < self.success_alignment_limit and inserted_depth >= 0.008:
            success = True
            done = True
            fail_reason = 'none'
            # 你的原始逻辑：基础奖励 + 100.0 的成功大奖
            reward = base_reward + 100.0
            print("🎉 [高精度物理成功] 轴孔实现亚毫米级对齐，并成功插入 8mm！")

        else:
            # 4. 正常步进，游戏继续
            done = False
            reward = base_reward

        info = {
            'success': success,
            'fail_reason': fail_reason,
            'alignment_error': alignment_error,
            'inserted_depth': inserted_depth,
            'approach_progress': travel_distance,
            'remaining_x_distance': current_x_distance,
            'alignment_delta': alignment_delta,
            'approach_delta': approach_delta,
            'center_bonus': center_bonus,
            'success_alignment_limit': self.success_alignment_limit,
            'peg_diameter_m': self.current_domain_params.get('peg_diameter_m', self.nominal_peg_diameter),
            'hole_diameter_m': self.current_domain_params.get('hole_diameter_m', self.nominal_peg_diameter),
            'hole_clearance_m': self.current_domain_params.get('hole_clearance_m', np.mean(self.hole_clearance_range)),
        }
        return reward, done, info

    def _adaptive_coarse_insert_step(self, alignment_error, remaining_x_distance):
        if not self.adaptive_coarse_insertion:
            return self.coarse_insertion_step

        if remaining_x_distance > 0.100:
            return self.coarse_insertion_step
        if remaining_x_distance > 0.060:
            return 0.020 if alignment_error < 0.010 else 0.015
        if remaining_x_distance > self.pre_insert_distance:
            return 0.015 if alignment_error < 0.006 else 0.008
        if alignment_error < self.coarse_insert_alignment_gate:
            return self.insertion_step
        return 0.0

    def _action_delta_in_hole_frame(self, action, coarse_insert_step=None):
        delta_pos = np.zeros(3)
        if action == 1:
            delta_pos[2] -= self.insertion_step
        elif action == 10:
            delta_pos[2] -= self.coarse_insertion_step if coarse_insert_step is None else coarse_insert_step
        else:
            delta_pos += self._plane_action_delta(action)
        return delta_pos

    def _action_delta_in_world_frame(self, action, coarse_insert_step=None):
        delta_pos = np.zeros(3)
        if action == 1:
            delta_pos[2] -= self.insertion_step
        elif action == 10:
            delta_pos[2] -= self.coarse_insertion_step if coarse_insert_step is None else coarse_insert_step
        else:
            delta_pos += self._plane_action_delta(action)
        return delta_pos

    def _action_delta_in_left_ee_frame(self, action, coarse_insert_step=None):
        delta_pos = np.zeros(3)
        if action == 1:
            delta_pos[2] -= self.insertion_step
        elif action == 10:
            delta_pos[2] -= self.coarse_insertion_step if coarse_insert_step is None else coarse_insert_step
        else:
            delta_pos += self._plane_action_delta(action)
        return delta_pos

    def _plane_action_delta(self, action):
        delta_pos = np.zeros(3)
        fine_actions = {
            2: (0, 1.0),
            3: (0, -1.0),
            4: (1, 1.0),
            5: (1, -1.0),
        }
        coarse_actions = {
            6: (0, 1.0),
            7: (0, -1.0),
            8: (1, 1.0),
            9: (1, -1.0),
        }

        if action in fine_actions:
            axis, sign = fine_actions[action]
            delta_pos[axis] = sign * self.linear_step
        elif action in coarse_actions:
            axis, sign = coarse_actions[action]
            delta_pos[axis] = sign * self.linear_step * self.coarse_linear_scale
        return delta_pos

    def _action_delta_to_hole_frame(self, action, left_rotation=None,
                                    alignment_error=0.0, remaining_x_distance=None):
        coarse_insert_step = None
        if action == 10 and remaining_x_distance is not None:
            coarse_insert_step = self._adaptive_coarse_insert_step(alignment_error, remaining_x_distance)

        if self.action_frame == "left_ee":
            if left_rotation is None:
                raise ValueError("left_rotation is required when action_frame is 'left_ee'")
            left_delta = self._action_delta_in_left_ee_frame(action, coarse_insert_step)
            world_delta = left_rotation @ left_delta
            rotation_world_hole = self.T_hole_world_fixed[:3, :3]
            hole_delta = rotation_world_hole.T @ world_delta
            return hole_delta, world_delta

        if self.action_frame == "world":
            world_delta = self._action_delta_in_world_frame(action, coarse_insert_step)
            rotation_world_hole = self.T_hole_world_fixed[:3, :3]
            hole_delta = rotation_world_hole.T @ world_delta
            return hole_delta, world_delta

        hole_delta = self._action_delta_in_hole_frame(action, coarse_insert_step)
        rotation_world_hole = self.T_hole_world_fixed[:3, :3]
        world_delta = rotation_world_hole @ hole_delta
        return hole_delta, world_delta

    # 5. 标准强化学习单步推进函数 envStep
    def envStep(self, action):
        self.current_step += 1
        log_this_step = self.verbose and (self.current_step == 1 or self.current_step % self.debug_interval == 0)
        if log_this_step:
            print("action:", action)

        obs = self.getObs()
        baseObs = self.getBaseObs()
        left_pose, right_pose = self._get_pinocchio_poses(obs, baseObs)
        left_tip_pose = np.array(obs[11]).reshape(3, 4)
        left_tip_rot = left_tip_pose[:3, :3].copy()
        start_left_xyz = left_tip_pose[:3, 3].copy()
        target_rot_left = left_pose[:3, :3].copy()
        target_pos_right = right_pose[:3, 3].copy()
        target_rot_right = right_pose[:3, :3].copy()
        current_alignment_error = np.linalg.norm(left_pose[1:3, 3] - right_pose[1:3, 3])
        current_x_distance = abs(left_pose[0, 3] - right_pose[0, 3])

        delta_pos_hole = np.zeros(3)
        delta_pos_world = np.zeros(3)
        if action != 0:
            delta_pos_hole, delta_pos_world = self._action_delta_to_hole_frame(
                action,
                left_tip_rot,
                alignment_error=current_alignment_error,
                remaining_x_distance=current_x_distance,
            )
            self.target_peg_pos_in_hole += delta_pos_hole

        if self.action_frame in ("world", "left_ee"):
            target_pos_left = left_pose[:3, 3].copy() + delta_pos_world
        else:
            peg_pose_hole = np.eye(4)
            peg_pose_hole[:3, :3] = pin.Quaternion(self.target_peg_quat_in_hole).toRotationMatrix()
            peg_pose_hole[:3, 3] = self.target_peg_pos_in_hole
            peg_pose_world = self.T_hole_world_fixed @ peg_pose_hole
            target_pos_left = peg_pose_world[:3, 3]
            target_rot_left = peg_pose_world[:3, :3]
            target_pos_right = self.T_hole_world_fixed[:3, 3]
            target_rot_right = self.T_hole_world_fixed[:3, :3]

        # if log_this_step:
        #     # print("action_frame:", self.action_frame)
        #     # print("delta_pos_hole:", delta_pos_hole)
        #     # print("delta_pos_world:", delta_pos_world)
        #     # print("target_peg_pos_in_hole:", self.target_peg_pos_in_hole)
        #     # print(
        #     #     f"DEBUG 目标 target_pos_left: X={target_pos_left[0]:.4f}, Y={target_pos_left[1]:.4f}, Z={target_pos_left[2]:.4f}")
        #     print(
        #         f"DEBUG 本步左臂目标增量(world): dX={delta_pos_world[0]:.4f}, dY={delta_pos_world[1]:.4f}, dZ={delta_pos_world[2]:.4f}")
            # print("DEBUG CoppeliaSim left_tip_rot(world columns X/Y/Z):\n", left_tip_rot)

        # ----- 2. 执行多步导纳控制（内循环） -----
        for _ in range(self.action_steps):
            obs_list = self.getObs()
            baseObs = self.getBaseObs()
            self._control_both_arms([target_pos_left, target_pos_right], [target_rot_left, target_rot_right],
                                    obs_list)
            self.client.step()
        end_obs = self.getObs()
        end_left_tip_pose = np.array(end_obs[11]).reshape(3, 4)
        real_delta_world = end_left_tip_pose[:3, 3] - start_left_xyz
        if log_this_step:
            print(
                f"   ⏱️ [内循环跟踪] 左臂实际增量(world): dX={real_delta_world[0]:.4f}, dY={real_delta_world[1]:.4f}, dZ={real_delta_world[2]:.4f}")

        # ----- 3. 获取最终状态，计算奖励与终止 -----
        obs = self.getObs()
        baseObs = self.getBaseObs()
        state = self._get_state(obs, baseObs)
        reward, done, info = self._compute_reward_done(obs, baseObs)
        if log_this_step or done:
            print("\n" + "-" * 30 + f" 🤖 Step: {self.current_step} 运行监控 " + "-" * 30)

        # 1. 打印当前的动作与即时奖励
        #     print(f"🎬 触发动作: {action} | 🪙 本步奖励: {reward:.4f}")

        # 2. 从正运动学结果中提取世界坐标系下左右臂末端真实位置 (取前3项平移)
        # 这里调用了你刚才修好的原版 _get_pinocchio_poses
        left_pose_m, right_pose_m = self._get_pinocchio_poses(obs, baseObs)
        current_left_xyz = left_pose_m[:3, 3]
        current_right_xyz = right_pose_m[:3, 3]

        if log_this_step or done:
            print(
                f"📍 左臂末端(轴)世界坐标: X={current_left_xyz[0]:.5f}, Y={current_left_xyz[1]:.5f}, Z={current_left_xyz[2]:.5f}")
            print(
                f"📍 右臂末端(孔)世界坐标: X={current_right_xyz[0]:.5f}, Y={current_right_xyz[1]:.5f}, Z={current_right_xyz[2]:.5f}")

        # 3. 打印你在仿真里的相对目标设定值（用来监控动作改变了哪一轴）
            print(f"🎯 轴孔相对目标位置(target_peg_pos_in_hole): {self.target_peg_pos_in_hole}")

            print(
                f"📐 物理对齐误差: {info['alignment_error'] * 1000:.2f} mm | "
                f"🚶 接近推进量: {info['approach_progress'] * 1000:.2f} mm | "
                f"📏 有效插入深度: {info['inserted_depth'] * 1000:.2f} mm | "
                f"两臂X剩余距离: {info['remaining_x_distance'] * 1000:.2f} mm | "
                f"fail_reason: {info['fail_reason']}")
        # 🟢 请在 DSAE1.py 的 envStep 函数最后的 return 之前插入这行：
        left_tip = np.array(self.getObs()[11]).reshape(3, 4)
        # if log_this_step or done:
            # print(
            #     f"📍 [envStep 实时监测] Action: {action} | 相对目标: {self.target_peg_pos_in_hole} | 左臂世界坐标 Z: {left_tip[2, 3]:.5f}")
        return state, reward, done, info.get('success', False), info


    # 6. 双臂底层驱动映射：左臂导纳，右臂卡死
    def _control_both_arms(self, positions, rotations, obs_list):
        baseObs = self.getBaseObs()
        obs = obs_list

        CurrentConfig = np.array(obs[0]).copy()
        CurrentVelocity = np.array(obs[1]).copy()
        CurrentConfig[2] = -CurrentConfig[2]
        CurrentConfig[9] = -CurrentConfig[9]
        CurrentVelocity[2] = -CurrentVelocity[2]
        CurrentVelocity[9] = -CurrentVelocity[9]

        q = np.concatenate((self.base_pose, CurrentConfig))
        vq = np.concatenate(([0, 0, 0, 0, 0, 0], CurrentVelocity))

        armNum = self.controller.armNum
        force_raw = np.array(obs[4])
        forceSensorMat_list = obs[5]

        sensor_mat_left = np.array(forceSensorMat_list[0]).reshape(3, 4)[:, :3]
        he_lin_left = sensor_mat_left @ force_raw[0:3]
        he_ang_left = sensor_mat_left @ force_raw[3:6]
        he_left = np.concatenate([he_lin_left, he_ang_left])
        # print("he_left: ", he_left)
        he_right = np.zeros(6)
        forceI = [np.zeros(6) for _ in range(armNum)]
        he = [he_left, he_right]
        vd = [np.zeros(6) for _ in range(armNum)]
        ad = [np.zeros(6) for _ in range(armNum)]

        # 控制器输入基座维度修复
        baseObs_fixed = list(baseObs)
        if len(baseObs_fixed[2]) == 3: baseObs_fixed[2] = np.concatenate((baseObs_fixed[2], np.zeros(3)))
        if len(baseObs_fixed[1]) == 3: baseObs_fixed[1] = np.concatenate((baseObs_fixed[1], np.zeros(3)))

        q_cmd, vq_cmd, aq_cmd, Fq, distL, distR = self.controller.AdmittanceController(
            q, vq, Pd=positions, Rd=rotations, vd=vd, ad=ad, forceI=forceI, he=he,
            baseObs=baseObs_fixed, extName='None', time=None
        )

        kp_joint = 1500.0
        kd_joint = 100.0
        right_pos = CurrentConfig[7:14]
        right_vel = CurrentVelocity[7:14]
        error = self.right_joint_target - right_pos
        pd_right = kp_joint * error - kd_joint * right_vel

        targetF = Fq.copy()
        targetF[7:14] = pd_right
        targetF[2] = -targetF[2]
        targetF[9] = -targetF[9]

        self.setJointForce(targetF)

    def _get_pinocchio_poses(self, obs, baseObs):
        """通过Pinocchio正运动学获得左右臂末端在世界系的3x4位姿矩阵"""
        ctrl = self.controller
        CurrentConfig = np.array(obs[0]).copy()

        # 关节角符号修正（与环境一致）
        CurrentConfig[2] = -CurrentConfig[2]
        CurrentConfig[9] = -CurrentConfig[9]
        q = np.concatenate((self.base_pose, CurrentConfig))
        qb = np.array(baseObs[0])
        qbm = np.concatenate((qb, q[3:]))   # 替换基座位置

        pin.forwardKinematics(ctrl.model, ctrl.data, qbm)
        pin.updateFramePlacements(ctrl.model, ctrl.data)

        if ctrl.frame_ide is not None:
            Mtool = [ctrl.data.oMf[ctrl.frame_ide[i]] for i in range(ctrl.armNum)]
        elif ctrl.joint_ide is not None:
            Mtool = [ctrl.data.oMi[ctrl.joint_ide[i]] for i in range(ctrl.armNum)]
        else:
            raise ValueError("No frame or joint ide defined")

        left_pose = np.zeros((3, 4))
        right_pose = np.zeros((3, 4))
        left_pose[:3, :3] = Mtool[0].rotation
        left_pose[:3, 3] = Mtool[0].translation
        right_pose[:3, :3] = Mtool[1].rotation
        right_pose[:3, 3] = Mtool[1].translation

        #发现left和right少了底座啊距离，添加上
        left_pose[2, 3] += 0.5
        right_pose[2, 3] += 0.5
        # print("left_pose", left_pose)
        # print("right_pose", right_pose)
        # print("self.base_pose:", self.base_pose)
        # print("baseObs[0]:", baseObs[0])

        return left_pose, right_pose

    # 2. 🛠️ 同步微调：将 3x4 变换矩阵完美补全为 4x4 标准齐次变换矩阵
    def _pose_to_transform(self, pose_3x4):
        """
        将 3x4 的位姿矩阵补齐为 4x4 的标准齐次变换矩阵
        """
        T = np.eye(4)
        T[:3, :4] = pose_3x4
        return T


    def __del__(self):
        self.sim.stopSimulation()
        print('Simulation end')

    def getHandles(self):
        # print('Simulation started')
        self.jointHandles = np.zeros(14)
        for i in range(14):
            self.jointHandles[i] = self.sim.getObject(self.HandlesName['jointHandles'][i])
        print(self.jointHandles)
        self.robotHandle = self.sim.getObject(self.HandlesName['robotHandle'])  # 找到句柄
        self.baseHandle = self.sim.getObject(self.HandlesName['baseHandle'])
        # self.tipHandle = self.sim.getObject(self.HandlesName['tipHandle'])
        # self.targetHandle = self.sim.getObject(self.HandlesName['targetHandle'])

        self.forceHandle = [self.sim.getObject(self.HandlesName['forceHandle'][i])
                            for i in range(len(self.HandlesName['forceHandle']))]
        self.pegSizeHandles = self._get_optional_object_handles(self.HandlesName.get('pegSizeHandles', []))
        self.holeSizeHandles = self._get_optional_object_handles(self.HandlesName.get('holeSizeHandles', []))

        # for force_path in self.HandlesName['forceHandle']:
        #     try:
        #         handle = self.sim.getObject(force_path)
        #         self.forceHandle.append(handle)
        #     except Exception as e:
        #         print(f"Warning: Force sensor {force_path} not found, skipping. Error: {e}")
        #         self.forceHandle.append(-1)  # 用 -1 占位，防止索引错误

        self.robotScriptHandle = self.sim.getScript(self.sim.scripttype_childscript, self.robotHandle)
        self.baseScriptHandle = self.sim.getScript(self.sim.scripttype_childscript, self.baseHandle)
        # self.objectHandle = self.sim.getObject('/targetObject')
        # print("forcehandle",self.forceHandle)

    def _get_optional_object_handles(self, object_paths):
        handles = []
        seen_handles = set()
        for object_path in object_paths:
            try:
                handle = self.sim.getObject(object_path)
                if int(handle) in seen_handles:
                    continue
                handles.append(handle)
                seen_handles.add(int(handle))
                print(f"[尺寸随机化] 找到对象: {object_path}")
            except Exception:
                print(f"[尺寸随机化] 未找到对象，跳过: {object_path}")
        return handles

    def getObs(self):
        retInts, obs, retStrings, retBuffer = self.sim.callScriptFunction('getObs', self.robotScriptHandle,
                                                                                    list(self.jointHandles), self.forceHandle, [],
                                                                                    'a')
        # currentConf=[]
        # for i in range(self.jointNum):
        #     currentConf.append(self.sim.getJointPosition(self.jointHandles[i]))
        return obs

    def getBaseObs(self):
        retInts, obs, retStrings, retBuffer = self.sim.callScriptFunction('getBaseObs', self.baseScriptHandle,
                                                                                    [], [], [],
                                                                                    'a')
        # currentConf=[]
        # for i in range(self.jointNum):
        #     currentConf.append(self.sim.getJointPosition(self.jointHandles[i]))
        return obs

    def setJointForce(self,force):
        # for i in range(self.jointNum):
        #     self.sim.setJointTargetForce(self.jointHandles[i], force[i])
        # goalConfig = [10, -10, 10, 10, 10, 10, -10]
        retInts, Configs, retStrings, retBuffer = self.sim.callScriptFunction('setJointForce', self.robotScriptHandle,
                                                                              list(self.jointHandles), list(force), [],
                                                                              'a')
    def setJointVelocity(self,Velocitys):
        # for i in range(self.jointNum):
        #     self.sim.setJointTargetForce(self.jointHandles[i], force[i])
        # goalConfig = [10, -10, 10, 10, 10, 10, -10]
        retInts, Configs, retStrings, retBuffer = self.sim.callScriptFunction('setJointVelocity', self.robotScriptHandle,
                                                                              list(self.jointHandles), list(Velocitys), [],
                                                                              'a')
    def PIDcontroller(self,target):
        # for i in range(self.jointNum):
        #     self.sim.setJointTargetForce(self.jointHandles[i], force[i])
        # goalConfig = [10, -10, 10, 10, 10, 10, -10]
        retInts, Configs, retStrings, retBuffer = self.sim.callScriptFunction('PIDcontroller', self.robotScriptHandle,
                                                                              list(self.jointHandles), list(target), [],
                                                                              'a')

    def moveRobotConfig(self,goalConfig):
        # scriptHandle = self.sim.getScript(self.sim.scripttype_childscript, self.robotHandle)
        # goalConfig = [10, -10, 10, 10, 10, 10, -10]
        retInts, currentConfig, retStrings, retBuffer = self.sim.callScriptFunction('moveToConfig', self.robotScriptHandle,
                                                                                list(self.jointHandles), list(goalConfig), [], 'a')
        # distance = np.linalg.norm(np.array(goalConfig) - np.array(currentConfig))
        # while distance > 0.001:
        #     retInts, currentConfig, retStrings, retBuffer = self.sim.callScriptFunction('moveToConfig', scriptHandle,
        #                                                                                 self.jointHandles, goalConfig,
        #                                                                                 [], 'a')
        #     distance = np.linalg.norm(np.array(goalConfig) - np.array(currentConfig))
        return currentConfig

    def getGraspMat(self,obs_list):
        # 计算相对于质心的抓取矩阵，并将其表示在物体坐标系下
        # objectTipMat = np.array(obs_list[0][5])
        objectMat = np.array(obs_list[6]).reshape(3,4) #世界坐标系
        comPosition = np.array(obs_list[10]).reshape(3,4)[:,3] #物体坐标系
        GraspMat = np.zeros((6,6*self.robotNum))
        contactP_o = []
        contactMat_o = []
        for i in range(self.robotNum):
            # obs=obs_list[i]
            contactMati = np.array(obs_list[3][i]).reshape(3,4)[:,0:3]
            contactPositioni = np.array(obs_list[3][i]).reshape(3, 4)[:,3]
            contactPi_o = objectMat[:,0:3].T.dot(contactPositioni - objectMat[:,3]) - comPosition # 物体坐标系
            contactMati_o = objectMat[:, 0:3].T.dot(contactMati) # 物体坐标系
            contactP_o.append(contactPi_o)
            contactMat_o.append(contactMati_o)
            # ri_s = pin.skew(ri_o)
            # Gi = np.eye(6)
            # Gi[3:,0:3] = ri_s
            # GraspMat[:,i*6:i*6+6]=Gi
        return contactP_o,contactMat_o

    def trajPlanner(self,Ps, Pd, currentT, end_time, Rs=None, Rd=None):
        # print(Ps)
        # print(Pd)
        start_position = np.array(Ps)
        # print("start position:",start_position)
        end_position = np.array(Pd)
        # print("end position",end_position)
        dim = 3
        start_vel = np.zeros((len(Ps), dim))
        end_vel = np.zeros((len(Ps), dim))
        start_acc = np.zeros((len(Ps), dim))
        end_acc = np.zeros((len(Ps), dim))
        # 初始化保存每个关节角度、速度和加速度随时间变化的列表
        pp = []
        vv = []
        aa = []

        # 计算a0-a5，并带入多项式中求解曲线
        # for i in range(len(start_position)):
            # 初始状态
            # t = [t_time[0]]
            # q = [start_position[i]]
            # v = [start_vel[i]]
            # a = [start_acc[i]]
            # pp_arm = []
            # vv_arm = []
            # aa_arm = []
        T = end_time
        T2 = T ** 2
        T3 = T ** 3
        T4 = T ** 4
        T5 = T ** 5
        a0 = start_position
        a1 = start_vel
        a2 = start_acc / 2.0
        # print(30*start_angle[i]-30*start_angle[0])
        a3 = (20 * end_position - 20 * start_position - (8 * end_vel + 12 * start_vel) * T - (
                    3 * end_acc - start_acc) * T2) / (2 * T3)
        a4 = (30 * start_position - 30 * end_position + (14 * end_vel + 16 * start_vel) * T + (
                    3 * end_acc - 2 * start_acc) * T2) / (2 * T4)
        a5 = (12 * end_position - 12 * start_position - (6 * end_vel + 6 * start_vel) * T - (
                    end_acc - start_acc) * T2) / (2 * T5)
        print("a0, a1, a2, a3, a4, a5",a0,a1,a2,a3,a4,a5)
        # currentT = np.arange(start_time, end_time, .01)
        # ti = np.arange(start_time, end_time, .01)

        # 求解出角度，角速度，角加速度随某个时间区间随时间变换的曲线
        qi = a0 + a1 * currentT + a2 * currentT ** 2 + a3 * currentT ** 3 + a4 * currentT ** 4 + a5 * currentT ** 5
        vi = a1 + 2 * a2 * currentT + 3 * a3 * currentT ** 2 + 4 * a4 * currentT ** 3 + 5 * a5 * currentT ** 4
        ai = 2 * a2 + 6 * a3 * currentT + 12 * a4 * currentT ** 2 + 20 * a5 * currentT ** 3
            # pp_arm.append(qi)
            # vv_arm.append(vi)
            # aa_arm.append(ai)
            # # 将矩阵转换为List，否则进行数据整合会报错
            # ti = ti.tolist()
            # qi = qi.tolist()
            # vi = vi.tolist()
            # ai = ai.tolist()

            # # 进行数据整合，用来绘制函数图像
            # t = t + ti[1:]
            # q = q + qi[1:]
            # v = v + vi[1:]
            # a = a + ai[1:]
            #
            # pp.append(qi)
            # vv.append(vi)
            # aa.append(ai)
        # plt.figure()
        # for j in range(len(start_position)):
        #     plt.subplot(3, 2, j + 1)
        #
        #     plt.plot(t, pp[j], linestyle=":", color=(1, 0, 0, 1.0), label="angle curve")  # 角度变化曲线
        #     plt.plot(t, vv[j], linestyle="-", color=(1, 0.5, 1, 1.0), label="speed curve")  # 角速度变化曲线
        #     plt.plot(t, aa[j], linestyle="-.", color=(0, 0, 0, 1.0), label="acceleration curve")  # 角加速度变化曲线
        #     plt.title("Angle {}".format(j + 1))
        #     plt.xlabel("Time (s)", x=1)
        #
        #     # plt.rcParams['font.size'] = 15   #设置字体大小
        #     plt.suptitle("5th Polynomial Interpolation (3-DOF-ROBOT)")
        #     plt.grid()  # 显示网格
        #     plt.legend()  # 显示图例
        #
        # plt.tight_layout()  # 调整子图布局
        # plt.show()
        return qi, vi, ai


    def testController(self):
        vq = np.zeros(20)
        q = np.concatenate(([0, 0, 0.5, 0, 0, 0, 1],
                            [0, 1.571, -0.5236, -1.0472, 0.5236, 0, 0],
                            [0, 1.571, -0.5236, -1.0472, 0.5236, 0, 0]))
        Rd = [np.array([[-1.87143752e-04, 6.85423107e-06, 9.99999982e-01],
                        [-9.99999982e-01, 3.67328356e-06, -1.87143777e-04],
                        [-3.67456622e-06, -1.00000000e+00, 6.85354352e-06]]),
              np.array([[1.87197342e-04, -6.85423127e-06, -9.99999982e-01],
                        [9.99999982e-01, -3.67328319e-06, 1.87197367e-04],
                        [-3.67456622e-06, -1.00000000e+00, 6.85354352e-06]])]
        Pd = [np.array([0.43489207, -0.51994866,  2.8506116]), np.array([-0.43489204,  0.51994866,  2.8506116])]
        he = [np.array([0, 0, -100, 0, 0, 0]), np.array([0, 0, -100, 0, 0, 0])]
        obsList = self.getObs()
        baseObsList = self.getBaseObs()
        for i in range(5000):
            q, vq, aq ,Fq= self.controller.AdmittanceController(q,vq,Pd=Pd,Rd=Rd,vd=None,ad=None,he=he,baseObs = baseObsList)
            baseObsList = self.getBaseObs()

            targetF = Fq.copy()
            targetF[2] = -targetF[2]
            targetF[9] = -targetF[9]
            # self.moveRobotConfig(targetq)
            print('targetF:', targetF)
            self.setJointForce(targetF)
            # self.client.step()
            obsList = self.getObs()
            conf = obsList[0]
            vconf = obsList[1]
            conf[2] = - conf[2]
            conf[9] = - conf[9]
            vconf[2] = - vconf[2]
            vconf[9] = - vconf[9]
            q = np.concatenate(([0,0,0.5,0,0,0,1],conf))
            vq = np.concatenate(([0,0,0,0,0,0],vconf))
            # if i % 5==0:
            #     print(i)
            #     self.controller.viz.displayCollisions(False)
            #     self.controller.viz.displayVisuals(True)
            #     self.controller.viz.display(q)
        # DualC.step(q, vq, Pd=Pd, Rd=Rd, he=he, Controller='Admittance')
    def getExternalForce(self,obs_list, objectAcc, contactP_o):
        objectPosition = np.array(obs_list[6]).reshape(3, 4)[:, 3]
        objectMat = np.array(obs_list[6]).reshape(3, 4)[:, 0:3]
        objectVelocity = np.array(obs_list[7])

        forceVector = np.array(obs_list[4])
        forceSensorMat = np.array(obs_list[5])
        forceSensorMat1 = forceSensorMat[0].reshape(3, 4)[:, 0:3]
        forceVector[0:3] = forceSensorMat1.dot(forceVector[0:3])
        forceVector[3:6] = forceSensorMat1.dot(forceVector[3:6])
        forceSensorMat2 = forceSensorMat[1].reshape(3, 4)[:, 0:3]
        forceVector[6:9] = forceSensorMat2.dot(forceVector[6:9])
        forceVector[9:12] = forceSensorMat2.dot(forceVector[9:12])

        objectTipMat = np.array(obs_list[11]).reshape(3,4)
        objectMass = obs_list[8]
        objectInertiaMatrix = np.array(obs_list[9]).reshape(3,3)
        objectInertiaMatrix_P = objectMat.dot(objectInertiaMatrix.dot(objectMat.T))
        tipVector = objectTipMat[:,3] - objectPosition
        M_object = np.eye(6)
        M_object[0:3,0:3] = objectMass * M_object[0:3,0:3]
        M_object[0:3, 3:6] = objectMass * pin.skew(tipVector)
        M_object[3:6, 3:6] = objectInertiaMatrix_P

        Fw_object = np.zeros(6)
        Fw_object[0:3] = -objectMass * pin.skew(objectVelocity[3:6]).dot(pin.skew(objectVelocity[3:6]).dot(tipVector))
        Fw_object[3:6] = pin.skew(objectVelocity[3:6]).dot(objectInertiaMatrix_P.dot(objectVelocity[3:6]))

        Fo_object = np.zeros(6)
        Fo_object[0:3] = objectMass * np.array([0,0,self.gravity])

        # G_object = np.zeros((6,6*self.robotNum))
        # for i in range(self.robotNum):
        #     ri_s = pin.skew(objectMat.dot(contactP_o[i]))
        #     Gi = np.eye(6)
        #     Gi[3:,0:3] = ri_s
        #     G_object[:,i*6:i*6+6]=Gi
        G_object = self.getGMat(obs_list, contactP_o)

        Fi_object = G_object.dot(-forceVector)

        Fh_object = M_object.dot(objectAcc)

        Fe_object = Fh_object + Fw_object - Fi_object - Fo_object
        # Fe_object = Fh_object - Fi_object - Fo_object
        Fe_object[3:6] = Fe_object[3:6] - pin.skew(tipVector).dot(Fe_object[0:3])
        # Fe_object = np.zeros(6)
        return Fe_object, G_object

    def getGMat(self, obs_list, contactP_o):
        objectMat = np.array(obs_list[6]).reshape(3, 4)[:, 0:3]
        G_object = np.zeros((6, 6 * self.robotNum))
        for i in range(self.robotNum):
            ri_s = pin.skew(objectMat.dot(contactP_o[i]))
            Gi = np.eye(6)
            Gi[3:, 0:3] = ri_s
            G_object[:, i * 6:i * 6 + 6] = Gi
        return G_object

    def object_Admittance(self, obs_list, contactP_o, contactMat_o, Pd = None, Rd = None, vPd = None, vRd = None, aPd = None, aRd = None, Fe = None):
        # Kp = np.array([[200, 0, 0, 0, 0, 0],
        #                [0, 200, 0, 0, 0, 0],
        #                [0, 0, 200, 0, 0, 0],
        #                [0, 0, 0, 200, 0, 0],
        #                [0, 0, 0, 0, 200, 0],
        #                [0, 0, 0, 0, 0, 200]])
        # Kd = Kp * 4
        # Md = Kp
        Kp = np.eye(6) * 50
        Kd= np.eye(6) * 20
        Md= np.eye(6) * 100  # 增大虚拟质量，增加惯性滤波效果

        # dt = 0.05
        objectPosition = np.array(obs_list[6]).reshape(3,4)[:,3]
        objectMat = np.array(obs_list[6]).reshape(3,4)[:,0:3]
        objectVelocity = np.array(obs_list[7])

        # basePosition = np.array(obs_list[12]).reshape(3,4)[:,3]
        # baseVelocity = np.array(obs_list[13])
        if vRd is None:
            vRd = np.array([0, 0, 0]).T
        if vPd is None:
            vPd = np.array([0, 0, 0]).T
        if aRd is None:
            aRd = np.array([0, 0, 0]).T
        if aPd is None:
            aPd = np.array([0, 0, 0]).T
        ad = np.concatenate((aPd,aRd))
        vd = np.concatenate((vPd,vRd))
        q_cmd=[]
        mat_cmd = []
        position_cmd = []
        vi_cmd = []
        ai_cmd = []

        # 计算ye
        Re = np.array(obs_list[11]).reshape(3, 4)[:,0:3]
        Pe = np.array(obs_list[11]).reshape(3, 4)[:, 3]
        if Pd is None:
            Pd = Pe
        if Rd is None:
            Rd = Re
        R_d_e = np.dot(Rd.T, Re)
        Rpy_d_e = pin.rpy.matrixToRpy(R_d_e)
        # Rpy_d_e = np.dot(Rd.T, Rpy_d_e)

        # R_e_d = np.dot(Re.T, Rd)
        # Rpy_e_d = pin.rpy.matrixToRpy(R_e_d)
        # print(Rpy_d_e)
        # p_d_d_e = np.dot(Rd.T, Pe - Pd - basePosition)
        p_d_d_e = np.dot(Rd.T, Pe - Pd)
        ye = np.concatenate((p_d_d_e, Rpy_d_e))

        # 计算vye
        # objectTipMat = np.array(obs_list[0][6]).reshape(3, 4)
        tipVector = Pe - objectPosition
        tipVelocity = objectVelocity.copy()
        tipVelocity[0:3] = objectVelocity[0:3] + pin.skew(objectVelocity[3:6]).dot(tipVector)
        # tipVelocity = tipVelocity - baseVelocity
        # tipVelocity = tipVelocity
        # J_d_e = pin.rpy.computeRpyJacobian(Rpy_d_e, pin.WORLD)
        # TA = np.eye(6)
        # TA[3:, 3:] = J_d_e
        # inv_TA = np.linalg.inv(TA)

        Td = np.eye(6)
        Td[0:3, 0:3] = Rd
        Td[3:, 3:] = Rd
        # JA_d = np.dot(inv_TA, Td.T)
        # vye = np.dot(JA_d, tipVelocity)
        vye = Td.T.dot(tipVelocity - vd)
        # 计算aye（目标坐标系下）
        # aye = -np.linalg.inv(Md).dot(np.dot(Td.T, -Fe) - Kd.dot(vye) - Kp.dot(ye)) + Td.T.dot(ad) # Fe 需在世界坐标系中表示
        aye = np.linalg.inv(Md).dot(np.dot(Td.T, Fe) - Kd.dot(vye) - Kp.dot(ye)) + Td.T.dot(ad)
        # print(aye)
        # 计算aye（世界坐标系下）
        # w_d_d_e = np.dot(Rd.T, tipVelocity[3:] - vRd)
        # vR_d_e = np.dot(np.linalg.inv(J_d_e), w_d_d_e)
        # vJ_d_e = pin.rpy.computeRpyJacobianTimeDerivative(Rpy_d_e, vR_d_e, pin.WORLD)

        # vTA = np.eye(6)
        # vTA[3:, 3:] = vJ_d_e
        # vJA_d = np.dot(inv_TA, - np.dot(vTA, JA_d))
        # ay_t = -np.linalg.inv(JA_d).dot(aye + vJA_d.dot(tipVelocity))
        ay_t = Td.dot(aye)
        # 计算世界坐标系下的质心加速度
        ao_t = ay_t.copy()
        ao_t[0:3] = ay_t[0:3] - pin.skew(ay_t[3:6]).dot(tipVector) \
                    - pin.skew(tipVelocity[3:6]).dot(pin.skew(tipVelocity[3:6]).dot(tipVector))

        vo_t = objectVelocity + ao_t * self.dt

        Rpy_o = pin.rpy.matrixToRpy(objectMat)
        J_o = pin.rpy.computeRpyJacobian(Rpy_o, pin.WORLD)
        To = np.eye(6)
        To[3:, 3:] = J_o
        inv_To = np.linalg.inv(To)
        vo_rpy_t = inv_To.dot(vo_t)
        po_t =np.concatenate((objectPosition,Rpy_o)) + vo_rpy_t * self.dt
        mat_o = pin.rpy.rpyToMatrix(po_t[3:6])

        for i in range(self.robotNum):
            # robot = self.robotlist[i]
            # obs = obs_list[i]
            # q = obs[0]
            # vq = obs[1]
            # q = np.concatenate((robot.base_pose,q))
            # vq = np.concatenate(([0,0,0,0,0,0], vq))
            # 计算机械臂末端的加速度
            contactP_i = objectMat.dot(contactP_o[i])
            ai_t = ao_t.copy()
            ai_t[0:3] = ao_t[0:3] + pin.skew(ao_t[3:6]).dot(contactP_i) \
                        + pin.skew(objectVelocity[3:6]).dot(pin.skew(objectVelocity[3:6]).dot(contactP_i))
            ai_cmd.append(ai_t)

            # 计算机械臂末端的速度
            v_i = objectVelocity
            v_i[0:3] = objectVelocity[0:3] + pin.skew(objectVelocity[3:6]).dot(contactP_i)
            vi_t = vo_t.copy()
            vi_t[0:3] = vo_t[0:3] + pin.skew(vo_t[3:6]).dot(contactP_i)
            # vi_t = np.zeros(6)
            vi_cmd.append(vi_t)

            # 计算机械臂末端的位姿
            mat_i = objectMat.dot(contactMat_o[i])
            rpy_i = pin.rpy.matrixToRpy(mat_i)
            p_i = objectPosition + contactP_o[i]
            p_i = np.concatenate((p_i, rpy_i))

            mat_i_t = mat_o.dot(contactMat_o[i])
            rpy_i_t = pin.rpy.matrixToRpy(mat_i_t)
            pi_t = po_t[0:3] + contactP_o[i]
            pi_t = np.concatenate((pi_t,rpy_i_t))
            # qi_t = robot.controller.InverseKinematics(mat_i_t, pi_t)
            mat_cmd.append(mat_i_t)
            position_cmd.append(pi_t)

        return mat_cmd,position_cmd,vi_cmd,ai_cmd,ao_t
    def moveToPose(self, Pd, Rd, stepNums, extName = 'None'):####改成两个机械臂
        print("!11111111111111111111111111111111111111111111111111111111111111111111")
        objectAcc = np.zeros(6)
        obs_list = self.getObs()
        Ps = []  # 起始位置
        Rs = []  # 起始姿态


        # left (objectTipMat)
        left_tip = np.array(obs_list[11]).reshape(3, 4)
        Ps.append(left_tip[:, 3])
        Rs.append(left_tip[:, 0:3])

        # right (targetTipMat)
        print(obs_list[16])
        right_tip = np.array(obs_list[16]).reshape(3, 4)
        Ps.append(right_tip[:, 3])
        Rs.append(right_tip[:, 0:3])
        print(f"左臂起始位置: {Ps[0]}, 目标位置: {Pd[0]}")
        print(f"右臂起始位置: {Ps[1]}, 目标位置: {Pd[1]}")
        # if Rd is None:  # If the target pose is not provided, use the current pose.
        #     Rd = Rs

        objectVelocityOld = np.array(obs_list[7])
        init_Ps = Ps.copy()  # 固定的起始位置

        obs_list_record=[]
        base_obs_list_record = []
        forceInte_record = []
        distance_record = []
        targetP_record = []
        joint_force_record = []
        Fe_object_record = []
        for step in range(stepNums):
            self.client.step()
            objectAcc = np.zeros(6)
            # time1 = time.perf_counter()
            # simulationTime = self.client.getSimulationTime()
            obs_list = self.getObs()
            simulationTime = obs_list[14]   # obs[15]=simulationtime
            obs_list_record.append(obs_list)
            # contactP_o, contactMat_o = self.getGraspMat(obs_list) # 对物体质心的抓取
            print('=++++++++++++++++++++++++++++++++++DualspaceArmenv++++++++++++++++++++++++++++++++++++++++++++++++++++')
            print(f"当前仿真步: {step}, 仿真时间: {simulationTime}, 目标位置: {targetP}")
            # print("end position",Pd)
            # print("steps:",step)
            end_time = 30   # total moving time????

            # 左臂当前位姿
            left_tip = np.array(obs_list[11]).reshape(3, 4)
            Ps_left = left_tip[:, 3]
            Rs_left = left_tip[:, 0:3]

            # 右臂当前位姿
            right_tip = np.array(obs_list[16]).reshape(3, 4)
            Ps_right = right_tip[:, 3]
            Rs_right = right_tip[:, 0:3]

            current_Ps = [Ps_left, Ps_right]
            # current_Rs = [Rs_left, Rs_right]
            print("current_Ps: ", current_Ps)

            if simulationTime >= end_time:
                simulationTime = end_time - 0.001

            # 计算当前进度
            t_progress = simulationTime / end_time
            if t_progress > 1:
                t_progress = 1

            # targetP = []  # 目标位置列表
            # targetVel = []  # 目标速度列表（6维）
            # targetAcc = []  # 目标加速度列表（6维）
            # targetR = []  # 目标姿态列表
            targetP ,targetvP, targetaP = self.trajPlanner(init_Ps, Pd, simulationTime, end_time)
            # targetP_record.append(targetP)    # 这里有问题，导致一直只添加最后的东西
            start_right_x = init_Ps[1][0]  # 右臂起始 x 坐标
            # targetP[1][0] = 2 * start_right_x - targetP[1][0]  # 关于起始点对称

            # print("targetP",targetP)
            targetP_record.append(targetP.copy())
            # print("targetP_record",targetP_record)

            # Expand the 3-dimensional velocity to 6 dimensions.
            targetvP_6d = []
            targetaP_6d = []
            for arm_idx in range(2):
                vel_6d = np.concatenate([targetvP[arm_idx], np.zeros(3)])
                acc_6d = np.concatenate([targetaP[arm_idx], np.zeros(3)])
                targetvP_6d.append(vel_6d)
                targetaP_6d.append(acc_6d)

            currentTime = obs_list[14]
            print('currentTime:',currentTime)
            G_object = np.zeros((6,12))
            # Fe_object = None

            # 需要把这里修改为加速度恒定为0，给定一个位置让他直接过去
            # print(f"DEBUG - Input TargetP to Admittance: {targetP}")


            obs_list, baseObs, ForceInte, distanceListL, distanceListR, targetF = self.robot_Admittance(targetP,
                                                                                                        Rd,
                                                                                                        targetvP_6d,
                                                                                                        targetaP_6d,
                                                                                                        10,
                                                                                                        G_object,
                                                                                                        # Fe_object = Fe_object,
                                                                                                        obs=obs_list,
                                                                                                        executable=False,
                                                                                                        extName = extName,
                                                                                                        time=None)

            if step % 100 == 0:
                progress = simulationTime / end_time * 100
                print(f"进度: {progress:.1f}% (Step {step}/{stepNums})")
            base_obs_list_record.append(baseObs)
            forceInte_record.append(ForceInte)
            distance_record.append(distanceListL[0])
            joint_force_record.append(targetF)
            # self.client.step()
            # for j in range(self.robotNum):
            #     robot=self.robotlist[j]
            #     robot.moveRobotConfig(list(q_cmd[j][7:]))
            # self.client.step()
        # 获取目录路径
        save_dir = 'data/dualSpaceArm'
        # 如果目录不存在，则创建
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        obs_list_record = np.asarray(obs_list_record, dtype=object)
        base_obs_list_record = np.asarray(base_obs_list_record, dtype=object)
        np.save('data/dualSpaceArm/obs_list'+ extName +'.npy', obs_list_record)
        np.save('data/dualSpaceArm/base_obs_list'+ extName +'.npy', base_obs_list_record)
        np.save('data/dualSpaceArm/forceInte' + extName + '.npy', forceInte_record)
        np.save('data/dualSpaceArm/distance' + extName + '.npy', distance_record)
        np.save('data/dualSpaceArm/targetP' + extName + '.npy', targetP_record)
        np.save('data/dualSpaceArm/jointForce' + extName + '.npy', joint_force_record)
        np.save('data/dualSpaceArm/FeObject' + extName + '.npy', Fe_object_record)
        return obs_list

    # def robot_Admittance(self, targetPosition, targetMat, targetVel, targetAcc, stepNums, G_object, Fe_object=None,
    #                  obs=None, executable=True, extName='None', time=None):

    def robot_Admittance(self, targetPosition, targetMat, targetVel, targetAcc, stepNums, G_object,  obs = None, executable=True, extName = 'None',time = None):
        baseObs = self.getBaseObs()
        ForceInte = np.zeros(6)
        distanceListL = [0.0]
        distanceListR = [0.0]
        targetF = np.zeros(14)

        G_null = Matrix(G_object).nullspace()
        V = []
        for i in range(len(G_null)):
            V.append(np.array(G_null[i],dtype=float).reshape(1,12)[0])
        V=np.array(V,dtype=float).T
        # V = np.array(V)

        steps = 0
        obsinfo = None
        if not executable and obs is not None:
            # print("123456789123456789123456789123456789123456789")
            obsinfo = obs
        else:
            obsinfo = self.getObs()
        # CurrentForce = obsinfo[2]
        # for i in range(stepNums):
        # while steps < stepNums and np.linalg.norm(CurrentForce) < 4 * self.forceThreshold:
        print(stepNums)
        while steps < stepNums:
            steps = steps +1
            if not executable and obs is not None:
                obsinfo = obs
            else:
                obsinfo = self.getObs()

            # obs2 = self.getObs()
            baseObs = self.getBaseObs()
            # 确保 baseObs 格式为 [[x,y,z], [vx,vy,vz], [ax,ay,az,0,0,0]]
            baseObs = list(baseObs)
            baseObs[0] = np.array(baseObs[0]) + self.base_pose[0:3]
            # 如果加速度只有3维，补3个0作为角加速度
            if len(np.array(baseObs[2]).flatten()) == 3:
                baseObs[2] = np.concatenate([np.array(baseObs[2]).flatten(), np.zeros(3)])
            else:
                baseObs[2] = np.array(baseObs[2])

            # baseObs = None
            CurrentConfig = obsinfo[0]
            CurrentVelocity = obsinfo[1]
            CurrentForce = np.array(obsinfo[4]).reshape(-1,6)
            # CurrentForce = np.array([0,0,0,50,0,0])
            forceSensorMat = obsinfo[5]
            # print(f"Step {steps}, 原始力数据: {CurrentForce}")
            force = []
            for i in range(self.robotNum):
                forceSensorMat_i = np.array(forceSensorMat[i]).reshape((3, 4))[:, :3]
            # time1_1 = time.perf_counter()
            # print(time1_1 - time1)
                Tf_i = np.zeros((6, 6))
                Tf_i[:3, :3] = forceSensorMat_i
                Tf_i[3:, 3:] = forceSensorMat_i
                force.append(Tf_i.dot(CurrentForce[i]))
            Force = np.concatenate((force[0],force[1]))
            ForceI = V.dot(np.linalg.pinv(V)).dot(-Force)

            tempForce1 = G_object.dot(V[:, 0])
            tempForce2 = G_object.dot(V[:, 1])
            tempForce3 = G_object.dot(V[:, 2])

            ForceInte = np.linalg.pinv(V).dot(ForceI)
            # ForceInte = np.zeros(6)
            ForceI = -ForceI.reshape(-1,6)
            # forceIn = list(forceIn)
            # forceIn.append(Force)
            # forceIn=np.array(forceIn)
            # forceOut = []
            # if len(forceIn)>18:
            #     for n in range(6):
            #         forceOut.append(signal.filtfilt(self.signal_b, self.signal_a, forceIn[:,n])[-1])
            # else:
            #     forceOut = Force
            # print(Force)
            # Force = np.array([0, 0, 0, 20, 0, 0])
            # q_t, vq_t, aq_t = self.controller.AdmittanceController(CurrentConfig, CurrentVelocity,
            #                                                        targetPosition, targetMat, targetVel,
            #                                                        targetAcc, he=np.array(Force),baseObs = baseObs)
            # self.moveRobotConfig(list(q_t[7:]))
            # if executable:
            #     self.client.step()
            CurrentConfig[2] = - CurrentConfig[2]
            CurrentConfig[9] = - CurrentConfig[9]
            CurrentVelocity[2] = - CurrentVelocity[2]
            CurrentVelocity[9] = - CurrentVelocity[9]
            CurrentConfig = np.concatenate((self.base_pose, CurrentConfig))
            CurrentVelocity = np.concatenate(([0, 0, 0, 0, 0, 0], CurrentVelocity))
            baseObs[0] = np.array(baseObs[0]) +self.base_pose[0:3]

            # # 在调用 AdmittanceController 之前
            # targetP_swapped = [targetPosition[1], targetPosition[0]]
            # targetR_swapped = [targetMat[1], targetMat[0]]
            # # 然后用交换后的变量调用
            he = [force[0], force[1]]

            q, vq, aq, Fq, distanceListL,distanceListR= self.controller.AdmittanceController(CurrentConfig,
                                                                                             CurrentVelocity,
                                                                                             Pd=targetPosition,
                                                                                             Rd=targetMat,
                                                                                             vd=targetVel,
                                                                                             ad=targetAcc,
                                                                                             forceI=ForceI,
                                                                                             he = he,
                                                                                             baseObs=baseObs,
                                                                                             extName = extName,
                                                                                             time=time)

            # q, vq, aq, Fq, distanceListL, distanceListR = self.controller.BaselineController(CurrentConfig,
            #                                                                                    CurrentVelocity,
            #                                                                                    Pd=targetPosition,
            #                                                                                    Rd=targetMat,
            #                                                                                    vd=targetVel,
            #                                                                                    ad=targetAcc,
            #                                                                                    he=Fe_object,
            #                                                                                    baseObs=baseObs,
            #                                                                                    extName=extName,
            #                                                                                    time=time)
            # baseObs = self.getBaseObs()
            targetF = Fq.copy()
            targetF[2] = -targetF[2]
            targetF[9] = -targetF[9]
            # print('targetF:', targetF)
            self.setJointForce(targetF)
            self.client.step()
            # obsList = self.getObs()
            # conf = obsList[0]
            # vconf = obsList[1]
            # conf[2] = - conf[2]
            # conf[9] = - conf[9]
            # vconf[2] = - vconf[2]
            # vconf[9] = - vconf[9]
            # q = np.concatenate(([0, 0, 0.5, 0, 0, 0, 1], conf))
            # vq = np.concatenate(([0, 0, 0, 0, 0, 0], vconf))
            print("distaceLR",distanceListL, distanceListR)

        return obsinfo,baseObs,ForceInte,distanceListL,distanceListR,targetF

    def robot_ForceControl(self, targetPosition, targetMat, targetVel, targetAcc, stepNums, G_object, obs = None, executable=True, extName = 'None'):
        # forceIn=[]
        G_null = Matrix(G_object).nullspace()
        V = []
        for i in range(len(G_null)):
            V.append(np.array(G_null[i],dtype=float).reshape(1,12)[0])
        V=np.array(V,dtype=float).reshape(12,6)
        # V = np.array(V)

        steps = 0
        obsinfo = None
        if not executable and obs is not None:
            obsinfo = obs
        else:
            obsinfo = self.getObs()
        # CurrentForce = obsinfo[2]
        # for i in range(stepNums):
        # while steps < stepNums and np.linalg.norm(CurrentForce) < 4 * self.forceThreshold:
        while steps < stepNums:
            steps = steps +1
            if not executable and obs is not None:
                obsinfo = obs
            else:
                obsinfo = self.getObs()
            # obs2 = self.getObs()
            baseObs = self.getBaseObs()
            # baseObs = None
            CurrentConfig = obsinfo[0]
            CurrentVelocity = obsinfo[1]
            CurrentForce = np.array(obsinfo[4]).reshape(-1,6)
            # CurrentForce = np.array([0,0,0,50,0,0])
            forceSensorMat = obsinfo[5]
            force = []
            for i in range(self.robotNum):
                forceSensorMat_i = np.array(forceSensorMat[i]).reshape((3, 4))[:, :3]
            # time1_1 = time.perf_counter()
            # print(time1_1 - time1)
                Tf_i = np.zeros((6, 6))
                Tf_i[:3, :3] = forceSensorMat_i
                Tf_i[3:, 3:] = forceSensorMat_i
                force.append(Tf_i.dot(CurrentForce[i]))
            Force = np.concatenate((force[0],force[1]))
            Force = V.dot(np.linalg.pinv(V)).dot(Force)
            ForceInte = np.linalg.pinv(V).dot(Force)
            Force = Force.reshape(-1,6)
            # forceIn = list(forceIn)
            # forceIn.append(Force)
            # forceIn=np.array(forceIn)
            # forceOut = []
            # if len(forceIn)>18:
            #     for n in range(6):
            #         forceOut.append(signal.filtfilt(self.signal_b, self.signal_a, forceIn[:,n])[-1])
            # else:
            #     forceOut = Force
            # print(Force)
            # Force = np.array([0, 0, 0, 20, 0, 0])
            # q_t, vq_t, aq_t = self.controller.AdmittanceController(CurrentConfig, CurrentVelocity,
            #                                                        targetPosition, targetMat, targetVel,
            #                                                        targetAcc, he=np.array(Force),baseObs = baseObs)
            # self.moveRobotConfig(list(q_t[7:]))
            # if executable:
            #     self.client.step()
            CurrentConfig[2] = - CurrentConfig[2]
            CurrentConfig[9] = - CurrentConfig[9]
            CurrentVelocity[2] = - CurrentVelocity[2]
            CurrentVelocity[9] = - CurrentVelocity[9]
            CurrentConfig = np.concatenate((self.base_pose, CurrentConfig))
            CurrentVelocity = np.concatenate(([0, 0, 0, 0, 0, 0], CurrentVelocity))
            baseObs[0] = np.array(baseObs[0]) +self.base_pose[0:3]
            # q, vq, aq, Fq, distanceListL,distanceListR= self.controller.AdmittanceController(CurrentConfig, CurrentVelocity, Pd=targetPosition, Rd=targetMat,
            #                                                      vd=targetVel, ad=targetAcc, he=Force,
            #                                                      baseObs=baseObs, extName = extName)

            q, vq, aq, Fq, distanceListL, distanceListR = self.controller.BaselineController(CurrentConfig,
                                                                                               CurrentVelocity,
                                                                                               Pd=targetPosition,
                                                                                               Rd=targetMat,
                                                                                               vd=targetVel,
                                                                                               ad=targetAcc, he=Force,
                                                                                               baseObs=baseObs,
                                                                                               extName=extName)
            # baseObs = self.getBaseObs()
            targetF = Fq.copy()
            targetF[2] = -targetF[2]
            targetF[9] = -targetF[9]
            # print('targetF:', targetF)
            self.setJointForce(targetF)
            self.client.step()
            # obsList = self.getObs()
            # conf = obsList[0]
            # vconf = obsList[1]
            # conf[2] = - conf[2]
            # conf[9] = - conf[9]
            # vconf[2] = - vconf[2]
            # vconf[9] = - vconf[9]
            # q = np.concatenate(([0, 0, 0.5, 0, 0, 0, 1], conf))
            # vq = np.concatenate(([0, 0, 0, 0, 0, 0], vconf))
        return obsinfo,baseObs,ForceInte,distanceListL,distanceListR


# control robot by keyboard
def main():
    client = RemoteAPIClient()
    sim = client.getObject('sim')
    client.setStepping(True)
    sim.startSimulation()

    client.step()
    # time.sleep(0.001)
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

    # 尝试使用更保守的参数
    ControllerParams['Kp'] = np.eye(6) * 100
    # ControllerParams['Kp'] = np.eye(6) * 500
    ControllerParams['Kd']  = np.eye(6) * 200
    ControllerParams['Md'] = np.eye(6) * 100  # 增大虚拟质量，
    # ControllerParams['Kd'] = 2 * np.sqrt(ControllerParams['Kp'] * ControllerParams['Md'])



    pinocchio_model_path = "models"
    urdf_path = '\\mulit_arm_urdf\\urdf\\mulit_arm_urdf2.urdf'
    # end_frame = ["robot1_ee_link", "robot2_ee_link"]
    end_frame = ["object_tip", "target_tip"]
    base_pose = [0, 0, 0.5, 0, 0, 0, 1]
    robot = DualSpaceArmEnv(client,sim,base_pose,HandlesName,ControllerParams,pinocchio_model_path,urdf_path,end_frame=end_frame)
    # robot.testController()
    # Pd = np.array([0,-1.97708,0.51127])
    # Pd = np.array([0,-2.24792,0.47906])
    # Pd = np.array([0, -0.5, 2.534])
    # Pd = np.array([0, 0, 0.36726])
    # PS: [0.46314311 ,- 0.02030299 , 2.56789011]
    # 左臂起始位置: [0.08392596 - 0.05760898  2.4182609], 目标位置: [0. - 0.12030299  2.86789011]
    # 右臂起始位置: [-0.08391724 - 0.05760266  2.41825441], 目标位置: [-0.15813387 - 0.12029739  2.86788021]
    Pd_left = np.array([ 0.1392596, -0.05760898,2.5182609])  # 左臂目标
    Pd_right = np.array([-0.08391724, - 0.12029739,3.46788021])
    Pd = [ Pd_left,Pd_right]
    Rd = None
    extName = 'APF contact scene2-1 test'
    # robot.test_joint_axes()
    # mismatched = robot.verify_forward_kinematics()
    # if mismatched:
    #     robot.joint_sign = np.ones(14)
    #     for idx in mismatched:
    #         robot.joint_sign[idx] = -1.0
    # else:
    #     robot.joint_sign = np.ones(14)
    # print("关节符号数组:", robot.joint_sign)


    robot.moveToPose(Pd, Rd, 12000, extName = extName)


    # Ps = np.array([0.2,-0.4,2.83])
    # robot.trajPlanner(Ps, Pd, 2.5, 5)

    # goalConfig = [10*math.pi/180,-70*math.pi/180, 130*math.pi/180,-150*math.pi/180,-90*math.pi/180,0*math.pi/180]
    # goalConfig = [50*math.pi/180, 10*math.pi/180, 10*math.pi/180, 10*math.pi/180, 10*math.pi/180, 10*math.pi/180]
    # currentConfig = robot.moveRobotConfig(goalConfig)
    # robot.move_z(0.03)
    # robot.move_z_Admittance(-0.03,  10000)
    # robot.move_x_Admittance(0.05, 10000)
    # targetForce = np.array([0,0,-15,0,0,0])
    # robot.forceControl(targetForce, 10000)
    # robot.move_rz_Admittance(0.05,1000)
    # robot.move_z_Impedance(0.15,20000)
    # robot.move_ry_Admittance(0.1,3000)
    # robot.reset()
    # force = robot.forceControl(robot.targetForce, 10000, robot.forceThreshold)
    # robot.move_spiral_Admittance(3000)
    # finalPose = robot.getCurrentPose()
    # print('finalPose',finalPose)

    # goalpose = currentPose
    # goalpose[2]=goalpose[2]+0.15
    #
    # currentPose = robot.moveRobotPose(goalpose)
    # currentPose = robot.getCurrentPose()
    # goalpose = currentPose
    # goalpose[2] = goalpose[2] + 0.1
    # currentPose = robot.moveRobotPose(goalpose)

    # time.sleep(2)
    # robot.moveRobotPose()
    # while True:
    #     robot.moveRobotPose()
        # robot.rotateAllAngle([2, 1, 1, 1, 1, 1])
        # time.sleep(2)
        # robot.rotateCertainAnglePositive(1, 15)
        # time.sleep(2)

if __name__ == '__main__':
    main()
