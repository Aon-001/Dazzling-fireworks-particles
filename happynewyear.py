import pygame
import random
import math
from pygame.math import Vector2
import time

import os
import sys

# 关键：不管是运行py脚本，还是运行打包后的exe，都能找到resources文件夹
def get_resource_path(relative_path):
    """获取资源的绝对路径（适配exe打包）"""
    if hasattr(sys, '_MEI PASS'):
        # 运行exe时，sys._MEI PASS是exe解压后的临时目录
        base_path = sys._MEIPASS
    else:
        # 运行py脚本时，base_path是脚本所在目录
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# 初始化pygame
pygame.init()
pygame.mixer.init()

# 屏幕设置
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("超级用心准备的春节礼物，github万人迷")
clock = pygame.time.Clock()

# 加载背景图片（替换成你的图片路径，比如"D:\python\测试\bg.jpg"）
bg_image = pygame.image.load("a/bg.jpg").convert_alpha()  # convert()提升性能
bg_image.set_alpha(10)
# 缩放背景图为「比屏幕大的正方形」，避免转动露底（边长设为1200，可改）
bg_size = 1200  # 背景图边长，建议1000-1500
bg_image = pygame.transform.scale(bg_image, (bg_size, bg_size))
bg_w, bg_h = bg_image.get_size()

# 2. 圆周转动核心参数（可按需求微调）
rotate_center = (WIDTH//2, HEIGHT//3)  # 转动中心（屏幕中上，贴合烟花区域，比纯中心更协调）
rotate_radius = 50  # 转动半径（越小，星空转得越柔和，建议50-100，太大星星跑太快）
rotate_speed = 0.012  # 角速度（越慢越自然，建议0.005-0.01，单位：弧度/帧）
current_angle = 0  # 当前转动角度（初始为0，自动累加）

# 加载透明人物PNG（替换为你的人物图文件名，和py文件同文件夹）
person_image = pygame.image.load("a/ren.png").convert_alpha()
person_image.set_alpha(50)
# 缩放人物图至合适尺寸（按需调整宽高，比如200x300，保持比例）
person_w, person_h = 800, 600
person_image = pygame.transform.scale(person_image, (person_w, person_h))
# 设置人物图固定位置（推荐右下角，避开烟花区域，可按需改）
# 右下角：(WIDTH - person_w - 20, HEIGHT - person_h - 20)
# 左下角：(20, HEIGHT - person_h - 20)
# 右上角：(WIDTH - person_w - 20, 20)
person_pos = (0, 0)

# 新增：初始化透明度（初始为0，完全透明）
person_alpha = 0
person_image.set_alpha(person_alpha)  # 设置初始透明

# 配色库：灵动的渐变色彩，适配烟花效果
TEXT_COLORS = [
    (250, 255, 200),   # 亮黄（核心色）
    (255, 230, 180),   # ehuang
    (255, 228, 225),   # cheng
    (230, 255, 240)    # qinghuang
]

# 2. 外围烟花粒子：正常多彩色系（保留烟花的丰富性）
MAIN_COLORS = [
    (255, 69, 0), (255, 150, 0), (255, 215, 0),
    (144, 238, 144), (135, 206, 250), (255, 192, 203), (218, 112, 214)
]
BG_COLOR = (10, 5, 20)  # 深紫黑背景，突出烟花
PARTICLE_SIZE = 2

# 6组四字祝福（可自行修改）
BLESS_GROUPS = [
    ["岂", "曰", "无", "衣"],  # 组1
    ["与", "子", "同", "袍"],
    ["王", "于", "兴", "师"],  # 组1
    ["修", "我", "戈", "矛"],
    ["君", "子", "逐", "鹿"],  # 组2
    ["扬", "我", "志", "兮"],  # 组3
    ["君", "子", "如", "玉"],  # 组4
    ["乱", "我", "心", "曲"],  # 组5
]

# 播放控制参数
last_firework_time = 0
GROUP_INNER_INTERVAL = 0.5  # 组内字间隔（0.5秒/字，快速连发）
GROUP_OUTER_INTERVAL = 7  # 组间停顿（4秒）
current_group_idx = 0
current_word_in_group_idx = 0
auto_play = False


# 检查新位置是否和已存在的烟花爆炸位置重叠
def is_pos_valid(new_pos, existing_fireworks, min_distance=80):
    """
    new_pos: 新生成的爆炸位置 (x,y)
    existing_fireworks: 正在显示的烟花列表
    min_distance: 最小间距（像素），避免重叠
    """
    for fw in existing_fireworks:
        # 只检查未爆炸/正在爆炸的烟花
        if fw.explode_pos and (not fw.exploded or (fw.exploded and len(fw.particles) > 0)):
            # 计算两个位置的欧氏距离
            distance = math.hypot(new_pos[0] - fw.explode_pos[0],
                                  new_pos[1] - fw.explode_pos[1])
            if distance <= min_distance:
                return False  # 距离太近，位置无效
    return True  # 位置有效，不重叠


# 生成不重叠的爆炸位置（集中在中上区域）
def get_random_explode_pos(existing_fireworks=None):
    if existing_fireworks is None:
        existing_fireworks = []
    # 最多尝试10次找不重叠的位置（避免死循环）
    for _ in range(10):
        # 中上区域：x(200-600)集中，y(80-250)靠上
        x = random.randint(80, 700)
        y = random.randint(80, 250)
        new_pos = (x, y)
        # 检查位置是否有效（不重叠）
        if is_pos_valid(new_pos, existing_fireworks):
            return new_pos
    # 如果10次都没找到，返回默认安全位置
    return (random.randint(700, 750), random.randint(100, 100))


# 粒子类（保持灵动效果，文字粒子清晰）
class Particle:
    def __init__(self, x, y, color, target_pos=None, is_text_particle=False):
        self.pos = Vector2(x, y)
        self.target_pos = target_pos
        self.color = color
        self.is_text_particle = is_text_particle

        angle = random.uniform(0, 2 * math.pi)
        if is_text_particle:
            base_speed = random.uniform(1, 4)
        else:
            base_speed = random.uniform(3, 5)

        speed_offset = random.uniform(-1, 1)
        self.vel = Vector2(
            math.cos(angle) * (base_speed + speed_offset),
            math.sin(angle) * (base_speed + speed_offset)
        )

        self.acc = Vector2(0, random.uniform(0.028, 0.032))
        self.life = random.randint(380, 420) if is_text_particle else random.randint(240, 280)
        self.size = PARTICLE_SIZE + random.uniform(-0.1, 0.1)
        self.current_alpha = 230

        self.state = "explode"
        self.gather_timer = random.randint(45, 55)
        self.hold_timer = random.randint(200, 240)

    def update(self):
        if self.is_text_particle:
            if self.state == "explode":
                decelerate = random.uniform(0.975, 0.980)
                self.vel *= decelerate
                self.vel += self.acc
                self.pos += self.vel
                self.gather_timer -= 1
                if self.gather_timer <= 0 and self.target_pos is not None:
                    self.state = "gather"
            elif self.state == "gather":
                dir_to_target = self.target_pos - self.pos
                if dir_to_target.length() > 1:
                    dir_to_target.normalize_ip()
                    gather_speed = random.uniform(1.8, 2.0)
                    self.vel = dir_to_target * gather_speed
                else:
                    self.vel *= 0.2
                self.pos += self.vel
                self.hold_timer -= 1
                if self.hold_timer <= 0:
                    self.state = "fall"
            elif self.state == "fall":
                self.vel *= random.uniform(0.975, 0.980)
                self.vel += self.acc
                self.pos += self.vel
        else:
            self.vel *= random.uniform(0.965, 0.970)
            self.vel += self.acc
            self.pos += self.vel

        self.life -= 1.0
        alpha_base = 400 if self.is_text_particle else 260
        self.current_alpha = int(self.life / alpha_base * 230)
        self.current_alpha = max(0, self.current_alpha)

    def draw(self, surface):
        if self.life > 0 and self.current_alpha > 0:
            draw_color = self.color
            draw_color = (int(draw_color[0]), int(draw_color[1]), int(draw_color[2]))

            temp_surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(temp_surf, draw_color, (int(self.size), int(self.size)), int(self.size))
            temp_surf.set_alpha(self.current_alpha)
            surface.blit(temp_surf, (int(self.pos.x - self.size), int(self.pos.y - self.size)))


# 单字采样（保证文字清晰）
def get_text_particle_targets(text, center_pos, font_size=60):
    font = pygame.font.SysFont(["SimHei", "Microsoft YaHei", "Arial"], font_size, bold=True)
    text_surf = font.render(text, True, (255, 255, 255))
    text_rect = text_surf.get_rect(center=center_pos)
    text_rect.top -= 8
    text_rect.bottom += 8
    text_rect.left -= 8
    text_rect.right += 8

    target_positions = []
    w, h = text_surf.get_width(), text_surf.get_height()

    sample_step = 1.1
    min_particles = 130
    max_particles = 260

    for y in range(text_rect.top, text_rect.bottom, int(sample_step)):
        for x in range(text_rect.left, text_rect.right, int(sample_step)):
            pixel_x = int(x - text_rect.left)
            pixel_y = int(y - text_rect.top)
            if 0 <= pixel_x < w and 0 <= pixel_y < h:
                pixel = text_surf.get_at((pixel_x, pixel_y))
                if pixel[3] > 0:
                    rx = x
                    ry = y
                    if 0 < rx < WIDTH and 0 < ry < HEIGHT:
                        target_positions.append(Vector2(rx, ry))

    if len(target_positions) < min_particles:
        while len(target_positions) < min_particles:
            rx = random.uniform(text_rect.left + 5, text_rect.right - 5)
            ry = random.uniform(text_rect.top + 5, text_rect.bottom - 5)
            target_positions.append(Vector2(rx, ry))
    elif len(target_positions) > max_particles:
        step = len(target_positions) // max_particles
        target_positions = target_positions[::step][:max_particles]

    return target_positions


# 多彩烟花粒子生成
def get_color_variations(base_color, num):
    colors = []
    r, g, b = base_color
    for _ in range(num):
        nr = max(0, min(255, r + random.randint(-30, 30)))
        ng = max(0, min(255, g + random.randint(-30, 30)))
        nb = max(0, min(255, b + random.randint(-30, 30)))
        colors.append((nr, ng, nb))
    return colors


# 烟花类（恢复升空轨迹，不重叠）
# 烟花类（修复不爆炸/落回问题，稳定升空+100%爆炸）
class Firework:
    def __init__(self, text="马"):
        self.explode_pos = None  # 先设为空，由外部传入不重叠的位置
        self.launch_pos = None  # 发射位置（底部）
        # 升空轨迹参数（清晰可见的初始粒子）
        self.trail_size = random.uniform(2.0, 2.5)  # 升空粒子大小
        # 修改1：优化速度+重力配比，保证稳定升空
        self.vel = Vector2(0, -random.uniform(10, 14))  # 提高最小升空速度
        self.acc = Vector2(0, random.uniform(0.1, 0.1))  # 降低重力加速度
        self.base_color = random.choice(MAIN_COLORS)
        self.exploded = False
        self.particles = []
        self.text = text

    def update(self):
        if not self.exploded and self.launch_pos is not None and self.explode_pos is not None:
            # 加入轻微风力偏移，更灵动
            wind_offset = random.uniform(-0.05, 0.05)
            self.vel.x += wind_offset
            self.launch_pos += self.vel
            self.vel += self.acc

            # 修改2：双重爆炸判定（到位置/到最高点）+ 缩小阈值范围，100%爆炸
            explode_threshold = self.explode_pos[1] + random.randint(3, 8)
            if self.launch_pos.y <= explode_threshold or self.vel.y >= 0:
                self.explode()
                self.exploded = True
        else:
            # 更新爆炸后的粒子
            for p in self.particles[:]:
                p.update()
                if p.life <= 0:
                    self.particles.remove(p)

    def explode(self):
        # 生成文字粒子目标位置
        text_targets = get_text_particle_targets(self.text, self.explode_pos)
        text_count = len(text_targets)
        firework_count = text_count

        # 生成烟花爆炸粒子
        firework_colors = get_color_variations(self.base_color, firework_count)
        for color in firework_colors:
            self.particles.append(Particle(self.explode_pos[0], self.explode_pos[1], color, is_text_particle=False))

        # 生成文字粒子
        text_color = random.choice(TEXT_COLORS)
        for target in text_targets:
            self.particles.append(Particle(self.explode_pos[0], self.explode_pos[1],
                                           text_color, target, is_text_particle=True))

    def draw(self, surface):
        # 绘制升空轨迹（自下而上的初始粒子，清晰可见）
        # 修改3：仅向上飞时绘制拖尾，避免下落残影
        if not self.exploded and self.launch_pos is not None and self.vel.y < 0:
            # 核心升空粒子（第一个可见的粒子）
            trail_alpha = int(150 + (HEIGHT - self.launch_pos.y) / HEIGHT * 100)
            trail_alpha = max(80, min(255, trail_alpha))
            # 绘制核心粒子
            pygame.draw.circle(surface, self.base_color,
                               (int(self.launch_pos.x), int(self.launch_pos.y)),
                               int(self.trail_size))
            # 绘制拖尾残影（模拟真实烟花轨迹）
            for i in range(1, 5):
                offset_y = self.trail_size * i * 2
                if self.launch_pos.y + offset_y < HEIGHT:
                    fade_alpha = trail_alpha - i * 30
                    if fade_alpha > 0:
                        fade_color = (*self.base_color, fade_alpha)
                        # 残影用透明表面绘制
                        temp_surf = pygame.Surface((int(self.trail_size * 2), int(self.trail_size * 2)),
                                                   pygame.SRCALPHA)
                        pygame.draw.circle(temp_surf, self.base_color, (int(self.trail_size), int(self.trail_size)),
                                           int(self.trail_size - i * 0.3))
                        temp_surf.set_alpha(fade_alpha)
                        surface.blit(temp_surf, (int(self.launch_pos.x - self.trail_size + i * 0.1),
                                                 int(self.launch_pos.y + offset_y - self.trail_size)))

        # 绘制爆炸后的粒子
        for p in self.particles:
            p.draw(surface)

    @property
    def size(self):
        return PARTICLE_SIZE + random.uniform(0.1, 0.3)


# 主函数
def main():
    global last_firework_time, current_group_idx, current_word_in_group_idx, auto_play, person_alpha
    game_state = "start"
    fireworks = []

    firework_start_time = 0  # 记录烟花播放状态的启动时间
    first_firework_delay = 1000  # 第一个烟花延迟1000毫秒=1秒
    bgm_played = False  # 标记背景音乐是否已播放
    bgm_volume = 0.5  # 音量（0-1，0静音，1最大，0.5是适中）

    # 启动界面呼吸光点参数
    center_light_r = 20
    light_breath_dir = 1
    light_speed = random.uniform(0.18, 0.22)

    running = True
    while running:
        clock.tick(60)
        # 原代码：screen.fill(BG_COLOR)
        # 新代码：绘制背景图片（0,0是左上角坐标）
        global current_angle
        # 1. 创建临时表面，用于绘制旋转后的星空图（避免原图反复旋转失真）
        temp_surf = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
        temp_surf.blit(bg_image, (0, 0))
        # 2. 旋转临时表面（绕自身中心旋转）
        rotated_bg = pygame.transform.rotate(temp_surf, math.degrees(current_angle))  # 弧度转角度
        # 3. 计算绘制坐标，让旋转后的星空图中心和屏幕转动中心重合
        rot_w, rot_h = rotated_bg.get_size()
        bg_x = rotate_center[0] - rot_w // 2
        bg_y = rotate_center[1] - rot_h // 2
        # 4. 绘制旋转后的星空背景
        screen.blit(rotated_bg, (bg_x, bg_y))
        # 5. 减慢角度累加速度（自身旋转需要更慢，否则头晕）
        current_angle += rotate_speed / 15

        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if game_state == "start":
                    center_pos = (WIDTH // 2, HEIGHT // 2)
                    dist = math.hypot(mouse_pos[0] - center_pos[0], mouse_pos[1] - center_pos[1])
                    if dist <= center_light_r + 5:
                        game_state = "firework"
                        auto_play = True
                        last_firework_time = time.time()

                        if not bgm_played:
                            try:
                                # 加载音频文件（替换成你的歌曲路径，比如"bgm.mp3"）
                                # 注意：路径不能有中文/空格，文件放在py文件同文件夹！
                                bgm = pygame.mixer.Sound("a/bgm.mp3")
                                bgm.set_volume(bgm_volume)  # 设置音量
                                # 播放并循环（-1表示无限循环，0表示只播1次）
                                bgm.play(loops=-1)
                                bgm_played = True  # 标记已播放，避免重复点击重复播
                            except Exception as e:
                                # 音频加载失败时提示（不崩溃）
                                print(f"音频加载失败：{e}，请检查文件路径/格式")

        # 启动界面
        if game_state == "start":
            center_pos = (WIDTH // 2, HEIGHT // 2)
            center_light_r += light_speed * light_breath_dir
            if center_light_r >= 30 or center_light_r <= 15:
                light_breath_dir *= -1
                light_speed = random.uniform(0.18, 0.22)

            light_r = 255 - random.randint(0, 10)
            light_g = 200 - random.randint(0, 10)
            light_b = 100 - random.randint(0, 10)
            pygame.draw.circle(screen, (light_r, light_g, light_b), center_pos, int(center_light_r))
            inner_r = int(center_light_r * 0.6)
            pygame.draw.circle(screen, (255, 240, 200), center_pos, inner_r)

            # 1. 记录程序启动时间（仅初始化一次，放在main函数开头）
            if 'start_time' not in locals():  # 避免重复赋值
                start_time = pygame.time.get_ticks()  # 获取程序启动的毫秒数

            tip_font_big = pygame.font.SysFont(["方正小标宋简体", "Arial"], 30)
            tip_font = pygame.font.SysFont(["华文行楷", "Arial"], 25)

            text1 = "神说，要有光"
            surf1 = tip_font_big.render(text1, True, (148, 159, 226))
            rect1 = surf1.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 80))  # 上方位置（y轴减80）
            screen.blit(surf1, rect1)

            text2 = "小杭点击光源，跟我去一个明亮的地方"
            current_time = pygame.time.get_ticks()  # 获取当前毫秒数
            delay_time = 1500  # 延迟1500毫秒=1.5秒
            if current_time - start_time >= delay_time:
                # 可选：加透明度渐变（从0→255，1秒渐显，更自然）
                # 计算渐变进度：延迟后每帧透明度+2，直到255
                fade_duration = 12000  # 渐变1秒
                elapsed_after_delay = current_time - start_time - delay_time
                text2_alpha = min(255, int(elapsed_after_delay / fade_duration * 255))

                tip_font_normal = pygame.font.SysFont(["华文行楷", "Arial"], 22)
                text2 = "小杭点击光源，跟我去一个明亮的地方"
                # 创建带透明度的文字表面
                surf2 = tip_font_normal.render(text2, True, (148, 159, 226))
                surf2.set_alpha(text2_alpha)  # 设置透明度
                rect2 = surf2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 80))
                screen.blit(surf2, rect2)

        # 自动播放逻辑（四字组+不重叠+升空轨迹）
        elif game_state == "firework" and auto_play:
            current_time = time.time()

            if firework_start_time == 0:
                firework_start_time = pygame.time.get_ticks()

            is_first_firework = (current_group_idx == 0 and current_word_in_group_idx == 0)
            if is_first_firework:
                elapsed_time = pygame.time.get_ticks() - firework_start_time
                if elapsed_time < first_firework_delay:
                    # 未到1秒，跳过本次循环，不发射第一个烟花
                    pass
                else:
                    # 到1秒，执行第一个烟花发射逻辑
                    if current_time - last_firework_time >= GROUP_INNER_INTERVAL:
                        current_word = BLESS_GROUPS[current_group_idx][current_word_in_group_idx]
                        firework = Firework(text=current_word)
                        explode_pos = get_random_explode_pos(fireworks)
                        firework.explode_pos = explode_pos
                        firework.launch_pos = Vector2(explode_pos[0], HEIGHT + random.randint(10, 30))
                        fireworks.append(firework)
                        current_word_in_group_idx += 1
                        last_firework_time = current_time

            # 自动播放逻辑（四字组+不重叠+升空轨迹）
            elif game_state == "firework" and auto_play:
                current_time = time.time()
                # ========== 核心修改：记录烟花启动时间 + 第一个烟花延迟 ==========
                # 首次进入firework状态时，记录启动时间（毫秒级，适配延迟判断）
                if firework_start_time == 0:
                    firework_start_time = pygame.time.get_ticks()

                # 第一个烟花：判断是否过了1秒延迟
                is_first_firework = (current_group_idx == 0 and current_word_in_group_idx == 0)
                if is_first_firework:
                    elapsed_time = pygame.time.get_ticks() - firework_start_time
                    if elapsed_time < first_firework_delay:
                        # 未到1秒，跳过本次循环，不发射第一个烟花
                        pass
                    else:
                        # 到1秒，执行第一个烟花发射逻辑
                        if current_time - last_firework_time >= GROUP_INNER_INTERVAL:
                            current_word = BLESS_GROUPS[current_group_idx][current_word_in_group_idx]
                            firework = Firework(text=current_word)
                            explode_pos = get_random_explode_pos(fireworks)
                            firework.explode_pos = explode_pos
                            firework.launch_pos = Vector2(explode_pos[0], HEIGHT + random.randint(10, 30))
                            fireworks.append(firework)
                            current_word_in_group_idx += 1
                            last_firework_time = current_time
                # 非第一个烟花：执行原有逻辑，无延迟
                else:
                    # ==============================================
                    # 组内快速连发
                    if (current_group_idx < len(BLESS_GROUPS) and
                            current_word_in_group_idx < 4 and
                            current_time - last_firework_time >= GROUP_INNER_INTERVAL):

                        current_word = BLESS_GROUPS[current_group_idx][current_word_in_group_idx]
                        firework = Firework(text=current_word)
                        explode_pos = get_random_explode_pos(fireworks)
                        firework.explode_pos = explode_pos
                        firework.launch_pos = Vector2(explode_pos[0], HEIGHT + random.randint(10, 30))
                        fireworks.append(firework)

                        current_word_in_group_idx += 1
                        last_firework_time = current_time

                    # 组间停顿
                    elif (current_group_idx < len(BLESS_GROUPS) and
                          current_word_in_group_idx >= 4 and
                          current_time - last_firework_time >= GROUP_OUTER_INTERVAL):

                        current_group_idx += 1
                        current_word_in_group_idx = 0
                        last_firework_time = current_time

                        # 循环播放
                        if current_group_idx >= len(BLESS_GROUPS):
                            current_group_idx = 0
                            current_word_in_group_idx = 0

        # 更新并绘制所有烟花
        for fw in fireworks[:]:
            fw.update()
            fw.draw(screen)
            # 清理已消失的烟花
            if fw.exploded and len(fw.particles) == 0:
                fireworks.remove(fw)

        # 显示提示文字
        if game_state == "firework":
            content_font = pygame.font.SysFont(["华文行楷", "Arial"], 20)
            hint_font = pygame.font.SysFont(["SimHei", "Arial"], 16)
            if current_group_idx < len(BLESS_GROUPS):
                # 烟花内容（华文行楷）
                current_group_name = "".join(BLESS_GROUPS[current_group_idx])
                # 辅助说明（原有字体）
                helper_text = " | 文字烟花乱序循环播放 "
            else:
                # 无烟花内容时，全部用正常字体
                current_group_name = ""
                helper_text = "播放中... | ESC退出"
            if current_group_name:
                # 渲染烟花内容（华文行楷，颜色可稍亮突出）
                content_surf = content_font.render(current_group_name, True, (148, 180, 226))  # 亮橙黄，和文字粒子呼应
                # 渲染辅助说明（原有颜色）
                helper_surf = hint_font.render(helper_text, True, (148, 180, 226))
                # 计算位置：内容在左，辅助说明紧跟在内容右侧
                content_x = 10
                helper_x = content_x + content_surf.get_width()
                hint_y = HEIGHT - 25
                # 依次绘制
                screen.blit(content_surf, (content_x, hint_y))
                screen.blit(helper_surf, (helper_x, hint_y))
            else:
                # 无烟花内容时，直接绘制辅助说明
                helper_surf = hint_font.render(helper_text, True, (148, 180, 226))
                screen.blit(helper_surf, (10, HEIGHT - 25))

            # 透明度从0→255渐变（每帧+2，直到255）
            if person_alpha < 255:
                person_alpha += 2
                person_image.set_alpha(person_alpha)
            # 绘制人物图
            screen.blit(person_image, person_pos)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()