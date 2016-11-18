路灯综合利用管理平台接口说明
============================

(The Description of Lighting Utilization Management Platform Interface)

所有接口采用 HTTP 协议 get/post 方式请求,提交的参数和返回数据格式为 Google Protocol Buffer ( protobuf ) 协议序列化后再经由 base64 编码得到的字符串

-	protobuf 协议格式说明

协议采用 proto3 格式编写,使用 protoc v3.0 beta2 编译

-	头结构:

> 该头结构将插入每个请求或返回的协议结构体中  
> 协议类名加前缀 "rq" 表示客户端->服务端,无前缀表示服务端->客户端

```protobuf
message Head {
    int64 idx = 1;  // 序号(必填)
    int32 ver = 2;  // 协议版本(必填,默认为协议发布日期6位整型)。当前版本为 160328
    string if_name = 3;  // 接口名称(可选)
    int64 if_dt = 4;  // 请求或返回时间(必填)

    int32 if_st = 100;  // 接口操作状态(必填)
                            // 1-操作成功, 0-操作失败, 原因参考msg, 10-用户未登录或超时(1h),请求被拒绝, 11-用户权限不足
                            // 41-数据库连接失败,42-指令提交失败(socket pool),43-第三方接口调用失败,45-数据库提交失败,46-参数错误

    string if_msg = 101;  // 失败时填充详细原因(可选)

    int32 paging_num = 200;  // 此次请求/应答是否使用分页(仅对非参数数据查询类接口有效,'query'开头的接口),0-不使用,大于0时使用,但是,若客户端请求的赋值>100或数据总量大于100,服务端按照100进行强制分页
    int32 paging_idx = 201;  // 分页序号,从1开始,当序号大于分页总数时默认返回最后页
    int32 paging_total = 202;  // 服务端返回该次请求产生的分页总数(客户端请求数据时不填充)
    int64 paging_buffer_tag = 203;  // 分页缓存标签,0-要求服务器重建缓存,xx-根据服务器返回的tag从对应缓存读取数据
    int32 paging_record_total = 204;  // 查询记录总数
}
```

-	公共应答

```
message CommAns {
    Head head = 1;  // 协议头信息
}
```

-	部分常用字段以及缩写说明

```
tml_id:     设备逻辑地址(系统分配,不可设置)
phy_id:     设备物理地址(硬件地址,可设置)
rtu:        终端
slu:        单灯
ldu:        防盗
als:        光照度设备
esu:        节能设备
mru:        电表
sluitem:       单灯控制器
lduitem:       防盗末端
st:         状态
num:        数量
idx:        序号,索引号
msg:        详细信息
if:         接口
desc:       描述
pwd:        密码
rq:         请求
wsock:      websocket
ws:         webservice
grp:        组
argv:       参数
comm:       通信
hw:         硬件
adv:        进阶
```

版本 v160328:
-------------

### 一. 用户/区域类

> 所有用户均包含隐含属性:客户代码,即系统终端和服务器的通信端口号,当管理员创建新用户时,新用户自动继承该属性,所有操作也默认从uuid中获取该属性作为必要条件  
> 用户权限: 1-X(可操作),2-W(可设置),4-R(可查询),3-XW(可操作,可设置),5-RX(可查询,可操作),6-RW(可设置,可查询),7-RWX(可查询,可设置,可操作),15-DRWX(管理员)

---

#### 用户验证

> 接口名称: userlogin (*get*\)  
> 对登录用户的用户名和密码进行验证,验证成功返回uuid,有效期默认60分钟(可通过配置文件热更新)

参数:  
1. pb2 - 详细参数(结构如下)

```protobuf
message rqUserLogin {
    Head head = 1;  // 协议头信息
    int32 dev = 2;  // 设备类型,1-pc,2-web,3-移动设备,不同设备同一用户可同时登录,同种设备同一用户互斥
    string unique = 3;  // 移动设备唯一标示(移动设备填充,可以由服务器配置文件设置是否校验)
    string user = 4;  // 用户名
    string pwd = 5;  // 密码(md5加密传输)
}
```

访问示例:

返回:

```protobuf
message UserLogin {
    Head head = 1;  // 协议头信息
    string uuid = 2;  // 用户验证成功后分配的uuid(系统生成)
    int32 auth = 3;  // 用户权限值
    string fullname = 4;  // 用户全名
    string user_db = 5;  // 用户关联数据库名称
    int32 user_area = 6;  // 用户的区域id
    string push_service = 7;  // 信息推送服务地址(socket)
    string push_service_wsock = 8;  // 信息推送服务地址(websocket)
}
```

---

#### 用户注销

> 接口名称: userlogout (*get*\)  
> 用户退出登录,注销uuid

参数:  
1. uuid - 用户uuid

访问示例:

返回:  
CommAns应答

---

#### 用户uuid续订

> 接口名称: userrenew (*post*\)  
> 用户续订当前uuid,续订后有效期为续订成功开始60分钟

参数:  
1. uuid - 用户当前uuid  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqUserRenew {
    Head head = 1;
    int32 dev = 2;  // 设备类型,1-pc,2-web,3-移动设备
    string unique = 3;  // 移动设备唯一标示(移动设备填充)
}
```

访问示例:

返回: CommAns应答

---

#### 添加用户

> 接口名称: useradd (*post*\)  
> 管理员添加用户信息

参数:  
1. uuid - 管理员uuid  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqUserAdd {
    Head head = 1;
    string user = 2;  // 新用户登录名(用户登录名不可修改)
    string fullname = 3;  // 新用户全名
    string pwd = 4;  // 新用户密码
    int32 area_id = 5;  // 新用户所属区域id
    int32 auth = 6;  // 新用户权限值,
    string tel = 7;  // 新用户手机号
    string code = 8;  // 新用户移动设备操作码(开关灯操作时输入)
    string dbname = 9;  // 用户管理的数据库名称
}
```

访问示例:

返回:  
CommAns应答

---

#### 删除用户

> 接口名称: userdel (*post*\)  
> 管理员删除用户

参数:  
1. uuid - 管理员uuid  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqUserDel {
    Head head = 1;
    string user_name = 3;  // 要删除的用户名
}
```

访问示例:

返回: CommAns应答

---

#### 修改用户参数

> 接口名称: useredit (*post*\)  
> 管理员修改用户参数

参数:  
1. uuid - 用户uuid  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqUserEdit {
    Head head = 1;
    string user_name = 2;  // 要修改的用户id
    string fullname = 3;  // 新用户全名
    string pwd = 4;  // 新用户密码(md5序列化后传输)如为空值表示不改密码
    int32 area_id = 5;  // 新用户所属区域id
    int32 auth = 6;  // 新用户权限值
    string tel = 7;  // 新用户手机号
    string code = 8;  // 新用户移动设备操作码(开关灯操作时输入)
    string pwd_old = 9;  // 旧密码(uuid为管理员时不需要)
}
```

访问示例:

返回:  
CommAns应答

---

#### 请求用户信息

> 接口名称: userinfo (*get*\)  
> 管理员查看用户信息

参数:  
1. uuid - 管理员uuid  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqUserInfo {
    Head head = 1;
    string user_name = 2;  // 要请求的用户名(留空-请求全部)
}
```

访问示例:

返回:

```protobuf
message UserInfo {
    message UserView {
        string user = 1;  // 用户登录名
        string fullname = 2;  // 用户全名
        string pwd = 3;  // 用户密码
        int32 auth = 4;  // 用户权限值
        string tel = 5;  // 用户手机号
        string code = 6;  // 用户移动设备操作码(开关灯操作时输入)
        int32 user_id = 7;  // 用户id
        int32 area_id = 8;  // 所属区域id
        string db_name = 9;  // 所属数据库名称
    }
    Head head = 1;
    repeated UserView user_view = 2;
}
```

---

### 二. 基础信息类

#### 系统基础信息

> 接口名称: sysinfo (*get*\)  
> 获取系统名称等信息

参数:  
1. uuid - 用户登录成功获得的uuid  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqSysInfo {
    Head head = 1;
    repeated int32 data_mark = 2[packed=true];  // 查询类型标记,1-系统名称,2-终端总数/启用数量/在线数量,3-现存故障总数,终端现存故障总数,单灯现存故障总数,防盗现存故障总数,7-服务运行状态
}
```

访问示例:

返回:

```protobuf
message SysInfo {
    Head head = 1;
    repeated int32 data_mark = 2[packed=true];  // 查询类型标记,同请求
    string sys_name = 3;  // 系统名称
    repeated int32 tml_num = 4 [packed=true];  // [终端总数,启用数量,在线数量]
    repeated int32 err_num = 5 [packed=true];  // 故障总数 [现存故障总数,终端现存总数,单灯现存故障总数,防盗现存故障总数]
    repeated int32 st_svr = 6;  // [数据服务,通信服务],0-服务不在线,1-服务在线,2-服务状态未知
}
```

---

#### 系统名称修改

> 接口名称: sysedit (*post*\)  
> 修改系统名称

参数:  
1. uuid - 用户登录成功获得的uuid  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqSysEdit {
    Head head = 1;
    string sys_name = 2;  // 新的系统名称
}
```

访问示例:

返回:  
CommAns应答

---

#### 事件信息获取

> 接口名称: eventinfo (*get*\)  
> 修改系统名称

参数:  
1. uuid - 用户登录成功获得的uuid

```protobuf
message rqEventInfo {
    Head head = 1;
}
```

访问示例:

返回:

```protobuf
message EventInfo {
    message EventView {
        int32 event_id = 1;
        string event_name = 2;
    }
    Head head = 1;
    repeated EventView event_view = 2;
}
```

---

#### 区域新增/修改/删除

> 接口名称: areaedit (*post*\)  
> 新增/修改/删除 区域设置,系统默认一个大区

参数:  
1. uuid - 用户登录成功获得的uuid  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqAreaEdit {
    Head head = 1;
    int32 opt = 2;  // 操作,1-新增,2-删除,3-修改
    int32 area_id = 3;  // 区域id(修改,删除时填充)
    string area_name = 4;  // 区域名称(新增,修改时填充)
	string area_desc = 5;  // 区域描述
}
```

访问示例:

返回:  
CommAns应答

---

#### 区域信息获取

> 接口名称: areainfo (*get*\)  
> 获取区域信息列表

参数:  
1. uuid - 用户登录成功获得的uuid

访问示例:

返回:

```protobuf
message AreaInfo {
    message AreaView {
        int32 area_id = 1;  // 区域id
        string area_name = 2;  // 区域名称
		string area_desc = 3;  // 区域描述
    }
    Head head = 1;
    repeated AreaView area_view = 2;
}
```

---

#### 终端分组信息获取

> 接口名称: grpinfo (*get*\)  
> 获得系统分组信息

参数:  
1. uuid - 用户登录成功获得的uuid  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqGrpInfo {
    Head head = 1;
    int32 grp_id = 2;  // 分组id,-1-获取全部
}
```

访问示例:

返回:

```protobuf
message GrpInfo {
    message GrpView {
        int32 grp_id = 1;  // 分组id
        string grp_name = 2;  // 分组名称
        int32 grp_order = 3;  // 分组排序(针对所属区域)
        int32 area_id = 4;  // 分组所属区域id
        string grp_desc = 5;  // 分组描述
    }
    Head head = 1;
    repeated GrpView grp_view = 2;
}
```

---

#### 终端分组新增/修改/删除

> 接口名称: grpedit (*post*\)  
> 添加一个分组

参数:1. uuid - 用户登录成功获得的uuid2. pb2 - 详细参数(结构如下)

```protobuf
message rqGrpEdit {
    Head head = 1;
    int32 opt = 2;  // 操作,1-新增,2-删除,3-修改
    int32 grp_id = 7;  // 分组id
    string grp_name = 3;  // 分组名称
    int32 grp_order = 4;  // 分组排序(针对所属区域)
    int32 area_id = 5;  // 分组所属区域id
    string grp_desc = 6;  // 分组描述
}
```

访问示例:

返回:  
CommAns应答

---

#### 故障基础信息查询

> 接口名称: errinfo (*get*\)  
> 获得系统故障名称,自定义名称,报警模式等信息

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqErrInfo {
    Head head = 1;
    int32 err_id = 5;  // 请求故障基础信息的id,-1-返回所有数据
}
```

访问示例:

返回:

```protobuf
message ErrInfo {
    message ErrView {
        int32 err_id = 1;  // 故障id
        string err_name = 2;  // 故障名称
        string err_name_custome = 3;  // 自定义名称
        int32 err_level = 4;  // 故障等级
        int32 voice_times = 5;  // 语音报警次数
        int32 enable_alarm = 6;  // 允许报警
        int32 enable_push = 7;  // 允许推送(针对当前用户)
        int32 enable_sms = 8;  // 允许发送短信(针对当前用户)
        repeated int32 tml_exclude = 9 [packed=true];  // 设置不将当前故障推送给用户的特例终端地址
    }
    Head head = 1;
    repeated ErrView err_view = 2;
}
```

---

#### 故障信息修改

> 接口名称: erredit (*post*\)  
> 修改故障的自定义名称,故障等级,报警次数,允许报警等

参数:  
1. uuid - 管理员的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqErrEdit {
    Head head = 1;
    repeated ErrInfo.ErrView err_view = 2;  // 报警信息(可以同时提交多条)
}
```

访问示例:

返回:  
CommAns应答

---

#### 自定义故障添加/删除/修改

> 接口名称: errcustomedit (*post*\)  
> 添加自定义故障类型

参数:  
1. uuid - 管理员的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqErrCustomeEdit {
    Head head = 1;
    int32 opt = 2;  // 1-新增,2-删除, 3-修改
    repeated ErrInfo.ErrView err_view = 3;  // 报警信息(可以同时提交多条)
}
```

访问示例:

返回:  
CommAns应答

---

### 三. 设备信息类

> 设备信息以模块为节点,与模块直接通信的设备均为主设备,下挂在模块下,通过终端485通信的设备或各类末端为附属设备,下挂在对应设备下 tml-泛指各类设备,rtu-路灯终端,als-光照度,slu-单灯,ldu-防盗,mru-抄表,esu-节能,com-模块

#### 主设备基础信息返回

> 接口名称: tmlinfo (*get*\)  
> 获取各类设备的基本参数以及工作参数

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqTmlInfo {
    Head head = 1;
    repeated int32 data_mark = 5;  // 请求数种类,1-baseinfo,2-tmlsubinfo,3-gisinfo,4-operateinfo,5-rtuinfo,6-RtuCurrentAlarmInfo,7-rtulightrateinfo,8-sluinfo,9-lduinfo,10-alsinfo,11mruinfo,12-esuinfo,13-esuopt
    int32 tml_id = 6;  // 请求的设备id,-1-返回所有数据
}
```

访问示例:

返回:

```protobuf
message TmlInfo {
    message BaseInfo {
        int32 phy_id = 1;  // 设备物理地址
        int32 tml_type = 2;  // 设备型号,1-终端,2-光控,3-节能,4-防盗,5-单灯,6-抄表
        int32 tml_st = 3;  // 设备状态,0-不用,1-停运,2-启用
        string tml_name = 4;  // 设备名称
        int32 tml_com_id = 5;  // 设备模块id
        int32 tml_com_sn = 8;  // 设备模块序列号(可以为sim卡号,需要出厂设置)
        int32 tml_com_ip = 9;  // 模块ip地址(绑定ip时可设置,否则无意义)
        int32 tml_model = 10;  // 设备型号,3005,3006,2090,3090等
        int32 tml_parent_id = 11;  // 父设备id
        int64 tml_dt_setup = 12;  // 安装日期
        string tml_desc = 13;  // 备注
        int64 tml_dt_update = 14;  // 最后更新时间
        string tml_street = 15;  // 安装位置
    }
    message TmlZoneInfo {
        int32 tml_area_id = 6;  // 设备区域地址(当区域地址和分组地址均为0时,表示该设备为公共设备,所有区域均可见,但只能由管理员编辑)
        int32 tml_grp_id = 7;  // 设备分组地址
    }
    message GisInfo {
        double tml_pix_x = 1;  // 位图x坐标
        double tml_pix_y = 2;  // 位图y坐标
        double tml_gis_x = 3;  // gis x坐标
        double tml_gis_y = 4;  // gis y坐标
    }
    message OperateInfo {
        repeated int32 switchout_id = 1 [packed=true];  // 回路序号
        repeated int32 tt_id = 2 [packed=true];  // 周设置表或年设置表id,10000+为周设置,30000+为年设置
    }
    message RtuInfo {
        repeated int32 work_mark = 1 [packed=true];  // 工作标志(界面建议不呈现),默认[1,0,0,1,1,1,0,1],0-false,1-true,[允许滚动显示(),允许声响报警,禁止报警,允许呼叫,允许开机申请,允许自检,禁止主报,禁止路由]
        int32 heart_beat = 2;  // 心跳周期,(单位分钟,默认60)(界面建议不呈现)
        int32 active_report = 3;  // 主报周期,(单位分钟,默认260)(界面建议不呈现)
        int32 alarm_delay = 4;  // 报警延迟,(单位秒,默认15)(界面建议不呈现)
        int32 voltage_range = 6;  // 电压量程
        int32 voltage_uplimit = 7;  // 电压上限
        int32 voltage_lowlimit = 8;  // 电压下限
        repeated string loop_switchout_name = 9; // 开关量输出名称
        repeated int32 switchout_verctor = 10 [packed=true];  // 开关量输出矢量,(1-16,依次填入)
        repeated RtuLoopItem rtu_loop_item = 11;  // 回路信息
        double shield_small_current = 12;  // 屏蔽小电流，0-表示不屏蔽，>0 表示低于设定值的电流屏蔽显示
        int32 loop_st_switch_by_current = 13;  // 采用电流判断是否吸合，0-不采用，1-采用
         
    }
    message SluInfo {
        int32 slu_off_line = 1;  // 停运,0-false,1-true
        int32 slu_auto_alarm = 2;  // 允许主报,0-false,1-true
        int32 slu_auto_patrol = 3;  // 允许巡测,0-false,1-true
        int32 slu_auto_resend = 4;  // 允许自动补发指令,0-false,1-true
        int32 slu_suls_num = 5;  // 控制器数量
        int32 slu_bt_pin = 6;  // 蓝牙pin码,默认62547600
        int32 slu_domain = 7;  // 域名,1-65535
        int32 slu_voltage_uplimit = 8;  // 电压报警上限,默认300
        int32 slu_voltage_lowlimit = 9;  // 电压报警下限,默认170
        int64 slu_zigbee_id = 10;  // zigbee地址
        int32 slu_comm_fail_count = 11;  // 通信失败报警,1-50,默认5
        double slu_power_factor = 12;  // 功率因数报警,0.4-1.0,默认0.6,发送时*100
        repeated slu_zigbee_comm = 13;  // 通信信道,1-16,可输入多个
        int32 slu_current_range = 14;  // 电流量程,0.1~20A,发送时*10
        int32 slu_power_range = 15;   // 功率量程,10~2000W,发送时/10
        double slu_lon = 16;  // 经度
        double slu_lat = 17; // 纬度
        int32 slu_route = 18;  // 路由模式,1-5,默认1
        int32 slu_bt_security = 19;  // 蓝牙安全模式,0-无安全模式,1-配对成功即可,2-配对+主站确认,默认0
        int32 slu_saving_mode = 20;  // 节能方式,1-pwm,2-485,默认1
        int32 slu_pwm_rate = 21;  // pwm频率或485波特率
        repeated SluItemInfo sluitem_item_info = 22;
    }
    message LduInfo {
        int32 lduitem_id = 1;  // 防盗集中器地址
        repeated LdusItemInfo lduitem_info = 2;
    }
    message AlsInfo {
        int32 als_id = 1;  // 光照度地址
        int32 als_range = 2;  // 光照度量程,1-100,2-10000, 默认2
        int32 als_mode = 3;  // 光照度模式,0-每隔5s主动上报(用户电脑串口直连),1-选测应答(选测1),2-按设定间隔主动上报(选测2),3-485连接下按设定间隔主动上报(选测3),4-按设定间隔主动上报(选测4)
        int32 als_interval = 4;  // 上报间隔,单位秒,默认10
        int32 als_comm = 5; // 1-串口直连,2-gprs,3-485
    }
    message MruInfo {
        repeated mru_id = 1;  // 抄表地址,六字节
        int32 mru_baud_rate = 2;  // 波特率
        int32 mru_transformer = 3;  // 电表变比
        int32 mru_type = 4;  // 协议版本,1-1997,2-2007
    }
    message EsuInfo {
		bool esu_used = 1;  // 有效标示  0-不用,1-使用
		int32 esu_preheating_time = 2;  // 预热时间 默认2分钟
		int32 esu_close_time = 4;  // 关机时间 不设置
		int32 esu_open_time = 5;  // 开机时间 不设置
		int32 esu_ct_radio_a = 6;  // A相接触器变比 50~500 默认150
		int32 esu_ct_radio_b = 7;  // B相接触器变比 50~500 默认150
		int32 esu_ct_radio_c = 8;  // C相接触器变比 50~500 默认150
		int32 esu_time_mode = 25;  // 时间模式：0 为定时模式 ；1为延时模式；默认1
		int32 esu_run_mode = 26;  // 运行模式：0 自动，1 手动； 默认 0
		int32 esu_fansatrt_temp = 9;  // 风机启动温度 默认45
		int32 esu_fanclose_temp = 10;  // 风机关闭温度 默认35
		int32 esu_enery_save_temp = 11;  // 退出节能温度 默认 70 界面设置
		int32 esu_mandatory_protect_temp = 12;  // 强制保护温度 默认85
		int32 esu_recover_temp = 13;  // 恢复节能温度 默认50
		double esu_input_overvoltage_limit = 14;  // 输入过压门限值 默认270
		double esu_Input_undervoltage_limit = 15;  // 输入欠压门限值 默认170
		double esu_output_undervoltage_limit = 16;  // 输出欠压门限值 默认160
		double esu_output_overload_limit = 17;  // 输出过载门限值 默认 144 电流
		int32 esu_regulating_speed = 18;  // 调压速度 仅模式为延时模式时有效 默认10 6~60
		int32 esu_power_phases = 19;  // 供电相数  默认3 不提供界面设置
		int32 esu_comm_type = 23;  // 通信模式 ：0 通过终端；1 通过通信模块 默认0
		int32 esu_work_mode = 24;  // 工作模式：0 通用模式；1 特殊模式；不提供界面设置 默认0
		int32 esu_auto_alarm = 20;  // 是否主动报警 0-false,1-true,0
		int32 esu_alarm_delay = 21;  // 报警延时时间  默认10秒钟
		int32 esu_mode = 22;  // 节能模式：0 接触器模式；1 IGBT模式 默认1
        repeated EsuAdjustVoltage esu_adjust_voltage = 23;
    }
    message EsuAdjustVoltage {
    	int32 esu_operate_id = 2;  // 操作序号 共有8个时间需要 1~8
    	int32 esu_operatoe_value = 3;  // 操作节能值
    	int32 esu_operate_time = 4;  // 操作时间 如00：30  则为30 时*60+分
    	int64 esu_update_time = 5;  // 本条信息更新时间
    }
    message RtuLoopItem {
        int32 loop_id = 1;  // 回路序号
        string loop_name = 2;  // 回路名称
        int32 loop_phase = 3;  // 回路电压相位,0-a,1-b,2-c
        int32 loop_current_range = 4;  // 回路电流量程
        int32 loop_switchout_id = 9;  // 回路对应的开关量输出id(1-16), 0-表示无对应开关量输出
        int32 loop_switchin_vector = 11;  // 回路对应的模拟量矢量(1-36)
        int32 loop_transformer = 12;  // 回路互感器比值
        int32 loop_transformer_num = 13;  // 回路互感器圈数(默认1)
        int32 loop_step_alarm = 14;  // 回路跳变报警
        int32 loop_st_switch = 15;  // 0-常开,1-常闭,默认1
    }
    message RtuCurrentAlarmInfo {
        repeated int32 loop_current_uplimit1 = 5 [packed=true];  // 回路电流报警一级上限
        repeated int32 loop_current_uplimit2 = 6 [packed=true];  // 回路电流报警二级上限
        repeated int32 loop_current_lowlimit1 = 7 [packed=true];  // 回路电流报警一级下限
        repeated int32 loop_current_lowlimit2 = 8 [packed=true];  // 回路电流报警二级下限
    }
    message RtuLightRateInfo {
        repeated double loop_light_rate = 1;  // 亮灯率因数
    }
    message SluItemInfo {
        repeated int32 sluitem_grp_id = 1 [packed=true];  // 组地址,0-254,默认[0,0,0,0,0]
        int64 sluitem_idx = 2;  // 条码
        int32 sluitem_power_uplimit = 3;  // 功率上限
        int32 sluitem_power_lowlimit = 4;  // 功率下限
        repeated int32 sluitem_route = 5 [packed=true];  // 控制器路由(前4级通信控制器编号1,2,3...)
        int32 sluitem_order = 6;  // 开灯序号
        repeated int32 sluitem_st_poweron = 7 [packed=true];  // 4路上电状态,0-关灯,1-开灯,默认[1,1,1,1]
        int32 sluitem_st = 8;  // 控制器状态,0-停运,1-投运
        int32 sluitem_alarm = 9;  // 控制器主报,0-不允许,1-允许
        repeated int32 sluitem_vector = 10 [packed=true];  // 4路矢量,默认[1,2,3,4]
        int32 sluitem_loop_num = 11; // 回路数量
        repeated int32 sluitem_rated_power = 12 [packed=true];  // 4路额定功率(w),0-不设置,1-0:20,2-76:100,3-101:120,4-121:150,5-151:200,6-201:250,7-251:300,8-301:400,9-401:600,10-601:800,11-800:1000,12-1001:1500,13-1501:2000,14-21:50,15-51:75
        string sluitem_name = 13;  // 名称
        int32 sluitem_id = 14;  // 地址,唯一,不可变
        int32 sluitem_phy_id = 15; // 物理地址,可变
        string sluitem_lamp_id = 16;  // 灯杆编号/名称
    }
    message LdusItemInfo {
        int32 loop_id = 1;  // 线路id
        string loop_name = 2;  // 线路名称
        int32 loop_st = 3;  // 线路状态,0-不用,1-使用
        int32 loop_transformer = 4;  // 互感器量程
        int32 loop_phase = 5;  // 相位
        string loop_lamppost = 6;  // 末端灯杆编号
        int32 loop_lighton_ss = 7;  // 开灯信号强度门限,默认400
        int32 loop_lightoff_ss = 8;  // 关灯信号强度门限,默认200,(界面可隐藏)
        int32 loop_lighton_ia = 9;  // 开灯阻抗报警门限,默认100,(界面可隐藏)
        int32 loop_lightoff_ia = 10;  // 关灯阻抗报警门限,默认600
        int32 loop_lighting_rate = 11;  // 开灯亮灯率报警门限,默认80,(界面可隐藏)
        repeated int32 loop_alarm_set = 12 [packed=true];  // 回路报警标识,0-false,1-true,共8个,默认[1,0,0,0,0,1,0,1],依次为[开灯信号强度告警,开灯阻抗告警,亮灯率变化告警,线路失电告警,关灯信号告警,关灯阻抗告警,线路短路告警,主动上报]
        string loop_desc = 13; // 备注
        int32 tml_loop_id = 14;  // 终端对应的回路序号
    }
    message TmlView {
        TmlZoneInfo tml_zone_info = 9;  // 设备所属设置
        RtuCurrentAlarmInfo rtu_current_alarm_info = 10;  // 电流上下限报警设置
        RtuLightRateInfo rtu_light_rate_info = 11;  // 亮灯率因数
        BaseInfo base_info = 12;  // 设备基础信息
        GisInfo gis_info = 13;  // 设备地理信息
        OperateInfo opt_info = 14;  // 时间表关联信息
        RtuInfo rtu_info = 15;  // 终端设备填充(返回完整数据时填充)
        SluInfo slu_info = 16;  // 单灯设备填充(返回完整数据时填充)
        LduInfo ldu_info = 17;  // 防盗设备填充(返回完整数据时填充)
        AlsInfo als_info = 18;  // 光照度设备填充(返回完整数据时填充)
        MruInfo mru_info = 19;  // 抄表设备填充(返回完整数据时填充)
        EsuInfo esu_info = 20;  // 节能设备填充(返回完整数据时填充)
    }
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 设备逻辑地址
    repeated TmlView tml_view = 3; 
}
```

---

#### 主设备新增/删除/修改

> 接口名称: tmledit (*post*\)  
> 添加/删除/修改主设备相关信息

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqTmlEdit {
    Head head = 1;
    int32 opt = 2;  // 操作,1-新增,2-删除,3-修改
    repeated int32 data_mark = 3;  // 请求数种类,1-baseinfo,2-tmlsubinfo,3-gisinfo,4-operateinfo,5-rtuinfo,6-RtuCurrentAlarmInfo,7-rtulightrateinfo,8-sluinfo,9-lduinfo,10-alsinfo,11mruinfo,12-esuinfo,13-esuopt
    int32 tml_id = 4;  // 设备逻辑地址
    TmlInfo.TmlView tml_view = 9;
}
```

访问示例:

返回:  
CommAns应答

---

### 四. 计划任务类

#### 计划任务查询

> 接口名称: crontabinfo (*get*\)  
> 查询计划任务的详细内容

参数:1. uuid - 登录成功获得的动态id2. pb2 - 详细参数(结构如下)

```protobuf
message rqCrontabInfo {
    Head head = 1;
    int64 cron_id = 2;  // 计划任务id,-1-查询全部
}
```

访问示例:

返回:

```protobuf
message CrontabInfo {
    message CrontabView {
        int64 cron_id = 1;  // 计划任务id
        string cron_name = 2;  // 计划任务名称
        int32 cron_type = 3;  // 计划任务对象类型,1-终端,2-光控,3-节能,4-防盗,5-单灯,6-抄表
        repeated int32 cron_targets = 4 [packed=true];  // 计划任务对象id(设置逻辑地址)
        int32 cron_comm = 5;  // 计划任务执行通信方式,0-保留,1-电台,2-串口232,3-串口485,4-Zigbee,5-电力载波,6-Socket
        int32 cron_opt = 6;  // 计划任务内容,10-终端选测,11-终端单回路开灯,12-终端单回路关灯,13-终端多回路控制
                             // 20-光控选测
                             // 30-节能选测,31-节能调档
                             // 40-防盗选测
                             // 50-单灯选测,51-单灯开灯,52-单灯关灯,53-单灯节能
                             // 60-抄表
        string cron_als_value = 15;  // 计划任务光控值,0表示无需光控
        string cron_argv = 14;  // 辅助参数,如单灯节能的百分比,开关回路等
        string cron_minute = 7;  // 计划任务执行时间分钟设置
        string cron_hour = 8;  // 计划任务执行时间小时设置
        string cron_day = 9;  // 计划任务执行时间日期设置
        string cron_month = 10;  // 计划任务执行时间月设置
        string cron_week = 11;  // 计划任务执行时间星期设置
        int32 cron_times = 12;  // 计划任务执行次数,0-无限
        int32 cron_lock = 13;  // 0-不锁定,表示用户可编辑,1-锁定,表示该任务由系统相关模块产生,用户不可修改(如时间表),默认不传输锁定的系统任务
    }
    Head head = 1;
    repeated CrontabView crontab_view = 2;
}
```

> crontab时间设置格式说明  
> ![](static/image/crontab.png)  
> 在以上各个字段中，还可以使用以下特殊字符：  
> + 星号(*\): 代表所有可能的值，例如month字段如果是星号,则表示在满足其它字段的制约条件后每月都执行该命令操作  
> + 逗号(,): 可以用逗号隔开的值指定一个列表范围,例如日期字段"1,2,5,7,8,9"表示每月的1,2,5,7,8,9号  
> + 中杠(-): 可以用整数之间的中杠表示一个整数范围,例如星期字段"2-6"表示"2,3,4,5,6"  
> + 正斜线(/): 可以用正斜线指定时间的间隔频率,例如小时字段"0-23/2"表示每两小时执行一次,相当于0,2,4,...2同时正斜线可以和星号一起使用,例如*/10,如果用在minute字段,表示每十分钟执行一次

---

#### 新增/删除/修改计划任务

> 接口名称: crontabedit (*post*\)  
> 新增/删除/修改计划任务

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqCrontabEdit {
    Head head = 1;
    int32 opt = 2;  // 操作,1-新增,2-删除,3-修改
    CrontabInfo.CrontabView crontab_view = 3;  // 计划任务内容(删除时只需要填充cron_id)
}
```

访问示例:

返回:  
CommAns应答

---

### 五. 时间管理类

#### 周设置时间表查询

> 接口名称: weektabinfo (*get*\)  
> 周设置时间表查询 周设置保存时,保存至2张表: + 一张为规则表记录该时间表的基本规则,用于用户重置设置使用 + 一张为以该规则计算出的全年时间表,不开灯的日期开关最后时限固定写入1500(25*60) 终端开关量输出绑定时间表id,默认从第二张表直接读取开关灯时间

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqWeektabInfo {
    Head head = 1;
    int32 wt_id = 2;  // 周时间表id,留空表示全部
}
```

访问示例:

返回:

```protobuf
message WeektabInfo {
    message WeektabView {
        message WeektabSet {
            int32 week = 1;  // 星期,0-6
            int32 als_on_enable = 2;  // 允许光控开,0-不允许,1-允许
            int32 als_on_value = 3;  // 开光控值
            int32 als_off_enable = 4;  // 允许关光控,0-不允许,1-允许
            int32 als_off_value = 5;  // 关光控值
            int32 offset_on_enable = 6;  // 允许开偏移,0-不允许,1-允许
            int32 offset_on_value = 7;  // 开偏移值
            int32 offset_off_enable = 8;  // 允许关偏移,0-不允许,1-允许
            int32 offset_off_value = 9;  // 关偏移值
            int32 deadline_on = 10;  // 开灯最后时限 h*60+m
            int32 deadline_off = 11;  // 关灯最后时限 h*60+m
        }
        int32 wt_id = 1;  // 时间表id,非自动递增,10000开始
        string wt_name = 2;  // 时间表名称
        string wt_desc = 3;  // 时间表描述
        repeated WeektabSet weektab_set = 4;  // 时间表设置
    }
    Head head = 1;
    repeated WeektabView week_tab_view = 2;
}
```

---

#### 年时间表查询

> 接口名称: yeartabinfo (*get*\)  
> 年时间表查询

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqYeartabInfo {
    Head head = 1;

    int32 yt_id = 2;  // 年时间表id,留空表示全部
    int32 start_date = 3;  // 查询开始月日,MMDD格式转int
    int32 end_date = 4;  // 查询结束月日,MMDD格式转int
    // 查询结束日期小于查询开始日期时,默认查询开始日期当天,查询开始结束日期均为0时,查询全年
}
```

访问示例:

返回:

```protobuf
message YeartabInfo {
    message DaySet {
        int32 day = 1;  // 有效日
        int32 month = 2;  // 有效月
        repeated StageSet stage_set = 5;
    }
    message StageSet {
        int32 stage_id = 1;  // 多段开关编号(1-4)
        int32 als_on_enable = 2;  // 允许光控开,0-不允许,1-允许
        int32 als_off_enable = 4;  // 允许关光控,0-不允许,1-允许
        int32 offset_on_enable = 6;  // 允许开偏移,0-不允许,1-允许
        int32 offset_off_enable = 8;  // 允许关偏移,0-不允许,1-允许
        int32 deadline_on = 10;  // 开灯最后时限 h*60+m
        int32 deadline_off = 11;  // 关灯最后时限 h*60+m
    }
    message YeartabView {
        int32 yt_id = 1;  // 时间表id,非自动递增,30000开始
        string yt_name = 2;  // 年表名称
        int32 area_id = 3;  // 关联的区域id
        string yt_desc = 4;  // 描述
        int32 als_on_value = 5;  // 开光控值
        int32 als_off_value = 6;  // 关光控值
        int32 offset_on_value = 7;  // 开偏移值
        int32 offset_off_value = 8;  // 关偏移值
        repeated DaySet day_set = 9;  // 每日设置
    }
    Head head = 1;

    repeated YeartabView year_tab_view = 6;
}
```

---

#### 新增/删除/修改周设置时间表

> 接口名称: weektabedit (*post*\)  
> 新增/删除/修改周设置时间表

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqWeektabEdit {
    Head head = 1;
    int32 opt = 2;  // 操作,1-新增,2-删除,3-修改
    WeektabInfo.WeektabView weektab_view = 3;  // 删除时只需要填充wt_id
}
```

访问示例:

返回:  
CommAns应答

---

#### 新增/删除/修改年时间表

> 接口名称: yeartabedit (*post*\)  
> 新增/删除/修改年时间表

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqYeartabEdit {
    Head head = 1;
    int32 opt = 2;  // 操作,1-新增,2-删除,3-修改
    YeartabInfo.YeartabView yeartab_view = 3;  // 删除时只需要填充yt_id
}
```

访问示例:

返回:  
CommAns应答

---

### 六. 设备控制类

#### 终端开关灯,停运/解除停运

> 接口名称: rtuctl (*post*\)  
> 向终端发送开关灯指令

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqRtuCtl {
    message RtuDo {
        int32 opt = 1;  // 1-单回路开关,2-多回路开关,3-停运,4-解除停运
        repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
        repeated int32 loop_do = 3 [packed=true];  // 从回路1开始最大16,要操作的内容0-关,1-开,2-不变,如3005共6个输出需要开启1,4,关闭2,6,则填入[1,0,2,1,2,0](opt=3,4时无效)
    }
    Head head = 1;
    repeated RtuDo rtu_do = 2;
}
```

访问示例:

返回:  
CommAns应答

---

#### 终端选测

> 接口名称: rtudataget (*post*)  
> 终端选测

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqRtuDataGet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
}
```

访问示例:

返回:  
CommAns应答

---

#### 终端参数召测

> 接口名称: rtuargvget (*post*)  
> 终端参数召测

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message RtuArgvGet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
}
```

访问示例:

返回:  
CommAns应答

---

#### 终端周设置召测

> 接口名称: rtuweektabget (*post*)  
> 终端周设置召测

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqRtuWeektabGet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
}
```

访问示例:

返回:  
CommAns应答

---

#### 终端年设置召测

> 接口名称: rtuyeartabget (*post*)  
> 终端年设置召测

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqRtuYeartabGet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
    int32 start_month = 3;  // 查询起始月
    int32 start_day = 4;  // 查询起始日
    int32 day_count = 5;  // 查询天数
    repeated int32 loop_id = 6 [packed=true];  // 回路编号,共16路,0-不查询,1查询,如查询回路1,2,则填入[1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
}
```

访问示例:

返回:  
CommAns应答

---

#### 终端对时

> 接口名称: rtutimerset (*post*)  
> 终端对时

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqRtuTimerSet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
}
```

访问示例:

返回:  
CommAns应答

---

#### 终端参数下发

> 接口名称: rtutimerset (*post*)  
> 终端参数下发

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqRtuArgvSet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
    int32 argv_type = 3;  // 要发送的参数类型,0-全部,1-工作,2-模拟量,3-开关量,4-上下限,5-电压
}
```

访问示例:

返回:  
CommAns应答

---

#### 终端周设置下发

> 接口名称: rtuweektabset (*post*)  
> 终端周设置下发

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqRtuWeektabSet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
}
```

访问示例:

返回:  
CommAns应答

---

#### 终端年时间下发

> 接口名称: rtuyeartabset (*post*)  
> 终端年时间下发

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqRtuYeartabSet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
}
```

访问示例:

返回:  
CommAns应答

---

#### 终端版本召测

> 接口名称: rtuverset (*post*)  
> 终端版本召测

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqRtuVerSet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
}
```

访问示例:

返回:  
CommAns应答

---

#### 抄表

> 接口名称: mrudataget (*post*)  
> 抄表

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqMruDataGet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
}
```

访问示例:

返回:  
CommAns应答

---

#### 抄表召测地址

> 接口名称: mruaddrget (*post*)  
> 抄表召测地址

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqMruAddrGet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
}
```

访问示例:

返回:  
CommAns应答

---

#### 光照度选测

> 接口名称: alsdataget (*post*)  
> 光照度选测

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqAlsDataGet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
}
```

访问示例:

返回:  
CommAns应答

---

#### 光照度模式设置

> 接口名称: alsargvset (*post*)  
> 光照度模式设置

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqAlsArgvSet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
}
```

访问示例:

返回:  
CommAns应答

---

#### 光照度模式召测

> 接口名称: alsargvget (*post*)  
> 光照度模式召测

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqAlsArgvGet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
}
```

访问示例:

返回:  
CommAns应答

---

#### 光照度版本召测

> 接口名称: alsverget (*get*)  
> 光照度版本召测

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqAlsVerGet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
}
```

访问示例:

返回:  
CommAns应答

---

#### 节能选测

> 接口名称: esudataget (*post*)  
> 节能选测

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqEsuDataGet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
}
```

访问示例:

返回:  
CommAns应答

---

#### 节能参数下发

> 接口名称: esuargvset (*post*)  
> 节能参数下发

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqEsuArgvSet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
}
```

访问示例:

返回:  
CommAns应答

---

#### 节能参数召测

> 接口名称: esuargvget (*post*)  
> 节能参数召测

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqEsuArgvGet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
}
```

访问示例:

返回:  
CommAns应答

---

#### 节能控制

> 接口名称: esuctl (*post*)  
> 节能控制

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqEsuCtl {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
    // todo
}
```

访问示例:

返回:  
CommAns应答

---

#### 节能对时

> 接口名称: esutimer (*post*)  
> 节能控制

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqEsuCtl {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
}
```

访问示例:

返回:  
CommAns应答

---

#### 单灯集中器选测

> 接口名称: sludataget (*post*)  
> 单灯集中器选测

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqSluDataGet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
    int32 data_mark = 3;  // 选测内容标示, 0-选测集中器状态,4-选测控制器物理信息,6-选测控制器辅助数据,7-选测控制器基本数据
    int32 sluitem_idx = 4;  // 控制器起始地址
    int32 sluitem_num = 5;  // 控制器数量
    int32 cmd_idx = 6;  // 命令序号
}
```

访问示例:

返回: CommAns应答

---

#### 单灯控制器选测

> 接口名称: sluitemdataget (*post*)  
> 单灯控制器选测

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqSluitemDataGet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
    int32 sluitem_idx = 3;  // 控制器地址
    Data_mark data_mark = 4;  // 选测标示
    int32 cmd_idx = 5;  // 命令序号
    message Data_mark {
        int32 read_data = 1;  // 选测
        int32 read_timer = 2;  // 读取时钟
        int32 read_args = 3;  // 读取运行参数
        int32 read_group = 4;  // 读取组地址
        int32 read_ver = 5;  // 读取版本
        int32 read_sunriseset = 6;  // 读取当天日出日落
        int32 read_timetable = 7;  // 读取本地参数（新）
        int32 read_ctrldata = 8;  // 读取控制器数据（新）
    }
}
```

访问示例:

返回: CommAns应答

---

#### 单灯控制

> 接口名称: sluctl (*post*)  
> 单灯控制

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqSluCtl {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
    int32 cmd_idx = 3;  // 序号
    int32 operation_type = 4;  // 指令类型 0-清除，1-定时，2-经纬度，3-即时
    int32 operation_order = 5;  // 操作顺序 0-广播，1-依次
    int32 addr_type = 6;  //地址类型 0-全部，1-组，2-规则，3-单一，4-gprs
    repeated int32 addrs = 7 [packed=true];  // 控制器地址
    repeated int32 week_set = 8 [packed=true];  // 周设置
    int32 timer_or_offset = 9;  // 定时 hh*60+mm->int32 或偏移量 依据 operation_type定
    int32 cmd_type = 10;  // 操作类型 3-经纬度关灯，4-混合控制，5-pwm调节，6-485调节
    repeated int32 cmd_mix = 11 [packed=true];  // 混合回路操作 0-不操作，1-开灯，2-1档节能，3-2档节能，4-关灯（经纬度关灯时，cmd_type<4视为不操作）
    CmdPWM cmd_pwm = 12;  // pwm功率调节
    message CmdPWM {
        repeated int32 loop_can_do = 1 [packed=true];  // 回路(仅需要操作的回路序号)
        int32 scale = 2;  // 比例 0-100 -> 0%-100%
        int32 rate = 3;  // 频率 /100为发送值
    }
}
```

访问示例:

返回:  
CommAns应答

---

#### 单灯对时

> 接口名称: slutimerset (*post*)  
> 单灯对时

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqSluTimerSet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
}
```

访问示例:

返回:  
CommAns应答

---

#### 单灯集中器参数下发

> 接口名称: sluargvset (*post*)  
> 单灯参数下发

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqSluArgvSet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
    int32 send_hub_patrol = 3;  // 设置允许巡测/停止巡测
    int32 send_hub_run = 4;  // 设置停运/启用,主动报警/禁止报警
    int32 send_hub_argv = 5;  // 设置参数
}
```

访问示例:

返回:  
CommAns应答

---

#### 单灯控制器参数下发

> 接口名称: sluitemargvset (*post*)  
> 单灯参数下发

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqSluitemArgvSet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
    int32 cmd_idx = 3;  // 命令序号
    int32 send_domain_name = 4;  // 发送域名，0-表示不需要下发域名设置指令，1-需要追加域名设置指令
    int32 sluitem_idx = 5;  // 控制器条码,发送域名时有效
    int32 send_sub_argv = 6;  // 发送控制器参数
    DataMark data_mark = 7;  // 发送控制器参数时有效
    int32 sluitem_idx = 8;  // 控制器起始地址,发送控制器参数时有效
    int32 sluitem_num = 9;  // 控制器数量,发送控制器参数时有效
    message DataMark {
        int32 group = 1;  // 控制器所属组（5个）
        int32 barcode = 2;  // 控制器条码
        int32 route = 3;  // 控制器路由（前4级通信控制器编号1,2,3...)
        int32 order = 4;  // 开灯序号
        int32 power_limit = 5;  // 功率上限/下限
        int32 power_on_st = 6;  // 上电控制状态
        int32 run_st = 7;  // 2-投运，1-停运
        int32 vector = 8;  // 控制器物理矢量
        int32 rated_power = 9;  // 额定功率
        int32 loop_count = 10;  // 回路数量
    }
}
```

访问示例:

返回:  
CommAns应答

---

#### 单灯集中器网络复位

> 接口名称: slunetreset (*post*)  
> 单灯集中器网络复位

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqSluNetReset {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
    int32 data_mark = 3;  // 复位标识,1-根据设置域名,复位整个网络,2-根据当前域名搜索网络以路由形式加入网络,3-根据设置域名创建网络,4-根据设置域名搜索网络以路由形式加入网络
}
```

访问示例:

返回:  
CommAns应答

---

#### 单灯集中器参数复位

> 接口名称: sluargvreset (*post*)  
> 单灯集中器参数复位

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqSluArgvReset {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
    ResetMark reset_mark = 3;
    int32 cmd_idx = 4;  // 命令序号

    message ResetMark {
        int32 clear_task = 1;  // 清除任务
        int32 reset_concentrator = 2;  // 复位集中器
        int32 hard_reset_zigbee = 3;  // 硬件复位zigbee
        int32 soft_reset_zigbee = 4;  // 软件复位zigbee
        int32 reset_carrier = 5;  // 复位电力载波
        int32 init_all = 6;  // 初始化所有
        int32 clear_data = 7;  // 清除数据
        int32 clear_argv = 8;  // 清除参数
    }
}
```

访问示例:

返回:  
CommAns应答

---

#### 单灯控制器参数复位

> 接口名称: sluitemargvreset (*post*)  
> 单灯集中器参数复位

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqSluitemArgvReset {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
    int32 addr_type = 2;    //地址类型 0-全部，1-组，2-规则，3-单一，4-gprs
    int32 addr = 3;  // 地址
    Reset_mark reset_mark = 3;
    int32 cmd_idx = 4;  // 命令序号

    message Reset_mark {
        int32 reset_mcu = 1;  // mcu复位
        int32 reset_comm = 2;  // 复位通信模块
        int32 init_mcu_hardware = 3;  // 初始化mcu
        int32 init_ram = 4;  // 初始化ram
        int32 zero_eeprom = 5;  // eeprom清零
        int32 zero_count = 6;  // 电能计数清零
    }
}
```

访问示例:

返回:  
CommAns应答

---

#### 单灯集中器参数召测

> 接口名称: sluargvget (*post*)  
> 单灯参数召测

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqSluArgvGet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
    int32 data_mark = 3;  // 参数标示,1-选测集中器工作参数,2-选测集中器报警参数,3-召测集中器版本
}
```

访问示例:

返回:  
CommAns应答

---

#### 单灯控制器参数召测

> 接口名称: sluitemargvget (*post*)  
> 单灯参数召测

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqSluitemArgvGet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
    rqSluitemArgvSet.DataMark data_mark = 3;
}
```

访问示例:

返回:  
CommAns应答

---

#### 防盗选测

> 接口名称: ldudataget (*get*)  
> 防盗数据选测

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqLduDataGet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
    repeated int32 loop_mark = 3 [packed=true];  // 回路标示, 0-不选测,1-选测,最大6路
}
```

访问示例:

返回:  
CommAns应答

---

#### 防盗参数发送

> 接口名称: lduargvset (*post*)  
> 防盗数据选测

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqLduArgvSet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
}
```

访问示例:

返回:  
CommAns应答

---

#### 防盗参数召测

> 接口名称: lduargvget (*post*)  
> 防盗数据选测

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqLduArgvGet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
    repeated int32 loop_mark = 3 [packed=true];  // 回路标示, 0-不选测,1-选测,最大6路
}
```

访问示例:

返回:  
CommAns应答

---

#### 防盗亮灯率设置

> 接口名称: ldulrateset (*post*)  
> 防盗数据选测

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqLduLrateSet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
    repeated int32 loop_mark = 3 [packed=true];  // 回路标示, 0-不选测,1-选测,最大6路
    int32 data_mark = 4;  // 操作标示,0-清楚亮灯率基准,1-设置亮灯率基准
}
```

访问示例:

返回:  
CommAns应答

---

#### 防盗亮灯率召测

> 接口名称: ldulrateget (*post*)  
> 防盗数据选测

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqLduLrateGet {
    Head head = 1;
    repeated int32 tml_id = 2 [packed=true];  // 要操作的设备逻辑地址列表,该列表中的终端均执行相同的操作
    repeated int32 loop_mark = 3 [packed=true];  // 回路标示, 0-不选测,1-选测,最大6路
}
```

访问示例:

返回:  
CommAns应答

---

### 七. 数据查询类

#### 现存/历史故障查询

> 接口名称: querydataerr (*post*)  
> 现存/历史故障查询

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqQueryDataErr {
    Head head = 1;
    int64 dt_start = 5;  // 起始年月日时间默认0:0:0,转换为long传输(1970-1-1开始的秒数)
    int64 dt_end = 6;  // 结束年月日时间默认23:59:59,转换为long传输(1970-1-1开始的秒数)
    int32 type = 7;  // 类型,0-最新,1-历史
    repeated int32 tml_id = 9 [packed=true];  // 设备id,留空表示全部,可多选
    repeated int32 err_id = 10 [packed=true];  // 要查询的故障id,留空表示全部,可多选
}
```

访问示例:

返回:

```protobuf
message QueryDataErr {
    message ErrView {
        int32 err_id = 1;  // 故障id
        string err_name = 2;  // 故障名称
        int64 data_create_idx = 3;  // 产生故障的数据记录时间
        int64 data_remove_idx = 4;  // 消除故障的数据记录时间
        int32 tml_id = 5;  // 产生故障的设备逻辑地址
        int64 dt_create = 6;  // 故障产生时间
        int64 dt_remove = 7;  // 故障消除时间(现存故障时为0)
        int32 phy_id = 8;  // 设备物理地址
        int32 tml_name = 9;  // 设备名称
        int32 tml_sub_id1 = 10;  // 回路序号 或控制系序号或线路序号
        int32 tml_sub_id2 = 11;  // 灯头序号 等
        string remark = 12;  // 备注
    }
    Head head = 1;
    int32 type = 2;  // 类型,0-最新,1-历史
    repeated ErrView err_view = 3;
}
```

---

#### 终端数据查询

> 接口名称: querydatartu (*post*)  
> 终端数据查询

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqQueryDataRtu {
    Head head = 1;
    int64 dt_start = 5;  // 起始年月日时间默认0:0:0,转换为long传输(1970-1-1开始的秒数)
    int64 dt_end = 6;  // 结束年月日时间默认23:59:59,转换为long传输(1970-1-1开始的秒数)
    int32 type = 7;  // 类型,0-最新,1-历史
    repeated int32 tml_id = 9 [packed=true];  // 设备id,留空表示全部,可多选
}
```

访问示例:

返回:

```protobuf
message QueryDataRtu {
    message LoopView {
        double voltage = 1;  // 电压
        double current = 2;  // 电流
        double power = 3;  // 功率
        double rate = 4;  // 亮灯率
        double factor = 5;  // 功率因数
        int32 switch_in_st = 6;  // 开关量输入状态,0-断,1-通
        int32 voltage_over_range = 7;  // 电压越限,0-正常,1-越下线,2-越上限,3-越量程
        int32 current_over_range = 8;  // 电流越限,0-正常,1-越下线,2-越上限,3-越量程
    }
    message DataRtuView {
        int32 tml_id = 1;
        int32 phy_id = 2;
        string tml_name = 13;  // 设备名称
        int64 dt_receive = 3;  // 数据接收时间
        repeated LoopView loop_view = 4;
        repeated int32 switch_out_st = 5 [packed=true];  // 开关量输出状态
        double current_a_sum = 6;  // A相总电流
        double current_b_sum = 7;  // B相总电流
        double current_c_sum = 8;  // C相总电流
        double voltage_a = 9;  // A相电压
        double voltage_b = 10;  // B相电压
        double voltage_c = 11;  // C相电压
        repeated int32 alarm_st = 12 [packed=true];  // 终端报警状态,共8位,每一位0-正常,1-异常,[供电,开机申请,停运,报警,电压超限,电流超限,无电流,参数错误]
    }
    Head head = 1;
    int32 type = 2;  // 类型,0-最新,1-历史
    repeated DataRtuView data_rtu_view = 3;
}
```

---

#### 单灯集中器数据查询

> 接口名称: querydataslu (*post*)  
> 单灯数据查询

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqQueryDataSlu {
    Head head = 1;
    int64 dt_start = 5;  // 起始年月日时间默认0:0:0,转换为long传输(1970-1-1开始的秒数)
    int64 dt_end = 6;  // 结束年月日时间默认23:59:59,转换为long传输(1970-1-1开始的秒数)
    int32 type = 7;  // 类型,0-最新,1-历史
    repeated int32 tml_id = 9 [packed=true];  // 设备id,留空表示全部,可多选
    int32 data_mark = 10;  // 数据类型标示,0-集中器状态数据,7-控制器基本数据,6-控制器辅助数据,4-控制器物理信息
}
```

访问示例:

返回:

```protobuf
message QueryDataSlu {
    message DataSluView {
        int32 tml_id = 1;
        int32 phy_id = 2;
        int64 dt_receive = 3;  // 数据接收时间
        repeated int32 reset_times = 4 [packed=true];  // 连续4天复位次数,[今天,昨天,前天,大前天]
        repeated int32 st_running = 5 [packed=true];  // 集中器状态,[运行状态(0-正常,1-停运),报警状态(0-允许主报,1-禁止主报),开机申请(0-非开机申请,1-开机申请),通信方式(0-485,1-gprs),主动巡测(0-巡测,1-停止巡测)]
        repeated int32 st_argv = 6 [packed=true];  // 集中器参数状态,0-正常,1-出错,[集中器参数,控制器参数,开关灯参数]
        repeated int32 st_hw = 7 [packed=true];  // 硬件参数状态,0-正常,1-出错,[zigbee,电力载波,fram,蓝牙,硬件时钟]
        int32 unknow_sluitem_num = 8;  // 未知控制器数量
        int32 zigbee_channel = 9;  // zigbee信道(1-16)
    }
    message SluitemBaseView {
        int32 tml_id = 1;
        int32 phy_id = 2;
        int64 dt_receive = 3;  // 数据接收时间
        int32 sluitem_id = 4;  // 控制器地址
        int64 dt_cache = 5;  // 集中器缓存该条数据的时间
        repeated int32 st_sluitem = 6 [packed=true];  // 控制器状态,[继电器校准参数出错(0-正常,1-出错),EEPROM出错(0-正常,1-出错),停运(0-正常,1-停运),禁止主动报警(0-主动报警,1-禁止),设置工作参数(0-未设置,1-已设置),校准(0-未校准,1-已校准),状态(0-正常,1-电压越上限,2-电压越下限,3-通信故障)]
        int32 temperature = 7;  // 温度,255或0表示无测温模块
        repeated LampBaseView lamp_base_view = 8;  // 灯头状态,数据
    }
    message LampBaseView {
        repeated int32 st_lamp = 1 [packed=true];  // 灯状态,[亮灯状态(0-亮灯,1-调档节能,2-调光节能,3-关灯),故障状态(0-正常,1-光源故障,2-补偿电容故障,3-意外灭灯,4-意外亮灯,5-自熄灯),漏电状态(0-无漏电,1-漏电),功率状态(0-正常,1-功率越上限,2-功率越下限)]
        double lamp_voltage = 2;  // 电压,单位V
        double lamp_current = 3;  // 电流,单位A
        double lamp_power = 4;  // 有功功率,单位W
        double lamp_electricity = 5;  // 累计电量,单位kW/h,0为无效数据
        int32 lamp_runtime = 6;  // 运行时间,单位分钟
        double lamp_saving = 7;  // 节能档位0-100%
    }
    message SluitemAdvView {
        int32 tml_id = 1;
        int32 phy_id = 2;
        int64 dt_receive = 3;  // 数据接收时间
        int32 sluitem_id = 4;  // 控制器地址
        int64 dt_cache = 5;  // 集中器缓存该条数据的时间
        int32 leakage_current = 6;  // 漏电流,55A表示满量程
        repeated LampAdvView lamp_adv_view = 7;
    }
    message LampAdvView {
        double max_voltage = 1;  // 最大电压
        double max_current = 2;  // 最大电流
        double max_electricity = 3;  // 最大电量
    }
    message SluitemPhyView {
        int32 tml_id = 1;
        int32 phy_id = 2;
        int64 dt_receive = 3;  // 数据接收时间
        int32 sluitem_id = 4;  // 控制器地址
        int32 signal_strength = 5;  // 信号强度
        int32 routing = 6;  // 路由级数 电力载波 0-6,zigbee 0-10
        int32 phase = 7;  // 所在相位 0-无法确定，1-A，2-B，3-C
        int32 comm_success = 8;  // 通信成功次数 1-16
        int32 comm_all = 9;  // 通信总次数 1-16
        int32 sluitem_loops = 10;  // 控制器回路数量
        int32 power_saving = 11;  // 节能方式 0-无控制，1-只有开关灯，2-一档节能，3-二档节能，4-RS485，5-PWM
        int32 has_leakage = 12;  // 漏电流测量 0-无，1-有
        int32 has_temperature = 13;  // 温度采集 0-无，1-有
        int32 has_timer = 14;  // 时钟 0-无，1-有
        int32 model = 15;  // 型号 0-unknow,1-wj2090j
    }
    Head head = 1;
    int32 data_mark = 2;  // 数据类型标示,同请求
    repeated DataSluView data_slu_view = 3;  // 当data_mark=0时返回
    repeated SluitemBaseView sluitem_base_view = 4; // 当data_mark=7时返回
    repeated SluitemAdvView sluitem_adv_view = 5;  // 当data_mark=6时返回
    repeated SluitemPhyView sluitem_phy_view = 6;  // 当data_mark=4时返回
}
```

---

#### 防盗数据查询

> 接口名称: querydataldu (*post*)  
> 防盗数据查询

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqQueryDataLdu {
    Head head = 1;
    int64 dt_start = 5;  // 起始年月日时间默认0:0:0,转换为long传输(1970-1-1开始的秒数)
    int64 dt_end = 6;  // 结束年月日时间默认23:59:59,转换为long传输(1970-1-1开始的秒数)
    int32 type = 7;  // 类型,0-最新,1-历史
    repeated int32 tml_id = 9 [packed=true];  // 设备id,留空表示全部,可多选
}
```

访问示例:

返回:

```protobuf
message QueryDataLdu {
    message DataLduView {
        int32 tml_id = 1;
        int32 phy_id = 2;
        int64 dt_receive = 3;  // 数据接收时间
        int32 line_id = 4;  // 回路x序号
    	double voltage = 5;  // 回路x电压
    	double current = 6;  // 回路x电流
    	double active_power = 7;  // 回路x有功功率
    	double reactive_power = 8;  // 回路x无功功率
    	double power_factor = 9;  // 回路x功率因数
    	double lighting_rate = 10;  // 回路x亮灯率
    	int32 single = 11;  // 回路x信号强度 脉冲
    	int32 impedance = 12;  // 回路x阻抗
    	int32 useful_signal = 13;  // 回路x 12s有用信号数量  阻抗数
    	int32 all_signal = 14;  // 回路x 12s信号数量 跳数
    	repeated int32 detection_flag = 15 [packed=true];  // 回路x检测标识 故障参数
    	repeated int32 alarm_flag = 16 [packed=true];  // 回路x报警标识  故障数据
    }
    Head head = 1;
    repeated DataLduView data_ldu_view = 2;
}
```

---

#### 抄表数据查询

> 接口名称: querydatamru (*post*)  
> 抄表数据查询

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqQueryDataMru {
    Head head = 1;
    int64 dt_start = 5;  // 起始年月日时间默认0:0:0,转换为long传输(1970-1-1开始的秒数)
    int64 dt_end = 6;  // 结束年月日时间默认23:59:59,转换为long传输(1970-1-1开始的秒数)
    int32 type = 7;  // 类型,0-最新,1-历史
    repeated int32 tml_id = 9 [packed=true];  // 设备id,留空表示全部,可多选
}
```

访问示例:

返回:

```protobuf
message QueryDataMru {
    message DataMruView {
        int32 tml_id = 1;
        int32 phy_id = 2;
        int64 dt_receive = 3;  // 数据接收时间
        int32 data_mark = 4;  // 数据类型,1-A相，2-B相，3-C相，4-总电量
        int32 data_dt = 5;  // 数据时间段,0-当前，1-上月，2-上上月
        int32 baud_rate = 6;  // 电表波特率
        int32 meter_value = 7;  // 抄表值
        int32 meter_ver = 8;  // 电表协议版本,1-1997协议，2-2007协议
    }
    Head head = 1;
    repeated DataMruView data_mru_view = 2;
}
```

---

#### 事件记录查询

> 接口名称: querydataevents (*post*)  
> 事件记录查询

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqQueryDataEvents {
    Head head = 1;
    int64 dt_start = 5;  // 起始年月日时间默认0:0:0,转换为long传输(1970-1-1开始的秒数)
    int64 dt_end = 6;  // 结束年月日时间默认23:59:59,转换为long传输(1970-1-1开始秒数)
    repeated int32 events_id = 7 [packed=true];  // 待定义
    repeated string user_name = 8;  // 用户名,可多选
    repeated int32 tml_id = 9 [packed=true];  // 设备id,可多选
}
```

访问示例:

返回:

```protobuf
message QueryDataEvents {
    message DataEventsView {
        int32 events_id = 1;  // 事件id
        string user_name = 2;  // 用户id
        int32 tml_id = 3;  // 设备对象id
        string events_msg = 4;  // 事件内容
        int64 dt_happen = 5;  // 事件发生时间
        string events_name = 6;  // 事件名称
    }
    Head head = 1;
    repeated DataEventsView data_events_view = 2;
}
```

---

#### 日出日落时间查看

> 接口名称: querydatasunriseset (*post*)  
> 日出日落时间查询

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqQueryDataSunriseset {
    Head head = 1;
    int64 dt_start = 5;  // 起始年月日时间默认0:0:0,转换为long传输(1970-1-1开始的秒数)
    int64 dt_end = 6;  // 结束年月日时间默认23:59:59,转换为long传输(1970-1-1开始的秒数)
}
```

访问示例:

返回:

```protobuf
message QueryDataSunriseset {
    message DataSunrisesetView {
        int64 dt_sun = 3;  // 日期 yyyy-mm-dd
        int32 sunrise = 4;  // 日出 hh*60+mm
        int32 sunset = 5;  // 日落 hh*60+mm
    }
    Head head = 1;
    repeated DataSunrisesetView data_sunriseset_view = 2;
}
```

---

#### 开关灯时间查询

> 接口名称: querydatalights (*post*)  
> 开关灯时间查询

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqQueryDataLights {
    Head head = 1;
    int64 dt_start = 5;  // 起始年月日时间默认0:0:0,转换为long传输(1970-1-1开始的秒数)
    int64 dt_end = 6;  // 结束年月日时间默认23:59:59,转换为long传输(1970-1-1开始的秒数)
    int32 target_type = 7; 1-终端,2-分组,3-区域
    repeated target_id = 8;
}
```

访问示例:

返回:

```protobuf
message QueryDataLights {
    message DataLightsView {
        int32 tml_id = 1;
        int32 phy_id = 2;
        int32 duration = 3;  // 时长
        int64 dt_lights = 4;  // 日期
    }
    Head head = 1;
    repeated DataLightsView data_lights_view = 2;
}
```

### 八. 报表类

...
