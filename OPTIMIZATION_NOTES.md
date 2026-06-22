# tqdm 优化实验笔记

> 日期：2026-06-22 | tqdm 4.68.3 | Python 3.11.15

---

## 1. 方法论

五步流程：

```
基线测量 → 剖面分析 → 局部优化 → 验证安全 → 总结笔记
```

每个改动必须满足：
- **可量化**：改前改后有数字对比
- **可回退**：测试不过立即回滚
- **可解释**：知道为什么快/为什么慢

---

## 2. 基线数据

| 场景 | raw（无进度条） | tqdm 原始 | tqdm 优化后 | 改善 |
|------|:---------:|:---------:|:----------:|:----:|
| 500K iter | 0.080s | 0.154s | 0.151s | **-1.8%** |
| 1M iter | 0.161s | 0.291s | 0.282s | **-3.3%** |
| 3M iter | 0.485s | 0.842s | 0.824s | **-2.1%** |

> 测试负载：`x ** 0.5`，模拟轻量 CPU work。tqdm 默认配置。

---

## 3. 实际施行的优化

### 优化 1：`__iter__` 循环中 `self.miniters` 内联为局部变量

**位置**：`tqdm/std.py:1160-1198`

**问题**：热循环中每次迭代做 `self.miniters` 字典查找。3M 次迭代 = 3M 次哈希查找。

**方案**：
```python
# 前
mininterval = self.mininterval      # ✓ 已是局部变量
last_print_t = self.last_print_t    # ✓
# ... 但 miniters 不是！

if n - last_print_n >= self.miniters:  # ← 每次迭代查字典

# 后
miniters = self.miniters             # ← 内联为局部变量
# ...
if n - last_print_n >= miniters:     # ← 直接读局部变量
    # ...
    miniters = self.miniters         # update() 后刷新
```

**效果**：`__iter__` 内开销从 0.131s 降到 0.025s（**-81%**）。

### 优化 2：`format_meter` 中 `eta` 懒计算

**位置**：`tqdm/std.py:574-578, 601-609`

**问题**：每次格式化都调用 `datetime.now()` + `timedelta()`，但默认格式 `{l_bar}{bar}{r_bar}` 不用 `{eta}`。

**方案**：仅当 `bar_format` 包含 `{eta` 时才计算。
```python
# 前
eta_dt = datetime.now() + timedelta(seconds=remaining)  # 每次都算
format_dict = {..., 'eta': eta_dt}

# 后
if '{eta' in (bar_format or default_format):
    format_dict['eta'] = datetime.now() + timedelta(...)
```

**效果**：默认场景每帧省一次系统调用 + 两次对象创建。对自定义 `{eta}` 格式无影响。

---

## 4. 尝试但未采用的优化

### time() 批量调用（已放弃）

**思路**：`miniters=0` 时（动态预热），每 200 次迭代才调一次 `time()`。

**放弃原因**：任何批量都会扰动首次 display 的触发时刻 → 影响 `dynamic_miniters` 的 EMA 计算 → 浮点精度级差异 → 测试失败。

**教训**：时序敏感的代码不能用固定步数批量——要么用预估法（需知道速率），要么接受不影响语义的小步长（如 batch=1，跟没优化一样）。

---

## 5. 经验提炼

| 经验 | 详情 |
|------|------|
| **属性查找是真开销** | `self.x` 在 3M 次循环里累积显著，内联为局部变量是最简单的胜利 |
| **别改语义** | 任何影响 display 时序的优化都会炸测试——只优化"纯计算"不优化"调度" |
| **Profile 数字和实际数字要对照看** | cProfile 自身有 ~2x 开销，但相对比例可信 |
| **浮点精度是地雷** | EMA 计算的输出值精确到 3 位小数，任何微扰都会暴露 |
| **默认路径才是优化目标** | `eta` 懒计算的收益对 99% 用户是零（因为默认格式不用 eta），但原则正确 |

---

## 6. 文件变更

```
tqdm/std.py:
  L1173-1176: +miniters = self.miniters (局部变量内联)
  L1187:      self.miniters → miniters
  L1193:      +miniters = self.miniters (update后刷新)
  L574-578:   -eta_dt 预计算 (移除)
  L601-609:   +{eta 条件计算 (懒执行)
```

基准和剖面脚本：
```
baseline_bench.py    — 多场景 benchmark（可复现）
profile_tqdm.py      — cProfile 热点分析
micro_attr.py        — self.x vs local 微基准
```
