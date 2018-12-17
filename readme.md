# 交互式综合服务接口

> Interactive Integrated Services Interface

#### 开发依赖项：

- tornado
- pyinstaller: 建议使用 v3.3.0 版本
- pyzmq
- MySQL-python
- mxpsu: 动态库请通过 github.com/xyzj/pypsu 下载源码后编译
- google protobuf: 建议直接将 python 模块源码复制到项目目录中使用，在线包的版本存在兼容性问题。

#### 安装运行

##### 编译

- 使用`python build_iisi.py`(windows)或`./build_iisi.sh`(linux)编译程序。

##### 运行

- 将编译后可执行程序复制到项目发布的 bin 目录中即可。

  > Windows 系统下默认编译输出文件名为`iisi.exe`
  > Linux 系统下默认编译输出文件名为`iisi`

- 启动参数
  - `-h`: 打印帮助
  - `--version`: 显示版本信息
  - `--debug`: 打印运行过程中的调试信息
  - `--conf`： 设置配置文件路径，若配置文件不存在会使用默认值生成一个新的配置文件

#### 其他说明

- 运行日志存放在 bin 父目录下的 log 文件夹中。
- 启动参数可以通过`iisi.exe --help`（windows）或`iisi --help`(linux)查询。
