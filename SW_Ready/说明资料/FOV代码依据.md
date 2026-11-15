# wmp_go2代码视场依据

来源：用户提供的wmp_go2-main.zip，未修改源码。压缩包SHA256：`00dd45450f8f0643a04532d5f34cc9d36eb13ac4f2334b1237a4f3ea5c41088c`。部分原注释编码不能按UTF-8显示，不影响参数数值读取。

Go2 depth继承A1 depth，未覆盖horizontal_fov与64×64尺寸；故策略深度视场为水平58°、垂直58°。play.py中的75°属于env录屏相机，不是depth.horizontal_fov。相机位置参数按用户要求不参与本次符合性判断，也没有修改。

## legged_gym/envs/go2/go2_amp_config.py

```text
72:     class depth(A1AMPCfg.depth):
73:         camera_num_envs = 512
74:         # 机身上方的虚拟前视相机，不代表 Go2 真机相机或雷达的外参。
75:         position = [0.28, 0.0, 0.10]
76:         y_angle = [-5.0, 5.0]
```

## legged_gym/envs/a1/a1_amp_config.py

```text
164:     class depth:
165:         use_camera = True
166:         backend = "warp"  # "isaac" or "warp"
167:         camera_num_envs = 1100 # 300 512 1024
168: 
169:         position = [0.28, 0, 0.12]  # front camera
170:         position_noise = 0.01  # XYZ position randomization: +/- 1cm
171:         y_angle = [15, 25]  # positive pitch down
172:         z_angle = [-2, 2]  # yaw randomization [deg]
173:         x_angle = [-2, 2]  # roll randomization [deg]
174: 
175:         update_interval = 5  # 5 works without retraining, 8 worse
176: 
177:         original = (64, 64)
178:         resized = (64, 64)
179:         horizontal_fov = 58
180:         buffer_len = 2
181: 
182:         near_clip = 0
183:         far_clip = 2
```

## legged_gym/sensors/warp/warp_cam.py

```text
29:     def initialize_camera_matrices(self):
30:         # Calculate camera params
31:         W = self.width
32:         H = self.height
33:         (u_0, v_0) = (W / 2, H / 2)
34:         f = W / 2 * 1 / math.tan(self.horizontal_fov / 2)
35: 
36:         vertical_fov = 2 * math.atan(H / (2 * f))
37:         alpha_u = u_0 / math.tan(self.horizontal_fov / 2)
38:         alpha_v = v_0 / math.tan(vertical_fov / 2)
```

## legged_gym/envs/base/legged_robot.py

```text
241:     def process_depth_image(self, depth_image, env_id):
242:         # These operations are replicated on the hardware
243:         # depth_image = self.crop_depth_image(depth_image)
244:         depth_image += self.cfg.depth.dis_noise * 2 * (torch.rand(1)-0.5)[0]
245:         depth_image = torch.clip(depth_image, -self.cfg.depth.far_clip, -self.cfg.depth.near_clip)
246:         # depth_image = self.resize_transform(depth_image[None, :]).squeeze()
247:         depth_image = self.normalize_depth_image(depth_image)
```

## legged_gym/scripts/play.py

```text
170:     env_cfg.env.enable_camera_sensors = record_frames and args.headless
171:     if env_cfg.env.enable_camera_sensors:
172:         env_cfg.env.camera_width = 1280
173:         env_cfg.env.camera_height = 720
174:         env_cfg.env.camera_horizontal_fov = 75.0
175:         # RGB 视频最终写入 CPU 文件，直接读取图像，避免跨设备图形互操作产生空张量。
176:         env_cfg.env.camera_enable_tensors = False
177:     fix_depth_camera_pose(env_cfg.depth)
178:     print(f'Depth camera position: {env_cfg.depth.position}; downward pitch: {env_cfg.depth.y_angle[0]:.1f} deg')
```
