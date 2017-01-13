短信WebService接口访问脚本编写说明
==================================

-	开发语言需要支持Google Protocol Buffer
-	开发语言需要有成熟的HTTP POST访问类库
-	短信WebService接口二次开发文档见下：《短信WebService接口设计说明》

短信WebService接口设计说明
==========================

(The Description of Interactive Integrated Services Interface)

-	所有接口采用 HTTP 协议 post 方式请求, 地址格式为`http://<ip>:<port>/<interface name>`  
-	提交的参数和返回数据格式为 Google Protocol Buffer ( protobuf ) 协议序列化后再经由 base64 编码得到的字符串

-	protobuf 协议格式说明  
	> 协议采用 proto3 格式编写,使用 protoc v3.0 beta2 编译  
	> 所有时间字段，均采用unix秒格式

-	动态安全码运算方式:  
	> 部分submit类型接口因为不需要登录,所以会将参数uuid改为scode, 在每次调用接口时通过动态运算获得

	-	动态码运算方式为计算 `YYYYMMDDHH<salt>` 字符串的md5码.
		-	`YYYYMMDDHH`为当前日期的字符串, 年为4位,月,日,小时均为2位,不足的十位补零
		-	`<salt>`为内定固定字符串,不在文档中公开,有需要的请咨询徐源

-	头结构:

> 该头结构将插入每个请求或返回的协议结构体中  
> 协议类名加前缀 "rq" 表示客户端->服务端,无前缀表示服务端->客户端

```protobuf
message Head {
    int64 idx = 1;  // 序号(必填)
    int32 ver = 2;  // 协议版本(必填,默认为协议发布日期6位整型)。当前版本为 160328
    string if_name = 3;  // 接口名称(可选)
    int64 if_dt = 100;  // 请求或返回时间(必填)
    int32 if_st = 101;  // 接口操作状态(返回必填)
                            // 1-操作成功, 0-操作失败, 原因参考msg, 10-用户未登录或超时(0.5h),请求被拒绝, 11-用户权限不足,12-用户登录ip非法,需重新登录
                            // 41-数据库连接失败,42-指令提交失败(socket pool),43-第三方接口调用失败,45-数据库提交失败,46-参数错误,
			    // 99-接口参数暂不支持
    string if_msg = 102;  // 失败时填充详细原因(可选)
    repeated string msg_filter = 103;  // 调用接口后可能产生的消息过滤器，仅对设备操作类型接口有效，如终端开关灯、选测，客户端可以动态设置这些过滤器用来获得精准推送
    int32 paging_num = 200;  // 此次请求/应答是否使用分页(仅对非参数数据查询类接口有效,'query'开头的接口),0-不使用,大于0时使用,但是,若客户端请求的赋值>100或数据总量大于100,服务端按照100进行强制分页
    int32 paging_idx = 201;  // 分页序号,从1开始,当序号大于分页总数时返回空
    int32 paging_total = 202;  // 服务端返回该次请求产生的分页总数(客户端请求数据时不填充)
    int64 paging_buffer_tag = 203;  // 分页缓存标签,0-要求服务器重建缓存,xx-根据服务器返回的tag从对应缓存读取数据
    int32 paging_record_total = 204;  // 查询记录总数
}
```

-	公共应答  
	> 公共应答仅包含head信息，用于不需要添加附加数据的场合

```
message CommAns {
    Head head = 1;  // 协议头信息
}
```

版本 v160328:
-------------

### 短信类

#### 短信发送接口（需要新版监控数据库以及新版监控短信发送软件支持）

> 接口名称: submitsms (*post*\)  
> 接口将短信内容提交至新版监控相关数据表，等待短信发送软件排队发送

参数:  
1. scode - 动态运算的安全码, 运算方法见文档开头  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqSubmitSms {
    Head head = 1;
    repeated int64 tels = 2 [packed=true];  // 目标号码，长度11位，可填写多个
    string msg = 3;  // 短信内容，长度超过340个字符会被拆分
}
```

返回:  
CommAns()应答

---

#### 短信发送记录查询

> 接口名称: querysmsrecord (*post*)  
> 查询短信发送记录

参数:  
1. uuid - 登录成功获得的动态id  
2. pb2 - 详细参数(结构如下)

```protobuf
message rqQuerySmsRecord {
    Head head = 1;
    repeated int64 tels = 3 [packed=true];  // 查询号码,长度11,可填写多个,可选
    string msg = 4;  // 查询内容,可模糊查询,可选
    int64 dt_start = 5;  // 查询起始日期
    int64 dt_end = 6;  // 查询结束日期
}
```

返回:

```protobuf
message QuerySmsRecord {
    message SmsRecord {
        int64 dt_send = 1;  // 发送日期
        int64 tel = 2;  // 发送号码
        string msg = 3;  // 发送内容
    }
    Head head = 1;
    repeated SmsRecord sms_record = 3;
}
```
