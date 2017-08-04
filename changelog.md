[2017-08-04]
---
- 加密配置文件中的数据库密码
- 对用户登录接口中的sql注入攻击漏洞进行修复

[2017-08-03]
---
- 整加QueryDataAls

[2017-08-01]
---
- 数据查询类接口('query'开头)，增加fetchunlimited参数处理，默认最大查询3000组数据
- 修正querydatamru接口历史数据查询bug
- 优化querydatartu和querydataslu查询语句

[2017-07-31]
---
- 修正sunrisetinfo接口数据库语句错误
- 修正queryeventstimetabledo接口命名错误，以及sql语句错误

[2017-07-28]
---
- 内置用户增加接口访问控制权限

[2017-07-19]
---
- 修正故障查询接口sql语句拼接错误
- 终端最新数据查询改为查询最新数据视图，当视图不存在时依然从历史数据中筛选获取

[2017-07-07]
------------

- 增加tcsport隐藏参数，用来区分访问的基础数据库名称
- 终端操作部分接口增加合肥协议支持

[2017-06-22]
------------

- 修正基础数据缓存不更新的漏洞

[2017-06-19]
------------

- 终端选测，终端批量开关灯，召测版本，对时，读取时钟增加ahhf协议支持

[2017-06-09]
------------

- 协议集增加Mahalo()结构

[2017-06-07]
------------

- 配置文件增加cross_domain项，true-允许跨域（默认），false-禁止跨域，功能采用重写flush()方法实现

[2017-06-06]
------------

- 新增 4.8 时间表开关灯操作记录查询接口querytimetabledo
- 协议集增加LocationInfo结构，用来查询中国城市经纬度
- 协议集ProjectInfo结构增加设备总数，故障总数，经纬度等信息

[2017-05-26]
------------

- 监控相关的数据访问类接口增加隐藏参数：givemejson，若存在，结果将以json格式返回。

[2017-05-24]
------------

- userlogin()结构增加tcs字段，返回对应的通信服务端口
- userlogin()结构zmq字段赋值改变，同时返回pull和pub端口号

[2017-05-17]
------------

- 工作流接口增加通用接口,FlowWorkHandler, 路由地址为`/flow/.\*`
- 优化uas模块载入时user_list表字段新增的代码,先判断是否存在字段,再判断是否新增
- zmqproxy由zmq.poller改为zmq.proxy控制转发

[2017-05-15]
------------

- 优化xsql模块,修正异常链接不释放的bug

[2017-05-08]
------------

- 修正ipcuplink接口数据库创建bug

[2017-04-21]
------------

- 新增`_mysql_no_fetch`方法,用于执行insert,delete,update等语句,返回affected_rows和insert_id,支持多语句
- 简化`_mysql_generator_sql_mysql`方法输入参数
- 优化`mydata_collector`方法流程

[2017-04-20]
------------

- 调整终端和单灯接口中操作相关接口的权限
- 调整配置文件参数

[2017-04-18]
------------

- 增加uas_url配置项

[2017-04-11]
------------

- 配合用户单点登录调整部分用户相关协议google协议字段
- 增加uas模块

[2017-04-06]
------------

- 修正单灯控制相关接口中缓存访问错误问题

[2017-03-28]
------------

- 调整userloginjk接口,直接访问userlogin接口
- 修改queryemdata接口的uuid验证为scode验证
- areainfo和groupinfo接口增加pb2参数

[2017-03-15]
------------

- 修正电表查询接口tml_id条件无效bug

[2017-03-10]
------------

- 修正气象数据查询None值处理bug

[2017-03-03]
------------

- 增加zmqproxy，iisi所有zmq接口在未配置ip地址的情况下，直接使用pub广播，若配置ip地址，则采用push推送至zmqproxy服务
- mariadb数据库操作改为异步
- 增加抄表接口

[2017-01-12]
------------

- 增加rtuverget,rtutimerctl,sluverget接口
- slutimerset接口改为slutimerctl,支持设置/召测

[2017-01-09]
------------

- 取消mysqldb.constants定义(windows下打包无法加载)
- 增加querydatamru和mrudataget接口
- 取消控制类接口的phy_id字段,规范接口格式
- 增加终端估算电量查询接口

[2016-12-27]
------------

- 修正单灯控制指令重复base64编码bug
- 修正tmlinfo接口data_mark=5 sql语句错误bug
- 单灯操作类接口增加485用字段 subitem_id
- 修正工作流接口出错处理中的bug、
- 用封装的conf类替换原配置文件处理方法

[2016-12-23]
------------

- 工作流接口封装，访问超时由5秒增加到12秒，以应对工作流接口性能不稳定问题

[2016-12-20]
------------

- 修正现存故障查询和历史故障查询语句中字段不匹配的bug
- 因存在技术问题，暂时取消异步http数据库访问

[2016-12-14]
------------

- 配置文件增加远程查询接口参数
- 数据查询方法调整为自动判断采用本地MySQLdb还是远程查询
- 优化查询/缓存性能（数据库操作性能和heidisql相同），接口响应方面，100w条终端历史数据查询接口操作总耗时约39～43s
- 终端最新数据查询以及单灯最新数据查询支持多终端同时查询
- 因部分查询数据特殊，无法从记录总数统计分页数量，因此当分页序号大于可能的分页总数时，返回空

[2016-12-08]
------------

- userloginjk 移动平台用户始终登录工作流
- 数据查询类接口不再跨库查询phy_id和tml_name
- 增加405页面

[2016-12-05]
------------

- 增加err404页面
- 将读写查询缓存放到cython中用threading加速
- sysinfo查询参数处理bug fix
- check_arguments增加参数是否存在判断

[2016-12-02]
------------

- 调整tmlinfo.sluiteminfo.sluitem_idx -> tmlinfo.sluiteminfo.sluitem_barcode,原命名易误解

[2016-11-30]
------------

- 合并testconfig和showhandlers接口为servicecheck,使用do=showhandler&do=testconfig参数
- 修正get_phy_cache,参数传递错误
- 操作类接口安全方面使用判断区域0替换判断权限值

[2016-11-29]
------------

- 修正用户登录中area_r,area_w,area_x填充bug

[2016-11-28]
------------

- 用Cython封装web handler和部分方法
- tmlinfo 中tml_id字段改为repeated格式
- tmlnfo 增加slubaseinfo和sluitemgrpinfo

[2016-11-23]
------------

- tmlinfo接口增加data_mark值3，只返回baseinfo中的tml_id和tml_dt_update字段
- 修正 .profile 和 lic.dll 读取路径错误bug
- 增加showhandlers接口，列出所有可用接口
- 修正部分接口中数据库读取的时间格式未转换问题
- 修正协议集中部分repeated int类型未加 [packed=true] 的问题,可能导致数据填充和读取问题

[2016-11-22]
------------

- 增加接口submitalarm
- 重命名smssublimt->sublimitsms, tcssubmit->submittcs
- 增加接口内请求参数日志记录

[2016-11-21]
------------

- 修改tcssubmit, smssubmit, ipcuplink接口参数,uuid->scode,采用YYYYMMDDHH<salt>格式,动态运算获得

[2016-11-17]
------------

- 增加区域信息查询接口:areainfo
- 增加监控专用用户登录接口:userloginjk
- 所有操作接口的phy_id字段,修改为仅对管理员或预置用户有效
- 增加分组信息接口:groupinfo

[2016-11-15]
------------

- 增加短信发送记录查询端口

[2016-11-14]
------------

- 所有接口改为post方式
- 接口uuid验证增加远程ip验证,若ip不符则注销用户,需重新登录
- 用户登录后有效时间改为30分钟
- 用户登录增加经纬度两个选填字段,返回增加zmq地址,取消socket和websocket地址
- 所有控制类接口增加phy_id字段,和tml_id同时存在时将忽略tml_id

[2016-11-11]
------------

- 完成接口:
	- 单灯数据查询
	- 终端数据查询
	- 设备基础信息查询
	- 电桩接口封装

[2016-10-21]
------------

- 重新构架项目，采用WS+ZMQ模式。
- 目前已支持接口：
	- 单灯开关灯，对时，选测（集中器/控制器）
	- 终端开关灯，选测
	- 短信提交
	- 用户管理
	- 事件记录查询，现存/历史故障查询
	- 工控机气象服务支持
- 目前与tcs服务依旧采用tcp socket方式，后期将与tcs配合改为zmq pub-sub模式
