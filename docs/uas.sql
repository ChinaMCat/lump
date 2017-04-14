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


-- 导出  表 uas.eventsinfo 结构
DROP TABLE IF EXISTS `eventsinfo`;
CREATE TABLE IF NOT EXISTS `eventsinfo` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `event_id` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `event_name` varchar(50) NOT NULL,
  `remark` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;

-- 正在导出表  uas.eventsinfo 的数据：~3 rows (大约)
DELETE FROM `eventsinfo`;
/*!40000 ALTER TABLE `eventsinfo` DISABLE KEYS */;
INSERT INTO `eventsinfo` (`id`, `event_id`, `event_name`, `remark`) VALUES
	(1, 1, '新增用户', NULL),
	(2, 2, '修改用户信息', NULL),
	(3, 3, '删除用户', NULL);
/*!40000 ALTER TABLE `eventsinfo` ENABLE KEYS */;


-- 导出  表 uas.eventslog 结构
DROP TABLE IF EXISTS `eventslog`;
CREATE TABLE IF NOT EXISTS `eventslog` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `event_id` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `event_time` bigint(20) NOT NULL DEFAULT '0',
  `event_user` varchar(32) NOT NULL DEFAULT '0',
  `remark` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- 正在导出表  uas.eventslog 的数据：~0 rows (大约)
DELETE FROM `eventslog`;
/*!40000 ALTER TABLE `eventslog` DISABLE KEYS */;
/*!40000 ALTER TABLE `eventslog` ENABLE KEYS */;


-- 导出  表 uas.userinfo 结构
DROP TABLE IF EXISTS `userinfo`;
CREATE TABLE IF NOT EXISTS `userinfo` (
  `user_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_name` varchar(32) NOT NULL,
  `user_pwd` char(32) NOT NULL,
  `user_fullname` varchar(32) DEFAULT NULL,
  `user_mobile` int(8) unsigned DEFAULT NULL,
  `user_tel` varchar(30) DEFAULT NULL,
  `user_email` varchar(50) DEFAULT NULL,
  `create_time` bigint(20) DEFAULT NULL,
  `remark` text,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `user_name` (`user_name`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

-- 正在导出表  uas.userinfo 的数据：~1 rows (大约)
DELETE FROM `userinfo`;
/*!40000 ALTER TABLE `userinfo` DISABLE KEYS */;
INSERT INTO `userinfo` (`user_id`, `user_name`, `user_pwd`, `user_fullname`, `user_mobile`, `user_tel`, `user_email`, `create_time`, `remark`) VALUES
	(1, 'admin', 'e807f1fcf82d132f9bb018ca6738a19f', 'admin', NULL, NULL, NULL, NULL, NULL);
/*!40000 ALTER TABLE `userinfo` ENABLE KEYS */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IF(@OLD_FOREIGN_KEY_CHECKS IS NULL, 1, @OLD_FOREIGN_KEY_CHECKS) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
