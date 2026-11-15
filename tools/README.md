# tools —— 从 SolidWorks 批量导出的脚本

这些脚本通过 **SolidWorks COM 接口**批量导出，用于生成 `SW_Ready/交换模型/` 下的 STEP/STL 以及 `web3d/assets/` 下的网页 3D 模型。日常使用不需要它们，只在模型改动后重新生成时需要。

## 环境要求

- SolidWorks 2025（已安装且能通过 COM 启动）
- 互操作程序集（随 SW 安装）：
  `D:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\api\redist\SolidWorks.Interop.sldworks.dll`

## 1. `sw_export_formats.cs` —— 批量导出 STEP + STL

输入一个 TSV 任务清单，三列用制表符分隔，**必须使用绝对路径**（SW 不接受相对路径）：

```
C:\...\SW_Ready\零件\连接件\雷达转接件.SLDPRT<TAB>C:\...\交换模型\STEP\雷达转接件.step<TAB>C:\...\交换模型\STL\雷达转接件.stl
```

输出列留空表示跳过该格式。运行：

```powershell
$api = 'D:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\api\redist'
$sw = "$api\SolidWorks.Interop.sldworks.dll"; $sc = "$api\SolidWorks.Interop.swconst.dll"
[Reflection.Assembly]::LoadFrom($sw) | Out-Null      # 必须先加载，否则运行期找不到程序集
[Reflection.Assembly]::LoadFrom($sc) | Out-Null
Add-Type -ReferencedAssemblies $sw,$sc -Path tools\sw_export_formats.cs
[ExportFormats]::Run("$PWD\export_list.tsv")
```

注意：网格扫描件（`零件/机器人/*`）导出 STEP 会得到 0 实体的空文件，属正常现象，应跳过 STEP 仅导 STL。

## 2. `sw_export_assembly_stl.cs` —— 按装配坐标导出整机 STL

对装配体本身 `SaveAs` STL，SolidWorks 会为每个组件写出一份**已在装配坐标系中**的 STL（命名形如 `ASM - 组件名-1.STL`）。这是 `web3d` 模型能正确拼装的关键：直接用「零件局部 STL + MathTransform 变换」会因为零件原点与网格坐标系不一致而错位。

```powershell
Add-Type -ReferencedAssemblies $sw,$sc -Path tools\sw_export_assembly_stl.cs
[AsmExport]::Run("$PWD\SW_Ready\装配体\无头Go2传感器安装总装.SLDASM", "$PWD\.web3d\asm_stl")
```

## 3. `build_glb_from_asm_stl.py` —— 生成网页用彩色 GLB

读取上一步的 `asm_stl`，按组件配颜色、减面（二分搜索最大体素步长，保证面数不低于目标，避免薄壁件被压塌）、Z-up→Y-up 旋转、居中，输出 `go2_full.glb` / `go2_sensors.glb`。

```powershell
python -X utf8 tools\build_glb_from_asm_stl.py
```

依赖：`numpy`、`trimesh`。
