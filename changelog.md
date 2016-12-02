[2016-12-02]
------------

-	调整tmlinfo.sluiteminfo.sluitem_idx -> tmlinfo.sluiteminfo.sluitem_barcode,原命名易误解

[2016-11-30]
------------

-	合并testconfig和showhandlers接口为servicecheck,使用do=showhandler&do=testconfig参数
-	修正get_phy_cache,参数传递错误
-	操作类接口安全方面使用判断区域0替换判断权限值

[2016-11-29]
------------

-	修正用户登录中area_r,area_w,area_x填充bug

[2016-11-28]
------------

-	用Cython封装web handler和部分方法
-	tmlinfo 中tml_id字段改为repeated格式
-	tmlnfo 增加slubaseinfo和sluitemgrpinfo

[2016-11-23]
------------

-	tmlinfo接口增加data_mark值3，只返回baseinfo中的tml_id和tml_dt_update字段
-	修正 .profile 和 lic.dll 读取路径错误bug
-	增加showhandlers接口，列出所有可用接口
-	修正部分接口中数据库读取的时间格式未转换问题
-	修正协议集中部分repeated int类型未加 [packed=true] 的问题,可能导致数据填充和读取问题

[2016-11-22]
------------

-	增加接口submitalarm
-	重命名smssublimt->sublimitsms, tcssubmit->submittcs
-	增加接口内请求参数日志记录

[2016-11-21]
------------

-	修改tcssubmit, smssubmit, ipcuplink接口参数,uuid->scode,采用YYYYMMDDHH<salt>格式,动态运算获得

[2016-11-17]
------------

-	增加区域信息查询接口:areainfo
-	增加监控专用用户登录接口:userloginjk
-	所有操作接口的phy_id字段,修改为仅对管理员或预置用户有效
-	增加分组信息接口:groupinfo

[2016-11-15]
------------

-	增加短信发送记录查询端口

[2016-11-14]
------------

-	所有接口改为post方式
-	接口uuid验证增加远程ip验证,若ip不符则注销用户,需重新登录
-	用户登录后有效时间改为30分钟
-	用户登录增加经纬度两个选填字段,返回增加zmq地址,取消socket和websocket地址
-	所有控制类接口增加phy_id字段,和tml_id同时存在时将忽略tml_id

[2016-11-11]
------------

-	完成接口:
	-	单灯数据查询
	-	终端数据查询
	-	设备基础信息查询
	-	电桩接口封装

[2016-10-21]
------------

-	重新构架项目，采用WS+ZMQ模式。
-	目前已支持接口：
	-	单灯开关灯，对时，选测（集中器/控制器）
	-	终端开关灯，选测
	-	短信提交
	-	用户管理
	-	事件记录查询，现存/历史故障查询
	-	工控机气象服务支持
-	目前与tcs服务依旧采用tcp socket方式，后期将与tcs配合改为zmq pub-sub模式
