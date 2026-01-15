# Flutter 版本兼容性说明

**更新日期**: 2026年1月15日

---

## ⚠️ 重要变更

### `--web-renderer` 参数已移除

**影响版本**: Flutter 3.7+

**错误信息**:
```
Could not find an option named "--web-renderer".
```

**原因**: 
- Flutter 3.7+ 版本移除了 `--web-renderer` 参数
- 现在Flutter会自动选择最佳的渲染器

**解决方案**:
```bash
# ❌ 旧命令（不再支持）
flutter run -d chrome --web-port=8080 --web-renderer=html

# ✅ 新命令
flutter run -d chrome --web-port=8080 --web-hostname=0.0.0.0
```

---

## 📋 当前推荐配置

### 开发环境

```bash
cd frontend
flutter run -d chrome --web-port=8080 --web-hostname=0.0.0.0
```

### 生产构建

```bash
cd frontend
flutter build web --release
```

---

## 🔍 检查Flutter版本

```bash
flutter --version
```

**推荐版本**: Flutter 3.10+

---

## 🛠️ 渲染器说明

### 自动选择（Flutter 3.7+）

Flutter现在会根据浏览器自动选择最佳渲染器：

- **CanvasKit**: 更好的性能和一致性（默认）
- **HTML**: 更小的包体积，更快的加载

### 手动指定（仅构建时）

如果需要指定渲染器，可以在构建时使用：

```bash
# 使用 CanvasKit 渲染器
flutter build web --web-renderer canvaskit

# 使用 HTML 渲染器
flutter build web --web-renderer html

# 自动选择（推荐）
flutter build web --web-renderer auto
```

**注意**: `flutter run` 命令不再支持 `--web-renderer` 参数

---

## 📚 相关文档

- [Flutter Web渲染器](https://docs.flutter.dev/platform-integration/web/renderers)
- [Flutter版本发布说明](https://docs.flutter.dev/release/release-notes)

---

## ✅ 已更新的文件

以下文件已移除 `--web-renderer` 参数：

- `scripts/start_frontend_lan.sh`
- `docs/LAN_ACCESS_FIX.md`
- `QUICK_START_LAN.md`
- `START_SERVICES.md`

---

**状态**: ✅ 已修复  
**兼容性**: Flutter 3.7+
