import os
os.environ['SSL_CERT_FILE'] = ''

import pinocchio as pin
import numpy as np
import sys
import time
import math
# import rand
from os.path import dirname, join, abspath
# from pinocchio.visualize import MeshcatVisualizer

class DualSpaceArmController:
    def __init__(self,Kp,Kd,Md,dt, pinocchio_model_path, urdf_path,end_frame=None,end_joint=None):
        # pinocchio_model_dir = join(dirname(dirname(str(abspath(__file__)))), "pinocchio_test\\models\\ur_robot")
        print(str(abspath(__file__)))
        pinocchio_model_dir = join(dirname(dirname(str(abspath(__file__)))), pinocchio_model_path)
        mesh_dir = pinocchio_model_dir
        # urdf_model_path = pinocchio_model_dir + '\\ur_description\\urdf\\ur5_robot.urdf'
        urdf_model_path = pinocchio_model_dir + urdf_path

        self.model, self.collision_model, self.visual_model = pin.buildModelsFromUrdf(
            urdf_model_path, mesh_dir, pin.JointModelFreeFlyer())
        # self.model, self.collision_model, self.visual_model = pin.buildModelsFromUrdf(
        #     urdf_model_path, mesh_dir)

        if end_frame is not None and end_joint is not None:
            print('Can not set both end_frame and end_joint!')

        if end_frame is not None:
            self.frame_ide = [self.model.getFrameId(end_frame[i]) for i in range(len(end_frame))]
        else:
            self.frame_ide = None
        if end_joint is not None:
            self.joint_ide = [self.model.getJointId(end_joint[i]) for i in range(len(end_joint))]
        else:
            self.joint_ide = None
        # self.viz = MeshcatVisualizer(self.model, self.collision_model, self.visual_model)
        self.viz = None
        self.data = self.model.createData()
        self.armNum = 2
        self.Kp = Kp
        self.Kd = Kd
        self.Md = Md
        self.dt = dt

        self.model.gravity = pin.Motion.Zero()

        # self.viewerInit()
        print('Controller init')

    def viewerInit(self):
        try:
            self.viz.initViewer(open=True)
        except ImportError as err:
            print(
                "Error while initializing the viewer. It seems you should install Python meshcat"
            )
            print(err)
            sys.exit(0)

        # Load the robot in the viewer.
        self.viz.loadViewerModel()

        # Display a robot configuration.
        # q0 = pin.neutral(self.model)
        # q1 = np.array(
        #     [0.0, 0.0, 0.235, 0.0, 0.0, 0.0, 1.0, 0.8, -1.6, 0.8, -1.6, -0.8, 1.6]
        # )
        # q = np.array([0.0, 0.0, 0.2, 0.0, 0.0, 0.0, 1.0, 0, -1.22, 2.27, -2.62, -1.57, 0])
        q = np.concatenate(([0, 0, 0.5, 0, 0, 0, 1],
                            [0, 1.571, -0.5236, -1.0472, 0.5236, 0, 0],
                            [0, 1.571, -0.5236, -1.0472, 0.5236, 0, 0]))
        self.viz.display(q)
        # self.viz.displayCollisions(False)
        # self.viz.displayVisuals(True)
        # frame_ide = self.model.getFrameId("ee_link")
        # frame_idb = self.model.getFrameId("base_link")
        # self.viz.drawFrameVelocities(frame_id=frame_ide,v_scale=2)
        time.sleep(0.1)
        # self.viz.loadViewerModel(rootNodeName="pinocchio2")
        # frame_id = self.model.getFrameId("base_link")
        # self.viz.drawFrameVelocities(frame_id=frame_id)
    def InverseKinematics(self,targetRot, targetPosition, initConf=None):
        # JOINT_ID = 6 # The end effector corresponds to the 6th joint
        # oMdes = pin.SE3(np.eye(3), np.array([0., 1., 0.])) # desired pose
        # frame_id = self.model.getFrameId("ee_link")
        # JointId=7
        oMdes = pin.SE3(np.array(targetRot), np.array(targetPosition))
        if initConf is None:
            q = pin.neutral(self.model) # initial configuration
        else:
            q = initConf
        eps = 1e-3
        IT_MAX = 50000
        DT = 1e-1
        damp = 1e-10

        i = 0
        while True:
            pin.forwardKinematics(self.model, self.data, q)
            pin.updateFramePlacements(self.model, self.data)
            if self.frame_ide is not None:
                Mtool = self.data.oMf[self.frame_ide]
            if self.joint_ide is not None:
                Mtool = self.data.oMi[self.joint_ide]
            # print(Mtool)
            # err = pin.log(Mtool.inverse() * oMdes).vector
            dMi = oMdes.actInv(Mtool) # compute the error between the desired pose and the current one
            err = pin.log(dMi).vector
            if np.linalg.norm(err) < eps:
                success = True
                break
            if i >= IT_MAX:
                success = False
                break
            # J = pin.computeJointJacobian(self.model, self.data, q, JointId)
            if self.frame_ide is not None:
                J = pin.computeFrameJacobian(self.model, self.data, q, self.frame_ide)  # cann't set pin.WORLD
            if self.joint_ide is not None:
                J = pin.computeJointJacobian(self.model, self.data, q, self.joint_ide)
            v=np.zeros(self.model.nv)
            # When solving the inverse kinematics, fix the base and only allow the mechanical arm joints
            #  (starting from the 7th dimension) to compensate for the end-effector pose error.
            v[6:] = - J[:,6:].T.dot(np.linalg.solve(J[:,6:].dot(J[:,6:].T) + damp * np.eye(6), err))
            # v = - J.T.dot(np.linalg.solve(J.dot(J.T) + damp * np.eye(6), err))
            # v[6:] = np.linalg.pinv(J[:,6:]).dot(err)
            q = pin.integrate(self.model, q, v * DT)
            # if not i % 10:
            #     print('%d: error = %s' % (i, err.T))
            i += 1

        if success:
            print("Convergence achieved!")
        else:
            print("\nWarning: the iterative algorithm has not reached convergence to the desired precision")

        # print('\nresult: %s' % q.flatten().tolist())
        # print('\nfinal error: %s' % err.T)
        return q

    def DirectDynamics(self, tau, q, vq, he, J):
        # q = rand(self.model.nq)
        # vq = rand(self.model.nv)
        aq0 = np.zeros(self.model.nv)
        # compute dynamic drift -- Coriolis, centrifugal, gravity
        b = pin.rnea(self.model, self.data, q, vq, aq0)
        # compute mass matrix M
        M = pin.crba(self.model, self.data, q)
        aq=np.zeros(self.model.nv).T
        aq[6:] = np.dot(np.linalg.inv(M[6:,6:]),tau - np.dot(J.T,he) - b[6:])
        dt=0.01
        vq = vq + aq * dt
        q = pin.integrate(self.model, q, vq * dt)
        return q,vq,aq

    def getM(self,q):
        M = pin.crba(self.model, self.data, q)
        return M

    def getC(self,q,vq):
        aq0 = np.zeros(self.model.nv)   #20
        # compute dynamic drift -- Coriolis, centrifugal, gravity
        c = pin.rnea(self.model, self.data, q, vq, aq0)
        return c

    def step(self,q, vq, Pd=None, Rd=None, he=None, Controller='Impedance'):
        # frame_ide = self.model.getFrameId("ee_link")
        # frame_idb = self.model.getFrameId("base_link")
        for i in range(5000):
            if Controller=='Impedance':
                u,J = self.ImpedanceController(q, vq, Pd, Rd, he=he)
                q, vq, aq = self.DirectDynamics(u, q, vq,J[:,6:],he)
            elif Controller=='Admittance':


                # ------ 构造 baseObs 20260610------
                qb = q[:7]  # 基座：位置 + 四元数
                vqb = vq[:6]  # 基座速度
                aqb = np.zeros(6)  # 基座加速度（地面固定时为零）
                baseObs = [qb, vqb, aqb]

                forceI = [np.zeros(6), np.zeros(6)]
                q, vq, aq, Fq, distanceListL, distanceListR = self.AdmittanceController(q,vq,Pd=Pd,Rd=Rd,vd=None,ad=None,he=he,forceI=forceI,baseObs=baseObs)
                print("Fq",Fq)
                print("distanceListL",distanceListL)
                print("distanceListR",distanceListR)

            if i % 5==0:
                # print(i)
                # self.viz
                # .displayCollisions(False)
                # self.viz.displayVisuals(True)
                # # self.viz.drawFrameVelocities(frame_id=frame_ide, v_scale=2)
                # # self.viz.drawFrameVelocities(frame_id=frame_idb, v_scale=2)
                # self.viz.display(q)
                time.sleep(0.2)

    def getCollisionPoints(self, qbm, frameListL, frameListR, d0=0.3, k=0.1):
        PointsPositionListL = []
        PointsPositionListR = []
        PointsJacobiListL = []
        PointsJacobiListR = []
        ForceDirL = []
        ForceDirR = []
        ForceL = []
        ForceR = []
        distanceListL = []
        distanceListR = []
        aqL = []
        aqR = []

        for frame in frameListL:
            frame_id = self.model.getFrameId(frame)
            pose = self.data.oMf[frame_id]
            PointsPositionListL.append(pose.translation)
            J = pin.computeFrameJacobian(self.model, self.data, qbm, frame_id, pin.WORLD)
            PointsJacobiListL.append(J)
        for frame in frameListR:
            frame_id = self.model.getFrameId(frame)
            pose = self.data.oMf[frame_id]
            PointsPositionListR.append(pose.translation)
            J = pin.computeFrameJacobian(self.model, self.data, qbm, frame_id, pin.WORLD)
            PointsJacobiListR.append(J)
        for i in range(len(frameListL)):
            ForceDirLi=[]
            ForceLi = []
            distanceListi=[]
            for j in range(len(frameListR)):
                disVector = np.array(PointsPositionListL[i]) - np.array(PointsPositionListR[j])
                distance = np.linalg.norm(disVector)
                direction = disVector/distance
                ForceDirLi.append(direction)
                if distance < d0:
                    force = k*(1/distance - 1/d0)/(distance*distance)
                else:
                    force = 0
                ForceLi.append(force*direction)
                distanceListi.append(distance)
            ForceDirL.append(ForceDirLi)
            ForceL.append(ForceLi)
            distanceListL.append(distanceListi)
        for i in range(len(frameListR)):
            ForceDirRi=[]
            ForceRi = []
            distanceListi = []
            for j in range(len(frameListL)):
                disVector = np.array(PointsPositionListR[i]) - np.array(PointsPositionListL[j])
                distance = np.linalg.norm(disVector)
                direction = disVector/distance
                ForceDirRi.append(direction)
                if distance<d0:
                    force = k*(1/distance - 1/d0)/(distance*distance)
                else:
                    force = 0
                ForceRi.append(force * direction)
                distanceListi.append(distance)
            ForceDirR.append(ForceDirRi)
            ForceR.append(ForceRi)
            distanceListR.append(distanceListi)
        for i in range(len(frameListL)):
            # for j in range(len(ForceL[i])):
            forcei = np.sum(ForceL[i],axis=0)
            aqLi = np.array(PointsJacobiListL[i])[0:3,6:].T.dot(forcei)
            aqL.append(aqLi)
        for i in range(len(frameListR)):
            # for j in range(len(ForceL[i])):
            forcei = np.sum(ForceR[i],axis=0)
            aqRi = np.array(PointsJacobiListR[i])[0:3,6:].T.dot(forcei)
            aqR.append(aqRi)
        aqLsum = np.sum(aqL, axis=0)
        aqRsum = np.sum(aqR, axis=0)
        aqApf = aqLsum + aqRsum
        return ForceL,ForceR,distanceListL,distanceListR,aqApf


    def AdmittanceController(self,q,vq,Pd=None,Rd=None,vd=None,ad=None, forceI=None, he = None, baseObs=None, extName = 'None',time=None):
        # q, vq, aq = self.AdmittanceController(q, vq, Pd=Pd, Rd=Rd, vd=None, ad=None, he=he, forceI=forceI,
        #                                       baseObs=baseObs)
        qb = np.array(baseObs[0])   # 7维
        vqb = np.array(baseObs[1])  # 6维
        aqb = np.array(baseObs[2])  # 6维
        qbm = q  # 21维
        # vqbm = np.concatenate((vqb, vq[3:]))    # 20维
        vqbm =vq

        if vd is None:
            vd = [np.zeros(6) for i in range(self.armNum)]
            vpd = [np.zeros(3) for i in range(self.armNum)]
            wd = [np.zeros(3) for i in range(self.armNum)]
        else:
            vpd = [vd[i][0:3] for i in range(self.armNum)]
            wd = [vd[i][3:6] for i in range(self.armNum)]
        if ad is None:
            ad = [np.zeros(6) for i in range(self.armNum)]

        # frame_id = self.model.getFrameId("ee_link")
        # pin.framesForwardKinematics(self.model, self.data, q)
        # pin.updateFramePlacements(self.model, self.data)
        # Mtool = self.data.oMf[frame_id]
        # # print(Mtool)
        # print("vd",vd)


        pin.forwardKinematics(self.model, self.data, qbm)
        pin.updateFramePlacements(self.model, self.data)
        if self.frame_ide is not None:
            Mtool = [self.data.oMf[self.frame_ide[i]] for i in range(self.armNum)]
        if self.joint_ide is not None:
            Mtool = [self.data.oMi[self.joint_ide[i]] for i in range(self.armNum)]
        if Pd is None:
            Pd = [Mtool[i].translation for i in range(self.armNum)]
        else:
            Pd = [Pd[i][0:3] for i in range(self.armNum)]
        if Rd is None:
            Rd = [Mtool[i].rotation for i in range(self.armNum)]
        # print('Pd',Pd)

        Re = [Mtool[i].rotation for i in range(self.armNum)]# 当前姿态（3x3旋转矩阵）
        # print(Re)
        R_d_e = [np.dot(Rd[i].T, Re[i]) for i in range(self.armNum)]
        # print("rde",R_d_e)
        Rpy_d_e = [pin.rpy.matrixToRpy(R_d_e[i]) for i in range(self.armNum)]
        # print("Rpy",Rpy_d_e)
        err_rot = [pin.log3(R_d_e[i]) for i in range(self.armNum)]

        # Rpy_d_e = [np.dot(Rd[i].T, Rpy_d_e[i]) for i in range(self.armNum)]
        # J_d_e = [pin.rpy.computeRpyJacobian(Rpy_d_e[i], pin.WORLD) for i in range(self.armNum)]
        # TA = [np.eye(6) for i in range(self.armNum)]
        # for i in range(self.armNum):
        #     TA[i][3:, 3:] = J_d_e[i]
        # inv_TA = [np.linalg.inv(TA[i]) for i in range(self.armNum)]
        if self.frame_ide is not None:
            J = [pin.computeFrameJacobian(self.model, self.data, qbm, self.frame_ide[i], pin.WORLD) for i in range(self.armNum)]
        if self.joint_ide is not None:
            J = [pin.computeJointJacobian(self.model, self.data, qbm, self.joint_ide[i]) for i in range(self.armNum)]
        # J = pin.computeFrameJacobian(self.model, self.data, q, frame_id, pin.WORLD)
        Td = [np.eye(6) for i in range(self.armNum)]
        for i in range(self.armNum):
            Td[i][0:3, 0:3] = Rd[i]
            Td[i][3:, 3:] = Rd[i]
        # JA_d = [np.dot(np.dot(inv_TA[i], Td[i].T), J[i][:,6:]) for i in range(self.armNum)]

        # ve = [np.dot(J[i], vqbm) for i in range(self.armNum)]
        # print("J",J)
        ve = [np.dot(J[i], vq) for i in range(self.armNum)]
        # print("ve,vd",ve,vd)
        # print("ve[i],vd[i]:",ve[i],vd[i])
        vxe = [Td[i].T.dot(ve[i]-vd[i]) for i in range(self.armNum)]

        # vd = np.zeros(12)
        # ve = [np.dot(J[i], vq) for i in range(self.armNum)]
        # vxe = [Td[i].T.dot(ve[i] - vd[i]) for i in range(self.armNum)]
        # v_d_d_e = [np.dot(Rd[i].T, ve[i][0:3] - vpd[i]) for i in range(self.armNum)]
        # w_d_d_e = [np.dot(Rd[i].T, ve[i][3:] - wd[i]) for i in range(self.armNum)]
        # vR_d_e = [np.dot(np.linalg.inv(J_d_e[i]), w_d_d_e[i]) for i in range(self.armNum)]
        # vJ_d_e = [pin.rpy.computeRpyJacobianTimeDerivative(Rpy_d_e[i], vR_d_e[i], pin.WORLD) for i in range(self.armNum)]

        # if self.frame_ide is not None:
        #     vJ = [pin.frameJacobianTimeVariation(self.model, self.data, q, vq, self.frame_ide[i], pin.WORLD) for i in range(self.armNum)]
        # if self.joint_ide is not None:
        #     vJ = [pin.computeJointJacobiansTimeVariation(self.model, self.data, q, vq) for i in range(self.armNum)]

        # vTA = [np.eye(6) for i in range(self.armNum)]
        # for i in range(self.armNum):
        #     vTA[i][3:, 3:] = vJ_d_e[i]

        # vJA_d = [np.dot(inv_TA[i], np.dot(Td[i].T, vJ[i]) - np.dot(vTA[i], JA_d[i])) for i in range(self.armNum)]
        Pe = [Mtool[i].translation for i in range(self.armNum)]

        # print("传参check:Pd" ,Pd)
        # # Pd = [np.array([1.45814311, -0.02030299, 2.56789011]),
        # #       np.array([0.45813387, -0.02029739, 2.56788021])]
        # print(f"CHECK - Pe_Left: {Pe[0]}")
        # print(f"CHECK - Pd_Left: {Pd[0]}")
        # print(f"CHECK - Pe_Right: {Pe[1]}")
        # print(f"CHECK - Pd_Right: {Pd[1]}")

        p_d_d_e = [np.dot(Rd[i].T, Pe[i] - Pd[i]) for i in range(self.armNum)]

        xe = [np.concatenate((p_d_d_e[i], Rpy_d_e[i])) for i in range(self.armNum)]
        # xe = [np.concatenate((p_d_d_e[i], err_rot[i])) for i in range(self.armNum)]

        # vxe = [np.dot(JA_d[i], vqbm[6:]) for i in range(self.armNum)]

        # print('he:', he)
        # print('xe:', Td[0].dot(xe[0]))
        # print('vxe:', Td[0].dot(vxe[0]))
        # axe = [-np.linalg.inv(self.Md).dot(np.dot(Td[i].T, -forceI[i]) - self.Kd.dot(vxe[i]) - self.Kp.dot(xe[i])) + Td[i].T.dot(ad[i]) for i in range(self.armNum)] # he 需在世界坐标系中表示


        # print("xe:",xe)
        # print("vxe:",vxe)
        # print("forceI",forceI)
        error_L = Pd[0] - Pe[0]
        error_R = Pd[1] - Pe[1]
        # print(f"DEBUG - Left Error Vector: {error_L}")
        # print(f"DEBUG - Right Error Vector: {error_R}")
        # forceI = 0 * forceI
        axe = [np.linalg.inv(self.Md).dot(np.dot(Td[i].T, forceI[i]) - self.Kd.dot(vxe[i]) - self.Kp.dot(xe[i])) + Td[i].T.dot(ad[i]) for i in range(self.armNum)] # he 需在世界坐标系中表示

        # axe = [(-1.0 * v_vel) + (-0.2 * v_pos) for v_vel, v_pos in zip(vxe, xe)]
        # axe = [-1* v for v in vxe]
        # print("axe",axe)
        # # axe = np.linalg.inv(self.Md).dot(np.dot(Td.T, he)-self.Kd.dot(vxe)-self.Kp.dot(xe)) # he 需在世界坐标系中表示

        # ve_t = [ve[i] + axe[i] * self.dt for i in range(self.armNum)]

        # be1 = [Rd[i].T.dot(vpd[i]) + pin.skew(Rd[i].T.dot(wd[i])).dot(p_d_d_e[i]) for i in range(self.armNum)]
        # be2 = [np.linalg.inv(J_d_e[i]).dot(Rd[i].T.dot(wd[i])) for i in range(self.armNum)]
        # be = [np.concatenate((be1[i],be2[i])) for i in range(self.armNum)]
        # if baseObs is not None:
        #     baseA = np.array(baseObs[0])
        #     baseA = np.concatenate((baseA, [0, 0, 0]))
        #     baseV = np.array(baseObs[1])
        #     baseV = np.concatenate((baseV, [0, 0, 0]))
        #
        #     aq_t = np.linalg.inv(J[:, 6:]).dot(Td.dot(axe - baseA)-vJ.dot(vq))
        #     aq_t = np.concatenate(([0, 0, 0, 0, 0, 0], aq_t))
        #     vq_t = vq + aq_t * self.dt
        #     print(baseV)
        # else:


        # J_pseudo_inv = [J[i][:,6:].T.dot(np.linalg.inv(J[i][:,6:].dot(J[i][:,6:].T))) for i in range(self.armNum)]
        # aq_t = [J_pseudo_inv[i].dot(Td[i].dot(axe[i]) - vJ[i][:,6:].dot(vq[6:])) for i in range(self.armNum)]
        # aq_t = np.sum(aq_t,axis=0)

        axe_w = [Td[i].dot(axe[i]) for i in range(self.armNum)]

        # if 'None' in extName:    # the base is fixed, the subsequent "elif" condition is not considered
        aq_t, Fq, distanceListL,distanceListR = self.getAqt2(qbm, vqbm, axe_w, aqb, Bedp = False, Db=0, Apf = False, time=time)
        # elif 'APF' in extName and 'BEDP' not in extName:
        #     aq_t, Fq, distanceListL,distanceListR = self.getAqt2(qbm, vqbm, axe_w, aqb, Bedp = False, Db=0, Apf = True, time=time)
        # elif 'BEDP-APF (Cb=0)' in extName:
        #     aq_t, Fq, distanceListL,distanceListR = self.getAqt2(qbm, vqbm, axe_w, aqb, Bedp = True, Db=0, Apf = True, time=time)
        # elif 'BEDP-APF (Cb=10)' in extName:
        #     aq_t, Fq, distanceListL,distanceListR = self.getAqt2(qbm, vqbm, axe_w, aqb, he=he, Bedp = True, Db=10, Apf = True, time=time)
        # elif extName == 'BEDP-APF (Cb=0) dis':
        #     aq_t, Fq, distanceListL,distanceListR = self.getAqt2(qbm, vqbm, axe_w, aqb, Bedp = True, Db=0, Apf = True, time=time)
        # elif 'BEDP-APF (Cb=100)' in extName:
        #     aq_t, Fq, distanceListL,distanceListR = self.getAqt2(qbm, vqbm, axe_w, aqb, he=he, Bedp = True, Db=100, Apf = True, time=time)
        # elif 'BEDP-APF (Cb=50)' in extName:
        #     aq_t, Fq, distanceListL, distanceListR = self.getAqt2(qbm, vqbm, axe_w, aqb, he=he, Bedp=True, Db=50,
        #                                                           Apf=True, time=time)
        # elif 'BEDP-APF (Cb=30)' in extName:
        #     aq_t, Fq, distanceListL, distanceListR = self.getAqt2(qbm, vqbm, axe_w, aqb, he=he, Bedp=True, Db=30,
        #                                                           Apf=True, time=time)
        # elif 'BEDP (Cb=30)' in extName:
        #     aq_t, Fq, distanceListL, distanceListR = self.getAqt2(qbm, vqbm, axe_w, aqb, he=he, Bedp=True, Db=30,
        #                                                           Apf=False, time=time)
        # elif 'BEDP (Cb=50)' in extName:
        #     aq_t, Fq, distanceListL, distanceListR = self.getAqt2(qbm, vqbm, axe_w, aqb, he=he, Bedp=True, Db=50,
        #                                                           Apf=False, time=time)
        #
        # elif extName == 'BEDP (Cb=0)':
        #     aq_t, Fq, distanceListL,distanceListR = self.getAqt2(qbm, vqbm, axe_w, aqb, Bedp = True, Db=0, Apf = False, time=time)
        # elif extName == 'BEDP (Cb=0) dis':
        #     aq_t, Fq, distanceListL,distanceListR = self.getAqt2(qbm, vqbm, axe_w, aqb, Bedp = True, Db=0, Apf = False, time=time)
        # elif extName == 'BEDP (Cb=10)':
        #     aq_t, Fq, distanceListL,distanceListR = self.getAqt2(qbm, vqbm, axe_w, aqb, Bedp = True, Db=10, Apf = False, time=time)
        # elif extName == 'BEDP (Cb=100)':
        #     aq_t, Fq, distanceListL,distanceListR = self.getAqt2(qbm, vqbm, axe_w, aqb, Bedp = True, Db=100, Apf = False, time=time)

        aq_t = np.concatenate((np.zeros(6), aq_t))
        vq_t = vqbm + aq_t * self.dt
        q_t = pin.integrate(self.model, qbm, vq_t * self.dt)
        # print('Pe', Pe)
        # print('Re', Re)
        # print(q_t)

        # aq_t = -np.linalg.inv(JA_d[:,6:]).dot(axe + vJA_d.dot(vq))
        # vq_t = vq[6:] + aq_t * self.dt
        # vq_t = np.concatenate(([0, 0, 0, 0, 0, 0], vq_t))
        # q_t = pin.integrate(self.model, q,  vq_t * self.dt)

        # vxe_t = vxe + axe * dt
        # pe_t = xe[0:3] + vxe_t[0:3] * dt
        # d_theta = np.linalg.norm(vxe_t[3:]) * dt
        # r = np.array([vxe_t[3:]/np.linalg.norm(vxe_t[3:])])
        # Rot_theta_1 = r.T.dot(r)
        # Rot_theta_2 = 1 - math.cos(d_theta)
        # Rot_theta_3 = np.array([[math.cos(d_theta),-r[0][2]*math.sin(d_theta), r[0][1]*math.sin(d_theta)],
        #                       [r[0][2]*math.sin(d_theta), math.cos(d_theta), -r[0][0]*math.sin(d_theta)],
        #                       [-r[0][1]*math.sin(d_theta), r[0][0]*math.sin(d_theta),math.cos(d_theta)]])
        # Rot_theta = Rot_theta_1 *Rot_theta_2 + Rot_theta_3
        # R_d_e_t = Rot_theta.dot(R_d_e)
        # targetRot = Rd.dot(R_d_e_t)
        # targetPosition = Pd + Rd.dot(pe_t)
        # q_t = self.InverseKinematics(targetRot, targetPosition, initConf=q)
        # vq_t = -np.linalg.inv(JA_d[:,6:]).dot(vxe_t)
        # q_t = np.concatenate(([0, 0, 0, 0, 0, 0, 1], q_t))
        # vq_t = np.concatenate(([0, 0, 0, 0, 0, 0], vq_t))
        return q_t, vq_t, aq_t, Fq, distanceListL, distanceListR

    def BaselineController(self,q,vq,Pd=None,Rd=None,vd=None,ad=None,he=None,baseObs=None, extName = 'None', time=None):
        # Md = np.eye(6) * 500
        Kd = np.eye(6) * 3
        print("baselincontroller")
        Kp = np.eye(6) * 3

        # Kp = np.array([[100, 0, 0, 0, 0, 0],
        #                [0, 100, 0, 0, 0, 0],
        #                [0, 0, 100, 0, 0, 0],
        #                [0, 0, 0, 100, 0, 0],
        #                [0, 0, 0, 0, 100, 0],
        #                [0, 0, 0, 0, 0, 100]])
        #
        # Kd = np.array([[100, 0, 0, 0, 0, 0],
        #                [0, 100, 0, 0, 0, 0],
        #                [0, 0, 100, 0, 0, 0],
        #                [0, 0, 0, 100, 0, 0],
        #                [0, 0, 0, 0, 100, 0],
        #                [0, 0, 0, 0, 0, 100]])
        # Kd = Kp*2
        # Md=Kp
        # dt = 0.05

        # vRd = np.array([0, 0, 0]).T  # 必须为0
        # vPd = np.array([0, 0, 0]).T  # 必须为0
        qb = np.array(baseObs[0])
        vqb = np.array(baseObs[1])
        aqb = np.array(baseObs[2])
        qbm = np.concatenate((qb, q[3:]))
        vqbm = np.concatenate((vqb, vq[3:]))

        if vd is None:
            vd = [np.zeros(6) for i in range(self.armNum)]
            print("11vd:",vd)
            vpd = [np.zeros(3) for i in range(self.armNum)]
            wd = [np.zeros(3) for i in range(self.armNum)]
        else:
            vpd = [vd[i][0:3] for i in range(self.armNum)]
            wd = [vd[i][3:6] for i in range(self.armNum)]
        if ad is None:
            ad = [np.zeros(6) for i in range(self.armNum)]

        pin.forwardKinematics(self.model, self.data, qbm)
        pin.updateFramePlacements(self.model, self.data)
        if self.frame_ide is not None:
            Mtool = [self.data.oMf[self.frame_ide[i]] for i in range(self.armNum)]
        if self.joint_ide is not None:
            Mtool = [self.data.oMi[self.joint_ide[i]] for i in range(self.armNum)]
        if Pd is None:
            Pd = [Mtool[i].translation for i in range(self.armNum)]
        else:
            Pd = [Pd[i][0:3] for i in range(self.armNum)]
        if Rd is None:
            Rd = [Mtool[i].rotation for i in range(self.armNum)]

        Re = [Mtool[i].rotation for i in range(self.armNum)]
        R_e_d = [np.dot(Re[i].T, Rd[i]) for i in range(self.armNum)]
        Rpy_e_d = [pin.rpy.matrixToRpy(R_e_d[i]) for i in range(self.armNum)]

        if self.frame_ide is not None:
            J = [pin.computeFrameJacobian(self.model, self.data, qbm, self.frame_ide[i], pin.WORLD) for i in range(self.armNum)]
        if self.joint_ide is not None:
            J = [pin.computeJointJacobian(self.model, self.data, qbm, self.joint_ide[i]) for i in range(self.armNum)]
        # J = pin.computeFrameJacobian(self.model, self.data, q, frame_id, pin.WORLD)
        Td = [np.eye(6) for i in range(self.armNum)]
        for i in range(self.armNum):
            Td[i][0:3, 0:3] = Rd[i]
            Td[i][3:, 3:] = Rd[i]

        ve = [np.dot(J[i], vq) for i in range(self.armNum)]
        vxe = [vd[i]-ve[i] for i in range(self.armNum)]

        # vJA_d = [np.dot(inv_TA[i], np.dot(Td[i].T, vJ[i]) - np.dot(vTA[i], JA_d[i])) for i in range(self.armNum)]
        Pe = [Mtool[i].translation for i in range(self.armNum)]
        p_e_d = [Pd[i] - Pe[i] for i in range(self.armNum)]

        xe = [np.concatenate((p_e_d[i], Rpy_e_d[i])) for i in range(self.armNum)]

        # axe = [np.linalg.inv(self.Md).dot(np.dot(Td[i].T, he[i]) - self.Kd.dot(vxe[i]) - self.Kp.dot(xe[i])) + Td[i].T.dot(ad[i]) for i in range(self.armNum)] # he 需在世界坐标系中表示
        axe_w = [ad[i] + Kd.dot(vxe[i]) + Kp.dot(xe[i]) for i in range(self.armNum)] # PD controller
        # axe = ad
        # axe_w = [Td[i].dot(axe[i]) for i in range(self.armNum)]

        if 'None' in extName:
            aq_t, Fq, distanceListL,distanceListR = self.getAqt2(qbm, vqbm, axe_w, aqb, Bedp = False, Db=0, Apf = False)
        # elif 'APF' in extName and 'BEDP' not in extName:
        #     aq_t, Fq, distanceListL,distanceListR = self.getAqt2(qbm, vqbm, axe_w, aqb, Bedp = False, Db=0, Apf = True)
        # elif 'BEDP-APF (Cb=0)' in extName:
        #     aq_t, Fq, distanceListL,distanceListR = self.getAqt2(qbm, vqbm, axe_w, aqb, Bedp = True, Db=0, Apf = True)
        # elif 'BEDP-APF (Cb=10)' in extName:
        #     aq_t, Fq, distanceListL,distanceListR = self.getAqt2(qbm, vqbm, axe_w, aqb, Bedp = True, Db=10, Apf = True)
        # elif extName == 'BEDP-APF (Cb=0) dis':
        #     aq_t, Fq, distanceListL,distanceListR = self.getAqt2(qbm, vqbm, axe_w, aqb, Bedp = True, Db=0, Apf = True)
        # elif 'BEDP-APF (Cb=100)' in extName:
        #     aq_t, Fq, distanceListL,distanceListR = self.getAqt2(qbm, vqbm, axe_w, aqb, Bedp = True, Db=100, Apf = True)
        # elif 'BEDP-APF (Cb=50)' in extName:
        #     aq_t, Fq, distanceListL, distanceListR = self.getAqt2(qbm, vqbm, axe_w, aqb, he=he, Bedp=True, Db=50,
        #                                                           Apf=True, time=time)
        # elif 'BEDP-APF (Cb=30)' in extName:
        #     aq_t, Fq, distanceListL, distanceListR = self.getAqt2(qbm, vqbm, axe_w, aqb, he=he, Bedp=True, Db=30,
        #                                                           Apf=True, time=time)
        # elif extName == 'BEDP (Cb=0)':
        #     aq_t, Fq, distanceListL,distanceListR = self.getAqt2(qbm, vqbm, axe_w, aqb, Bedp = True, Db=0, Apf = False)
        # elif extName == 'BEDP (Cb=0) dis':
        #     aq_t, Fq, distanceListL,distanceListR = self.getAqt2(qbm, vqbm, axe_w, aqb, Bedp = True, Db=0, Apf = False)
        # elif extName == 'BEDP (Cb=10)':
        #     aq_t, Fq, distanceListL,distanceListR = self.getAqt2(qbm, vqbm, axe_w, aqb, Bedp = True, Db=10, Apf = False)
        # elif extName == 'BEDP (Cb=100)':
        #     aq_t, Fq, distanceListL,distanceListR = self.getAqt2(qbm, vqbm, axe_w, aqb, Bedp = True, Db=100, Apf = False)

        aq_t = np.concatenate((np.zeros(6), aq_t))
        vq_t = vqbm + aq_t * self.dt
        q_t = pin.integrate(self.model, qbm, vq_t * self.dt)

        return q_t, vq_t, aq_t, Fq, distanceListL, distanceListR

    def getAqt(self,q,vq,axe,aqb):
        Kp = np.array([[2000, 0, 0], [0, 1500, 0], [0, 0, 500]])
        Kd = 0.5 * np.eye(3)
        axe = np.concatenate((axe[0],axe[1]))
        aqb = np.concatenate((aqb,[0,0,0]))
        H = self.getM(q)
        C = self.getC(q,vq)
        Hbm = H[0:6,6:]
        Cb = C[0:6]
        Cb[0:3] = Cb[0:3] - Kp.dot(q[0:3]) - Kd.dot(vq[0:3])
        J = [pin.computeFrameJacobian(self.model, self.data, q, self.frame_ide[i], pin.WORLD) for i in
             range(self.armNum)]
        Jbm = np.concatenate((J[0],J[1]),axis=0)
        Jm = np.concatenate((J[0][:,6:],J[1][:,6:]),axis=0)
        Jb = np.concatenate((J[0][:,0:6],J[1][:,0:6]),axis=0)
        vJ = [pin.frameJacobianTimeVariation(self.model, self.data, q, vq, self.frame_ide[i], pin.WORLD) for i in
              range(self.armNum)]
        vJbm = np.concatenate((vJ[0], vJ[1]), axis=0)
        Hbmw = np.linalg.inv(Hbm.T.dot(Hbm))
        Jw = Hbmw.dot(Jm.T).dot(np.linalg.inv(Jm.dot(Hbmw).dot(Jm.T)))
        aq1 = Jw.dot(axe-vJbm.dot(vq)-Jb.dot(aqb))
        aq2 = (np.eye(14)-Jw.dot(Jm)).dot(np.linalg.pinv(Hbm)).dot(Cb)/5
        # aq2 = (np.eye(14) - Jw.dot(Jm)).dot(Hbmw).dot(Cb) / 5
        # aq2 = (np.eye(14) - Jw.dot(Jm)).dot(Hbm.T).dot(Cb) / 5
        aq = aq1 + aq2
        Hm = H[6:, 6:]
        Fq = Hm.dot(aq) + Hbm.T.dot(aqb) + C[6:]
        return aq, Fq

    def getAqt2(self,q,vq,axe,aqb,he = None, Bedp = True, Db=0, Apf = True, time=None):
        # Kp = np.array([[1000,0,0],[0,1000,0],[0,0,200]])
        # Kd = 0.005 * np.eye(3)
        axe = np.concatenate((axe[0],axe[1]))
        # aqb = np.concatenate((aqb,[0,0,0]))

        H = self.getM(q)    # 20*20
        C = self.getC(q,vq) #20
        Hbm = H[0:6,6:] #6,14
        Cb = C[0:6]
        # Cb[0:3] = Cb[0:3] - Kp.dot(q[0:3]) - Kd.dot(vq[0:3])
        J = [pin.computeFrameJacobian(self.model, self.data, q, self.frame_ide[i], pin.WORLD) for i in
             range(self.armNum)]
        Jbm = np.concatenate((J[0],J[1]),axis=0)    #12,20
        Jm = np.concatenate((J[0][:,6:],J[1][:,6:]),axis=0) # 后14列
        Jb = np.concatenate((J[0][:,0:6],J[1][:,0:6]),axis=0)   # base
        vJ = [pin.frameJacobianTimeVariation(self.model, self.data, q, vq, self.frame_ide[i], pin.WORLD) for i in
              range(self.armNum)]
        vJbm = np.concatenate((vJ[0], vJ[1]), axis=0)
        vJm = vJbm[:,6:]
        # Hbmw = np.linalg.inv(Hbm.T.dot(Hbm))
        # Jw = Hbmw.dot(Jm.T).dot(np.linalg.inv(Jm.dot(Hbmw).dot(Jm.T)))
        S = np.eye(14)-np.linalg.pinv(Jm).dot(Jm)   #14*14
        aq1 = np.linalg.pinv(Jm).dot(axe-vJbm.dot(vq)-Jb.dot(aqb))
        aq2 = S.dot(np.linalg.pinv(Hbm.dot(S)))
        # aq2 = np.linalg.pinv(Hbm.dot(S))

        if Bedp:
            vqb = vq[0:6]
            if time is None:
                if he is None:
                    he = np.zeros(6)
                else:
                    he = he.reshape(-1,6)
                    he = np.sum(he,axis=0)
                aq3 = aq2.dot(-he + Db * vqb-Hbm.dot(aq1) - Cb)/1.2
                # aq3Max = np.max(abs(aq3))
                # if aq3Max>1:
                #     aq3 = aq3/(aq3Max/1)

                print('aq3:',aq3)
            else:
                if time>15:
                    scale = 1.2 + time * 0.5
                else:
                    scale = 1.2
                aq3 = aq2.dot(Db * vqb - Hbm.dot(aq1) - Cb) / scale
        else:
            aq3 = np.zeros(14)
            # print('aq3:',aq3)
        if Apf:
            frameListL = ['robot1_link4']
            frameListR = ['robot2_link4']
            ForceL,ForceR,distanceListL,distanceListR, aqApf = self.getCollisionPoints(q, frameListL, frameListR, d0=3, k=4)
            aq4 = S.dot(aqApf)
        else:
            frameListL = ['robot1_link4']
            frameListR = ['robot2_link4']
            ForceL, ForceR, distanceListL, distanceListR, aqApf = self.getCollisionPoints(q, frameListL, frameListR,
                                                                                          d0=3, k=0.04)
            aq4 = np.zeros(14)
        # aq3=0
        # aq4=0
        # print('aq4:', aq4)
        aq1 = np.linalg.pinv(Jm).dot(axe)
        aq = aq1 + aq3 + aq4

        # aqout = np.zeros(14)
        # np.clip(aq,-20,20,aqout)

        aqout = aq

        Hm = H[6:, 6:]
        Fq = Hm.dot(aqout) + Hbm.T.dot(aqb) + C[6:]
        return aq, Fq, distanceListL, distanceListR

    def getAqtApf(self,q,vq,axe,aqb):
        axe = np.concatenate((axe[0],axe[1]))
        aqb = np.concatenate((aqb,[0,0,0]))
        H = self.getM(q)
        C = self.getC(q,vq)
        Hbm = H[0:6,6:]
        Cb = C[0:6]
        # Cb[0:3] = Cb[0:3] - Kp.dot(q[0:3]) - Kd.dot(vq[0:3])
        J = [pin.computeFrameJacobian(self.model, self.data, q, self.frame_ide[i], pin.WORLD) for i in
             range(self.armNum)]
        # Jbm = np.concatenate((J[0],J[1]),axis=0)
        Jm = np.concatenate((J[0][:,6:],J[1][:,6:]),axis=0)
        Jb = np.concatenate((J[0][:,0:6],J[1][:,0:6]),axis=0)
        vJ = [pin.frameJacobianTimeVariation(self.model, self.data, q, vq, self.frame_ide[i], pin.WORLD) for i in
              range(self.armNum)]
        vJbm = np.concatenate((vJ[0], vJ[1]), axis=0)
        # vJm = vJbm[:,6:]
        # Hbmw = np.linalg.inv(Hbm.T.dot(Hbm))
        # Jw = Hbmw.dot(Jm.T).dot(np.linalg.inv(Jm.dot(Hbmw).dot(Jm.T)))
        S = np.eye(14)-np.linalg.pinv(Jm).dot(Jm)
        aq1 = np.linalg.pinv(Jm).dot(axe-vJbm.dot(vq)-Jb.dot(aqb))
        # aq1 = np.linalg.pinv(Jm).dot(axe - vJm.dot(vq[6:]))
        # Jm_inv = np.linalg.pinv(Jm)
        aq2 = S.dot(np.linalg.pinv(Hbm.dot(S)))
        # aq2 = np.linalg.pinv(Hbm.dot(S))
        vqb = vq[0:6]
        aq3 = aq2.dot(0 * vqb-Hbm.dot(aq1) - Cb)/1.2
        # aq3 = np.zeros(14)
        aq = aq1 + aq3
        print("aq123:",aq1,aq2,aq3)
        Hm = H[6:,6:]
        Fq = Hm.dot(aq) + Hbm.T.dot(aqb) + C[6:]
        # Fq = Hm.dot(aq) + C[6:]
        #

        return aq, Fq

    def getAqt3(self,q,vq,axe,aqb):
        Kp = 200 * np.eye(3)
        Kd = 0.5 * np.eye(3)
        G = -1 * np.eye(6)
        axe = np.concatenate((axe[0],axe[1]))
        aqb = np.concatenate((aqb,[0,0,0]))
        H = self.getM(q)
        C = self.getC(q,vq)
        Hbm = H[0:6,6:]
        Cb = C[0:6]
        Cb[0:3] = Cb[0:3] - Kp.dot(q[0:3]) - Kd.dot(vq[0:3])
        J = [pin.computeFrameJacobian(self.model, self.data, q, self.frame_ide[i], pin.WORLD) for i in
             range(self.armNum)]
        Jbm = np.concatenate((J[0],J[1]),axis=0)
        Jm = np.concatenate((J[0][:,6:],J[1][:,6:]),axis=0)
        Jb = np.concatenate((J[0][:,0:6],J[1][:,0:6]),axis=0)
        vJ = [pin.frameJacobianTimeVariation(self.model, self.data, q, vq, self.frame_ide[i], pin.WORLD) for i in
              range(self.armNum)]
        vJbm = np.concatenate((vJ[0], vJ[1]), axis=0)
        vJm = vJbm[:,6:]
        # Hbmw = np.linalg.inv(Hbm.T.dot(Hbm))
        # Jw = Hbmw.dot(Jm.T).dot(np.linalg.inv(Jm.dot(Hbmw).dot(Jm.T)))
        S = np.eye(14)-np.linalg.pinv(Jm).dot(Jm)
        # aq1 = np.linalg.pinv(Jm).dot(axe-vJbm.dot(vq)-Jb.dot(aqb))
        aq1 = np.linalg.pinv(Jm).dot(axe - vJm.dot(vq[6:]))
        # Jm_inv = np.linalg.pinv(Jm)
        aq2 = S.dot(np.linalg.pinv(Hbm.dot(S)))
        aq3 = aq2.dot(G.dot(vq[0:6]) - Cb - Hbm.dot(aq1))/10
        # aq3 = -aq2.dot(Hbm.dot(aq1))
        # aq3 = np.zeros(14)
        # aq1 = np.zeros(14)
        # aq2 = (np.eye(14) - Jw.dot(Jm)).dot(Hbm.T).dot(Cb)
        aq = aq1 + aq3
        Hm = H[6:,6:]
        # Fq = Hm.dot(aq)+ C[6:]/1000
        Fq = Hm.dot(aq) + Hbm.T.dot(aqb) + C[6:]
        return aq, Fq

    def getAqt4(self,q,vq,axe,aqb):
        Kp = np.array([[1000,0,0],[0,1000,0],[0,0,200]])
        Kd = 0.5 * np.eye(3)
        P = -0.1 * np.eye(12)
        W = 0.01 * np.eye(6)
        axe = np.concatenate((axe[0],axe[1]))
        aqb = np.concatenate((aqb,[0,0,0]))
        H = self.getM(q)
        C = self.getC(q,vq)
        Hbm = H[0:6,6:]
        Hb = H[0:6,0:6]
        B = np.concatenate((np.zeros((6,6)),-np.linalg.inv(Hb)),axis=0)
        Cb = C[0:6]
        # Cb[0:3] = Cb[0:3] - Kp.dot(q[0:3]) - Kd.dot(vq[0:3])
        J = [pin.computeFrameJacobian(self.model, self.data, q, self.frame_ide[i], pin.WORLD) for i in
             range(self.armNum)]
        Jbm = np.concatenate((J[0],J[1]),axis=0)
        Jm = np.concatenate((J[0][:,6:],J[1][:,6:]),axis=0)
        Jb = np.concatenate((J[0][:,0:6],J[1][:,0:6]),axis=0)
        vJ = [pin.frameJacobianTimeVariation(self.model, self.data, q, vq, self.frame_ide[i], pin.WORLD) for i in
              range(self.armNum)]
        vJbm = np.concatenate((vJ[0], vJ[1]), axis=0)
        vJm = vJbm[:,6:]
        # Hbmw = np.linalg.inv(Hbm.T.dot(Hbm))
        # Jw = Hbmw.dot(Jm.T).dot(np.linalg.inv(Jm.dot(Hbmw).dot(Jm.T)))
        S = np.eye(14)-np.linalg.pinv(Jm).dot(Jm)
        aq1 = np.linalg.pinv(Jm).dot(axe-vJbm.dot(vq)-Jb.dot(aqb))
        # aq1 = np.linalg.pinv(Jm).dot(axe - vJm.dot(vq[6:]))
        # Jm_inv = np.linalg.pinv(Jm)
        aq2 = S.dot(np.linalg.pinv(Hbm.dot(S)))
        Xb = np.concatenate((q[0:6],vq[0:6]))
        aq3 = aq2.dot(-np.linalg.inv(W).dot(B.T).dot(P).dot(Xb) - Cb - Hbm.dot(aq1))/1.2
        # aq3 = -aq2.dot(Hbm.dot(aq1))
        # aq3 = np.zeros(14)
        # aq1 = np.zeros(14)
        # aq2 = (np.eye(14) - Jw.dot(Jm)).dot(Hbm.T).dot(Cb)
        aq = aq1 + aq3
        Hm = H[6:,6:]
        # Fq = Hm.dot(aq)+ C[6:]/1000
        # he = np.concatenate((he[0],he[1]))
        Fq = Hm.dot(aq) + Hbm.T.dot(aqb) + C[6:]
        return aq, Fq


if __name__ == '__main__':
    Kp = np.array([[800, 0, 0, 0, 0, 0],
                        [0, 800, 0, 0, 0, 0],
                        [0, 0, 800, 0, 0, 0],
                        [0, 0, 0, 800, 0, 0],
                        [0, 0, 0, 0, 800, 0],
                        [0, 0, 0, 0, 0, 800]])
    Kd = Kp * 2
    Md = Kp
    dt = 0.02
    pinocchio_model_path = "models"
    urdf_path = '\\mulit_arm_urdf\\urdf\\mulit_arm_urdf2.urdf'
    # urdf_path = '\\ur_description\\urdf\\ur5_robot_no_ee.urdf'
    # end_joint = "ee_fixed_joint"
    end_frame = ["robot1_ee_link","robot2_ee_link"]
    DualC = DualSpaceArmController(Kp,Kd,Md,dt,pinocchio_model_path,urdf_path,end_frame=end_frame)
    # DualC.DirectDynamics(tau, q, vq, he, J)
    # DualC.viewerInit()
    # q = np.concatenate(([0,0,0.2,0,0,0,1],
    #                     [0,0,0,0,0,0,0],
    #                     [0,0,0,0,0,0,0]))


    # q = np.array([0.0, 0.0, 0.2, 0.0, 0.0, 0.0, 1.0, 0.0, -1.22, 2.27, -2.62, -1.57, 0])
    # Rd=np.array([[0,1,0],
    #             [-1,0,0],
    #             [0,0,1]])
    # Pd=np.array([0.435728,0.109293,0.079542]).T
    # UR5C.InverseKinematics(Rd, Pd, q)

    vq = np.zeros(20)
    # q = np.concatenate(([0, 0, 0.3, 0, 0, 0, 1],
    #                     [0.1, 1.57, 0.52, 1.04, 0.1, 1.57, 0],
    #                     [0.1, 1.57, 0.52, 1.04, 0.1, 1.57, 0]))

    q = np.concatenate(([0, 0, 0.5, 0, 0, 0, 1],
                        [0, 1.571, -0.5236, -1.0472, 0.5236, 0, 0],
                        [0, 1.571, -0.5236, -1.0472, 0.5236, 0, 0]))
    # Rd=[np.array([[-0.81388177, -0.58102869,  0.00146026],
    #    [ 0.05655666, -0.08172309, -0.99504908],
    #    [ 0.5782714 , -0.80976972,  0.09937397]]),
    #     np.array([[ 0.81388176,  0.5810287 , -0.00146021],
    #    [-0.0565567 ,  0.08172306,  0.99504908],
    #    [ 0.5782714 , -0.80976972,  0.09937397]])]
    # Pd=[np.array([0.83971373, -0.18718689,  2.84024598]), np.array([-0.83971372,  0.18718691,  2.94024598])]
    # ===== 获取初始末端位姿 =====
    pin.forwardKinematics(DualC.model, DualC.data, q)
    pin.updateFramePlacements(DualC.model, DualC.data)

    pose_L = DualC.data.oMf[DualC.frame_ide[0]]
    pose_R = DualC.data.oMf[DualC.frame_ide[1]]

    print("初始左臂位置:", pose_L.translation)
    print("初始右臂位置:", pose_R.translation)

    Rd = [np.array([[-1.87143752e-04,  6.85423107e-06,  9.99999982e-01],
       [-9.99999982e-01,  3.67328356e-06, -1.87143777e-04],
       [-3.67456622e-06, -1.00000000e+00,  6.85354352e-06]]),
          np.array([[ 1.87197342e-04, -6.85423127e-06, -9.99999982e-01],
       [ 9.99999982e-01, -3.67328319e-06,  1.87197367e-04],
       [-3.67456622e-06, -1.00000000e+00,  6.85354352e-06]])]
    Pd = [np.array([0.43489207, -0.51994866,  1.8506116]), np.array([-0.43489204,  0.51994866,  1.8506116])]
    he = [np.array([0, 0, 0, 0, 0, 0]),np.array([0, 0, 0, 0, 0, 0])]
    # vRd = np.array([0, 0, 0]) #必须为0
    # vPd = np.array([0, 0, 0])#必须为0
    DualC.step(q, vq, Pd=Pd, Rd=Rd, he=he, Controller='Admittance')
    M = DualC.getM(q)
    C = DualC.getC(q,vq)

    # DualC.step(q, vq, he=he, Controller='Admittance')
