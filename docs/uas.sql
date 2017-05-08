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

-- 导出 uas 的数据库结构
CREATE DATABASE IF NOT EXISTS `uas` /*!40100 DEFAULT CHARACTER SET utf8 */;
USE `uas`;


-- 导出  表 uas.events_info 结构
DROP TABLE IF EXISTS `events_info`;
CREATE TABLE IF NOT EXISTS `events_info` (
  `event_id` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `event_name` varchar(50) NOT NULL,
  `event_remark` text,
  PRIMARY KEY (`event_id`)
) ENGINE=Aria DEFAULT CHARSET=utf8 PAGE_CHECKSUM=1;

-- 正在导出表  uas.events_info 的数据：4 rows
DELETE FROM `events_info`;
/*!40000 ALTER TABLE `events_info` DISABLE KEYS */;
INSERT INTO `events_info` (`event_id`, `event_name`, `event_remark`) VALUES
	(1, '新增用户', NULL),
	(2, '修改用户信息', NULL),
	(3, '删除用户', NULL),
	(4, '用户登录', NULL);
/*!40000 ALTER TABLE `events_info` ENABLE KEYS */;


-- 导出  表 uas.events_log 结构
DROP TABLE IF EXISTS `events_log`;
CREATE TABLE IF NOT EXISTS `events_log` (
  `events_log_id` int(11) NOT NULL AUTO_INCREMENT,
  `event_id` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `event_time` bigint(20) NOT NULL DEFAULT '0',
  `user_id` int(11) NOT NULL DEFAULT 0,
  `event_id` int(11),
  `event_remark` text,
  PRIMARY KEY (`events_log_id`)
) ENGINE=Aria DEFAULT CHARSET=utf8 PAGE_CHECKSUM=1;

-- 正在导出表  uas.events_log 的数据：0 rows
DELETE FROM `events_log`;
/*!40000 ALTER TABLE `events_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `events_log` ENABLE KEYS */;


-- 导出  表 uas.user_list 结构
DROP TABLE IF EXISTS `user_list`;
CREATE TABLE IF NOT EXISTS `user_list` (
  `user_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_name` varchar(32) NOT NULL,
  `user_pwd` char(32) NOT NULL,
  `user_alias` varchar(32) DEFAULT NULL,
  `user_mobile` int(8) unsigned DEFAULT NULL,
  `user_tel` varchar(30) DEFAULT NULL,
  `user_email` varchar(50) DEFAULT NULL,
  `create_time` bigint(20) DEFAULT NULL,
  `user_remark` text,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `user_name` (`user_name`)
) ENGINE=Aria AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 PAGE_CHECKSUM=1;

-- 正在导出表  uas.user_info 的数据：1 rows
DELETE FROM `user_list`;
/*!40000 ALTER TABLE `user_info` DISABLE KEYS */;
INSERT INTO `user_list` (`user_id`, `user_name`, `user_pwd`, `user_alias`, `user_mobile`, `user_tel`, `user_email`, `create_time`, `user_remark`) VALUES
	(1, 'admin', '202cb962ac59075b964b07152d234b70', 'admin', NULL, NULL, NULL, 1492570257, 'admin account, can not delete.');
/*!40000 ALTER TABLE `user_info` ENABLE KEYS */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IF(@OLD_FOREIGN_KEY_CHECKS IS NULL, 1, @OLD_FOREIGN_KEY_CHECKS) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
