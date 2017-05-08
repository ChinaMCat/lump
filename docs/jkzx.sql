-- --------------------------------------------------------
-- 主机:                           192.168.50.83
-- 服务器版本:                        10.1.21-MariaDB - MariaDB Server
-- 服务器操作系统:                      Linux
-- HeidiSQL 版本:                  9.2.0.4947
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;

-- 导出 jkzx 的数据库结构
CREATE DATABASE IF NOT EXISTS `jkzx` /*!40100 DEFAULT CHARACTER SET utf8 */;
USE `jkzx`;


-- 导出  表 jkzx.area_info 结构
DROP TABLE IF EXISTS `area_info`;
CREATE TABLE IF NOT EXISTS `area_info` (
  `area_id` int(11) NOT NULL AUTO_INCREMENT,
  `area_parent` int(11) NOT NULL DEFAULT '0',
  `area_name` varchar(50) NOT NULL DEFAULT '0',
  `area_remark` text,
  PRIMARY KEY (`area_id`)
) ENGINE=Aria AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 PAGE_CHECKSUM=1;

-- 正在导出表  jkzx.area_info 的数据：1 rows
DELETE FROM `area_info`;
/*!40000 ALTER TABLE `area_info` DISABLE KEYS */;
INSERT INTO `area_info` (`area_id`, `area_parent`, `area_name`, `area_remark`) VALUES
	(1, 0, '五零盛同', NULL);
/*!40000 ALTER TABLE `area_info` ENABLE KEYS */;


-- 导出  表 jkzx.events_info 结构
DROP TABLE IF EXISTS `events_info`;
CREATE TABLE IF NOT EXISTS `events_info` (
  `event_id` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `event_name` varchar(50) NOT NULL,
  `event_class_id` int(11) DEFAULT NULL,
  `event_class_name` varchar(50) DEFAULT NULL,
  `event_remark` text,
  PRIMARY KEY (`event_id`)
) ENGINE=Aria DEFAULT CHARSET=utf8 PAGE_CHECKSUM=1;

-- 正在导出表  jkzx.events_info 的数据：65 rows
DELETE FROM `events_info`;
/*!40000 ALTER TABLE `events_info` DISABLE KEYS */;
INSERT INTO `events_info` (`event_id`, `event_name`, `event_class_id`, `event_class_name`, `event_remark`) VALUES
	(1, '设备增加', 2, '设备管理', NULL),
	(2, '设备参数更新', 2, '设备管理', NULL),
	(3, '设备删除', 2, '设备管理', NULL),
	(11, '终端时间同步', 1, '终端控制', NULL),
	(12, '终端工作参数', 1, '终端控制', NULL),
	(13, '终端矢量参数', 1, '终端控制', NULL),
	(14, '终端模拟量参数', 1, '终端控制', NULL),
	(15, '终端上下限参数', 1, '终端控制', NULL),
	(16, '终端电压参数', 1, '终端控制', NULL),
	(17, '终端停运', 1, '终端控制', NULL),
	(18, '终端投运', 1, '终端控制', NULL),
	(19, '终端开灯', 1, '终端控制', NULL),
	(20, '终端关灯', 1, '终端控制', NULL),
	(21, '终端开关灯应答', 1, '终端控制', NULL),
	(23, '终端开机申请', 1, '终端控制', NULL),
	(24, '亮灯率设置', 1, '终端控制', NULL),
	(25, '电流上下限设置', 1, '终端控制', NULL),
	(26, '复位终端', 1, '终端控制', NULL),
	(27, '恢复出厂设置', 1, '终端控制', NULL),
	(31, '节能设备参数', 5, '节能控制', NULL),
	(32, '节能设备调压时间', 5, '节能控制', NULL),
	(33, '节能设备手动调', 5, '节能控制', NULL),
	(34, '节能设备手动开机', 5, '节能控制', NULL),
	(35, '节能设备手动关机', 5, '节能控制', NULL),
	(36, '节能设备手动开关机应答', 5, '节能控制', NULL),
	(41, '光控设备模式设置', 6, '光控控制', NULL),
	(42, '光控设备主报时间设置', 6, '光控控制', NULL),
	(51, '复位网络', 8, '单灯控制', NULL),
	(52, '设置集中器巡测', 8, '单灯控制', NULL),
	(53, '设置停运投运与主动报警', 8, '单灯控制', NULL),
	(54, '设置集中器参数', 8, '单灯控制', NULL),
	(55, '设置域名', 8, '单灯控制', NULL),
	(56, '复位与参数初始化', 8, '单灯控制', NULL),
	(57, '设置时钟', 8, '单灯控制', NULL),
	(58, '设置控制器参数', 8, '单灯控制', NULL),
	(59, '设置短程控制参数', 8, '单灯控制', NULL),
	(60, '设置集中器报警参数', 8, '单灯控制', NULL),
	(61, '蓝牙连接请求', 8, '单灯控制', NULL),
	(64, '单灯方案设置', 4, '用户操作', NULL),
	(65, '混合或调光操作', 8, '单灯控制', NULL),
	(71, '设置漏电地址', 9, '漏电控制', NULL),
	(72, '设置漏电运行参数', 9, '漏电控制', NULL),
	(73, '手动分合闸', 9, '漏电控制', NULL),
	(74, '设置检查门限', 9, '漏电控制', NULL),
	(75, '设置时钟', 9, '漏电控制', NULL),
	(76, '复位', 9, '漏电控制', NULL),
	(101, '周设置', 4, '用户操作', NULL),
	(103, '节假日设置', 4, '用户操作', NULL),
	(111, '任务更新', 4, '用户操作', NULL),
	(112, '任务删除', 4, '用户操作', NULL),
	(121, '用户登陆', 4, '用户操作', NULL),
	(122, '用户注销', 4, '用户操作', NULL),
	(131, '分组信息更新', 4, '用户操作', NULL),
	(132, '区域信息更新', 4, '用户操作', NULL),
	(141, '故障类型设置', 4, '用户操作', NULL),
	(142, '终端或分组特殊报警设置', 4, '用户操作', NULL),
	(143, '用户显示报警更新', 4, '用户操作', NULL),
	(144, '删除现存故障', 4, '用户操作', NULL),
	(154, '用户增加', 4, '用户操作', NULL),
	(155, '用户更新', 4, '用户操作', NULL),
	(156, '用户删除', 4, '用户操作', NULL),
	(161, '清除亮灯率基准', 7, '防盗检测', NULL),
	(162, '设置亮灯率基准', 7, '防盗检测', NULL),
	(163, '设置防盗检测参数', 7, '防盗检测', NULL),
	(164, '终端位置移动', 2, '设备管理', NULL);
/*!40000 ALTER TABLE `events_info` ENABLE KEYS */;


-- 导出  表 jkzx.events_log 结构
DROP TABLE IF EXISTS `events_log`;
CREATE TABLE IF NOT EXISTS `events_log` (
  `events_log_id` int(11) NOT NULL AUTO_INCREMENT,
  `event_id` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `event_time` bigint(20) NOT NULL DEFAULT '0',
  `user_id` int(11) NOT NULL DEFAULT '0',
  `event_remark` text,
  `project_id` int(11) NOT NULL DEFAULT '0',
  `event_ip` int(11),
  `tml_id` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`events_log_id`)
) ENGINE=Aria DEFAULT CHARSET=utf8 PAGE_CHECKSUM=1;

-- 正在导出表  jkzx.events_log 的数据：0 rows
DELETE FROM `events_log`;
/*!40000 ALTER TABLE `events_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `events_log` ENABLE KEYS */;


-- 导出  表 jkzx.project_info 结构
DROP TABLE IF EXISTS `project_info`;
CREATE TABLE IF NOT EXISTS `project_info` (
  `project_id` int(11) NOT NULL AUTO_INCREMENT,
  `project_name` varchar(50) NOT NULL,
  `project_ip` char(15) NOT NULL,
  `project_port` smallint(5) unsigned NOT NULL,
  `project_root` varchar(50) NOT NULL DEFAULT '/',
  `area_id` int(11) NOT NULL DEFAULT '1',
  `project_active` tinyint(4) NOT NULL DEFAULT '1',
  `project_remark` text,
  PRIMARY KEY (`project_id`)
) ENGINE=Aria DEFAULT CHARSET=utf8 PAGE_CHECKSUM=1;

-- 正在导出表  jkzx.project_info 的数据：0 rows
DELETE FROM `project_info`;
/*!40000 ALTER TABLE `project_info` DISABLE KEYS */;
/*!40000 ALTER TABLE `project_info` ENABLE KEYS */;


-- 导出  表 jkzx.user_info 结构
DROP TABLE IF EXISTS `user_info`;
CREATE TABLE IF NOT EXISTS `user_info` (
  `user_id` int(11) NOT NULL DEFAULT '0',
  `user_alias` varchar(50) DEFAULT '0',
  `user_remark` text,
  PRIMARY KEY (`user_id`)
) ENGINE=Aria DEFAULT CHARSET=utf8 PAGE_CHECKSUM=1;

-- 正在导出表  jkzx.user_info 的数据：1 rows
DELETE FROM `user_info`;
/*!40000 ALTER TABLE `user_info` DISABLE KEYS */;
INSERT INTO `user_info` (`user_id`, `user_alias`, `user_remark`) VALUES
	(1, 'admin', '管理员帐户不可删除');
/*!40000 ALTER TABLE `user_info` ENABLE KEYS */;


-- 导出  表 jkzx.user_project 结构
DROP TABLE IF EXISTS `user_project`;
CREATE TABLE IF NOT EXISTS `user_project` (
  `user_id` int(11) NOT NULL DEFAULT '0',
  `project_id` int(11) NOT NULL DEFAULT '0',
  `user_auth` tinyint(3) unsigned DEFAULT '0',
  PRIMARY KEY (`user_id`,`project_id`)
) ENGINE=Aria DEFAULT CHARSET=utf8 PAGE_CHECKSUM=1;

-- 正在导出表  jkzx.user_project 的数据：0 rows
DELETE FROM `user_project`;
/*!40000 ALTER TABLE `user_project` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_project` ENABLE KEYS */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IF(@OLD_FOREIGN_KEY_CHECKS IS NULL, 1, @OLD_FOREIGN_KEY_CHECKS) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
